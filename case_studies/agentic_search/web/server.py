"""Agentic search: a local web page for searching, indexing and asking.

Type a search term: the chosen engines' top results are fetched, cached,
split into paragraphs, embedded and compiled into a knowledge graph. Then
ask questions and follow-ups about those pages. More search terms or pasted
links add to the same knowledge base; Clear starts again. Runs on your own
machine only (127.0.0.1); the API key stays in this process's environment.

Usage (from the repository root, with OPENAI_API_KEY set):
  python -m case_studies.agentic_search.web.server
then open http://127.0.0.1:8771
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import html
import json
import re
import threading
import time

from case_studies.agentic_rag.rag import COSTS
from case_studies.agentic_search import engines
from case_studies.agentic_search.ask import ask
from case_studies.agentic_search.knowledge_base import (
    KnowledgeBase, delete, sessions)

HOST, PORT = '127.0.0.1', 8771
PAGE = Path(__file__).with_name('index.html')
SAVED = sessions()                # reopen the most recent search, if any
KB = KnowledgeBase.open(SAVED[0]['id']) if SAVED else KnowledgeBase()
BUSY = threading.Lock()          # one indexing job or question at a time
MAX_ENTITIES = 40
# Pages from the web may show their text, images and styles here, but run
# nothing: no scripts, plugins or frames, and no form submissions.
NO_SCRIPTS = [('Content-Security-Policy',
               "script-src 'none'; object-src 'none'; frame-src 'none'; "
               "form-action 'none'")]


def start_job(work, label):
    """Run an indexing job in the background; the page polls /api/state."""
    if not BUSY.acquire(blocking=False):
        return False

    def go():
        KB.job.update(running=True, error=None, label=label)
        KB.job['log'] = []
        try:
            work()
        except Exception as error:      # reported on the page
            KB.job['error'] = f'{type(error).__name__}: {error}'
            KB.log(f'failed: {KB.job["error"]}')
        finally:
            KB.job['running'] = False
            BUSY.release()
    threading.Thread(target=go, daemon=True).start()
    return True


def overview():
    """The knowledge graph at page level, for drawing: searches, pages,
    the busiest entities, and their links. Paragraphs are folded into
    their pages so the picture stays readable."""
    g = KB.graph
    page_of = {d['id']: d['page'] for d in KB.docs}
    nodes = {}
    for node_id, node in g.nodes.items():
        if node['kind'] in ('search', 'page'):
            nodes[node_id] = {'id': node_id, 'kind': node['kind'],
                              'title': node['title'],
                              'url': node.get('url')}
    nodes.pop('manual', None)
    busiest = sorted(KB.entities.items(), key=lambda kv: -len(kv[1][1]))
    for node_id, (name, mentions) in busiest[:MAX_ENTITIES]:
        nodes[node_id] = {'id': node_id, 'kind': 'entity', 'title': name,
                          'mentions': len(mentions)}
    edges, seen = [], set()

    def add(a, relation, b, kind='structural'):
        key = (a, relation, b)
        if a in nodes and b in nodes and a != b and key not in seen:
            seen.add(key)
            edges.append({'from': a, 'to': b, 'relation': relation,
                          'kind': kind})
    if any(p['found'][0]['search'] == 'manual' for p in KB.pages
           if p['status'] == 'indexed'):
        nodes['manual'] = {'id': 'manual', 'kind': 'search',
                           'title': 'added by hand'}
    for e in g.edges:
        source, target = e['source'], e['target']
        if e['relation'] == 'mentioned_in':
            add(source, 'mentioned in', page_of.get(target, target))
        elif e['relation'] in ('has_paragraph', 'next_paragraph'):
            continue
        else:
            add(source, e['relation'].replace('_', ' '), target, e['kind'])
    return {'nodes': list(nodes.values()), 'edges': edges}


def step_view(step):
    kind = step[0]
    if kind == 'search':
        found = KB.search(step[1])     # cached embedding: free to repeat
        return {'kind': kind, 'query': step[1], 'hits': found['hits'],
                'facts': found['facts']}
    if kind == 'read':
        doc = KB.by_id.get(step[1], {})
        return {'kind': kind, 'id': step[1], 'title': doc.get('title'),
                'url': doc.get('url'), 'page': doc.get('page')}
    if kind == 'explore':
        node = KB.graph.resolve(step[1])
        return {'kind': kind, 'node': step[1], 'resolved': node}
    if kind == 'answer':
        return {'kind': kind, 'citations': step[1], 'refused': step[2]}
    if kind == 'decline':
        return {'kind': kind, 'reason': step[1],
                'refused': step[2] if len(step) > 2 else []}
    return {'kind': kind, 'detail': str(step[1])}


def roles(steps):
    """What the agent did with each page and entity, for highlighting the
    overview graph, with the step at which it first happened."""
    found = {}

    def mark(node, role, i):
        entry = found.setdefault(node, {'roles': [], 'step': i})
        if role not in entry['roles']:
            entry['roles'].append(role)
    for i, s in enumerate(steps, 1):
        if s['kind'] == 'search':
            for hit in s['hits']:
                mark(KB.by_id[hit['id']]['page'], 'hit', i)
        elif s['kind'] == 'read' and s.get('page'):
            mark(s['page'], 'read', i)
        elif s['kind'] == 'explore' and s.get('resolved'):
            node = s['resolved']
            mark(KB.by_id[node]['page'] if node in KB.by_id else node,
                 'explored', i)
        elif s['kind'] == 'answer':
            for c in s['citations']:
                if c in KB.by_id:
                    mark(KB.by_id[c]['page'],
                         'refused' if s['refused'] else 'cited', i)
    return found


def answer(body):
    asked = str(body.get('question', '')).strip()[:500]
    history = [{'question': str(t.get('question', ''))[:500],
                'answer': str(t.get('answer', ''))[:1500]}
               for t in body.get('history', [])[-4:]]
    start = time.perf_counter()
    question, outcome, calls = ask(KB, asked, history)
    steps = [step_view(s) for s in outcome['trace']]
    result = {
        'asked': asked, 'question': question,
        'rewritten': question != asked, 'status': outcome['status'],
        'answer': outcome.get('answer'), 'reason': outcome.get('reason'),
        'citations': [{'id': c, 'title': KB.by_id[c]['title'],
                       'url': KB.by_id[c]['url'],
                       'page': KB.by_id[c]['page']}
                      for c in outcome.get('citations', [])
                      if c in KB.by_id],
        'trace': steps, 'roles': roles(steps),
        'steps': outcome['budget'].steps_used,
        'cost_units': round(outcome['budget'].cost_used, 3),
        'limits': {'steps': 10, 'cost': 0.2}, 'costs': COSTS,
        'input_tokens': sum(c['input_tokens'] for c in calls),
        'output_tokens': sum(c['output_tokens'] for c in calls),
        'seconds': round(time.perf_counter() - start, 1)}
    KB.add_turn(result)               # saved with the session
    KB.save()
    return result


def switch(new_kb):
    """Save the current session and make another one current."""
    global KB
    KB.save()
    KB = new_kb


class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, kind='application/json', extra=()):
        data = body if isinstance(body, bytes) else json.dumps(
            body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', f'{kind}; charset=utf-8'
                         if 'pdf' not in kind else kind)
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        for name, value in extra:
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        query = parse_qs(url.query)
        if url.path == '/':
            self.send(200, PAGE.read_bytes(), 'text/html')
        elif url.path == '/api/state':
            self.send(200, {**KB.summary(), 'engines': engines.status()})
        elif url.path == '/api/graph':
            self.send(200, overview())
        elif url.path == '/api/sessions':
            self.send(200, {'current': KB.id, 'sessions': sessions()})
        elif url.path.startswith('/read/'):
            # A clean reading view of a cached page, scrolled to a cited
            # paragraph (?chunk=p3-c07) and highlighted.
            page_id = url.path.removeprefix('/read/')
            if not any(p['id'] == page_id and p['status'] == 'indexed'
                       for p in KB.pages):
                return self.send(404, {'error': 'no such page'})
            self.send(200, KB.reader(page_id, query.get('chunk', [None])[0]),
                      'text/html', NO_SCRIPTS)
        elif url.path == '/api/doc':
            doc_id = query.get('id', [''])[0]
            doc = KB.by_id.get(doc_id)
            if doc is None and doc_id in KB.graph.nodes:
                node = KB.graph.explore(doc_id, limit=30)
                doc = {'id': doc_id, 'title': node['title'],
                       'kind': node['kind'], 'text': ' · '.join(
                           f'{l["relation"]} → {l["title"]}'
                           for l in node['links'])}
            self.send(200 if doc else 404, doc or {'error': 'not found'})
        elif url.path.startswith('/cache/'):
            # The saved original of a scraped page, with no scripts allowed
            # to run on this local origin, and a base address so its images
            # and styles load from the original site.
            page_id = url.path.removeprefix('/cache/')
            path = KB.cached(page_id)
            if path is None:
                return self.send(404, {'error': 'not cached'})
            if path.suffix == '.pdf':
                return self.send(200, path.read_bytes(), 'application/pdf')
            page = next(p for p in KB.pages if p['id'] == page_id)
            origin = html.escape(page.get('final_url', page['url']))
            base = f'<base href="{origin}">'
            body = re.sub(rb'<head[^>]*>', lambda m: m.group(0)
                          + base.encode(), path.read_bytes(), count=1,
                          flags=re.I)
            self.send(200, body, 'text/html', NO_SCRIPTS)
        else:
            self.send(404, {'error': 'not found'})

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get('Content-Length', 0))
        try:
            body = json.loads(self.rfile.read(length) or b'{}')
        except json.JSONDecodeError:
            return self.send(400, {'error': 'invalid request'})
        if path == '/api/search':
            term = str(body.get('term', '')).strip()[:200]
            chosen = [e for e in body.get('engines', ['duckduckgo'])
                      if e in engines.ENGINES]
            top_n = max(1, min(int(body.get('top_n', 10)), 30))
            if not term or not chosen:
                return self.send(400, {'error': 'a term and an engine'})
            if body.get('fresh') and KB.pages:   # into a new knowledge base
                if not BUSY.acquire(blocking=False):
                    return self.send(409, {'error': 'busy: wait for the job'})
                try:
                    switch(KnowledgeBase())
                finally:
                    BUSY.release()
            ok = start_job(lambda: KB.add_search(
                term, chosen, top_n, bool(body.get('graph', True))),
                f'searching “{term}”')
        elif path == '/api/add-url':
            link = str(body.get('url', '')).strip()[:2000]
            if not link.startswith(('http://', 'https://')):
                return self.send(400, {'error': 'paste a full http(s) link'})
            ok = start_job(lambda: KB.add_url(
                link, bool(body.get('graph', True))), f'adding {link}')
        elif path == '/api/conversation':
            # Start, switch to or delete a conversation in this knowledge
            # base; its pages and index are shared by all of them.
            action = body.get('action')
            conversation_id = str(body.get('id', ''))
            if action == 'new':
                KB.new_conversation()
            elif action == 'open':
                KB.open_conversation(conversation_id)
            elif action == 'delete':
                KB.delete_conversation(conversation_id)
            else:
                return self.send(400, {'error': 'unknown action'})
            KB.save()
            return self.send(200, {'current': KB.current})
        elif path in ('/api/new', '/api/open', '/api/delete'):
            # New search, reopen a saved one, or delete one. The current
            # session is saved first, so nothing is lost by switching.
            if not BUSY.acquire(blocking=False):
                return self.send(409, {'error': 'busy: wait for the job'})
            try:
                session_id = str(body.get('id', ''))
                if path == '/api/new':
                    switch(KnowledgeBase())
                elif path == '/api/open':
                    if session_id not in {s['id'] for s in sessions()}:
                        return self.send(404, {'error': 'no such session'})
                    switch(KnowledgeBase.open(session_id))
                else:
                    if session_id == KB.id:
                        switch(KnowledgeBase())
                    delete(session_id)
            finally:
                BUSY.release()
            return self.send(200, {'current': KB.id})
        elif path == '/api/ask':
            if not KB.docs:
                return self.send(400, {'error': 'search first: the '
                                       'knowledge base is empty'})
            if not BUSY.acquire(blocking=False):
                return self.send(409, {'error': 'busy: indexing is still '
                                       'running'})
            try:
                return self.send(200, answer(body))
            except Exception as error:      # shown on the page
                return self.send(500, {'error': f'{type(error).__name__}: '
                                       f'{error}'})
            finally:
                BUSY.release()
        else:
            return self.send(404, {'error': 'not found'})
        self.send(202 if ok else 409,
                  {'started': ok} if ok else {'error': 'busy: a job is '
                                              'already running'})

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    print(f'Agentic search: http://{HOST}:{PORT}  (Ctrl+C to stop)')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
