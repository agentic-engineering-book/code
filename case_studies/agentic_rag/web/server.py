"""Ask the book: a local web page for trying the Chapter 31 agent.

Runs on your own machine only (127.0.0.1). The page sends a question here;
this server runs the first-principles agent with a real OpenAI model (or the
deterministic stand-in) and returns the answer, its citations and the full
trace. The API key stays in this process's environment and never reaches
the browser.

Usage (from the repository root, with OPENAI_API_KEY set):
  python -m case_studies.agentic_rag.web.server
then open http://127.0.0.1:8770
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json
import time

from agentic import PolicyModel

from case_studies.agentic_rag import graph, hybrid
from case_studies.agentic_rag.agent import RULES, run, scripted_policy
from case_studies.agentic_rag.evaluate import score
from case_studies.agentic_rag.naive import naive_rag
from case_studies.agentic_rag.openai_model import (
    MODEL, OpenAIRagModel, standalone_question)
from case_studies.agentic_rag.questions import QUESTIONS
from case_studies.agentic_rag.rag import COSTS, FILES, corpus

HOST, PORT = '127.0.0.1', 8770
PAGE = Path(__file__).with_name('index.html')


def links_of(name):
    try:
        found = graph.load().explore(name, limit=12)
    except ValueError:
        return []
    return [{'relation': l['relation'], 'node': l['node'],
             'title': l['title'], 'trusted': l.get('trusted', True),
             'extracted': l['source'] == 'extracted'}
            for l in found['links']]


def step_view(step, docs, retriever=None):
    """A trace step as JSON, with search results re-listed for display
    (the hybrid retriever caches query embeddings, so this is free)."""
    kind = step[0]
    if kind == 'search' and retriever is not None:
        found = retriever.search(step[1])
        return {'kind': kind, 'query': step[1], 'hybrid': True,
                'hits': found['hits'], 'facts': found['facts']}
    if kind == 'search':
        hits = [{'id': d['id'], 'title': d['title'], 'score': s,
                 'trusted': d['trusted']} for s, d in docs.search(step[1])]
        return {'kind': kind, 'query': step[1], 'hits': hits}
    if kind == 'read':
        doc = docs.by_id.get(step[1], {})
        return {'kind': kind, 'id': step[1], 'title': doc.get('title'),
                'trusted': doc.get('trusted', True)}
    if kind == 'explore':
        return {'kind': kind, 'node': step[1], 'links': links_of(step[1])}
    if kind == 'answer':
        return {'kind': kind, 'citations': step[1], 'refused': step[2]}
    if kind == 'decline':
        refused = step[2] if len(step) > 2 else []
        return {'kind': kind, 'reason': step[1], 'refused': refused}
    return {'kind': kind, 'detail': str(step[1])}


def graph_view(steps, max_nodes=70):
    """The part of the knowledge graph one run touched, for drawing: each
    node with its roles (hit, read, explored, link, cited, refused) and the
    step at which it first appeared, plus the graph's links among them."""
    g = graph.load()
    nodes, order = {}, []

    def touch(node_id, role, step):
        if node_id not in g.nodes:
            return
        if node_id not in nodes:
            if len(nodes) >= max_nodes and role in ('hit', 'link'):
                return
            nodes[node_id] = {'roles': [], 'step': step}
            order.append(node_id)
        if role not in nodes[node_id]['roles']:
            nodes[node_id]['roles'].append(role)
    for i, step in enumerate(steps, 1):
        if step['kind'] == 'search':
            for hit in step['hits']:
                touch(hit['id'], 'hit', i)
        elif step['kind'] == 'read':
            touch(step['id'], 'read', i)
        elif step['kind'] == 'explore':
            touch(g.resolve(step['node']) or '', 'explored', i)
            for link in step['links']:
                touch(link['node'], 'link', i)
        elif step['kind'] == 'answer':
            role = 'refused' if step['refused'] else 'cited'
            for doc_id in step['citations']:
                touch(doc_id, role, i)
    # Anchor each document the agent used (read, explored or cited) to its
    # chapter, or the book, so the picture shows where the evidence came
    # from; and show the people and concepts that cited documents link to.
    # Search hits that were never read get no context: they are noise.
    used = {'read', 'explored', 'cited', 'refused'}
    for node_id in list(order):
        info = nodes[node_id]
        if not used & set(info['roles']):
            continue
        parents = [e['source'] for e in g.into[node_id]
                   if e['source'].startswith(('chapter:', 'concept:'))
                   and e['relation'] != 'mentioned_in']
        for parent in parents[:1] or (['book'] if g.nodes[node_id].get(
                'doc') and not g.nodes[node_id].get('chapter') else []):
            touch(parent, 'context', info['step'])
        if 'cited' in info['roles']:
            linked = [e['target'] for e in g.out[node_id]
                      if g.nodes[e['target']]['kind'] == 'person']
            linked += [e['source'] for e in g.into[node_id]
                       if g.nodes[e['source']]['kind'] in ('person',
                                                           'concept')]
            for other in linked[:4]:
                touch(other, 'context', info['step'])
    edges = [{'from': e['source'], 'to': e['target'],
              'relation': e['relation'], 'kind': e['kind']}
             for node_id in nodes for e in g.out[node_id]
             if e['target'] in nodes]
    return {'nodes': [{'id': n, 'title': g.nodes[n]['title'],
                       'kind': g.nodes[n]['kind'],
                       'trusted': g.nodes[n]['trusted'],
                       'superseded': any(e['relation'] == 'superseded_by'
                                         for e in g.out[n]),
                       **nodes[n]} for n in order],
            'edges': edges}


def neighbours(node_id):
    """One node's links, for expanding the graph view in the browser."""
    g = graph.load()
    found = g.explore(node_id, limit=40)
    nodes = [{'id': l['node'], 'title': l['title'], 'kind': l['kind'],
              'trusted': l.get('trusted', True)} for l in found['links']]
    edges = [{'from': found['node'], 'to': l['node'],
              'relation': l['relation'], 'kind': l['source']}
             for l in found['links']]
    center = g.nodes[found['node']]
    return {'center': {'id': found['node'], 'title': center['title'],
                       'kind': center['kind'],
                       'trusted': center['trusted']},
            'nodes': nodes, 'edges': edges,
            'more': found.get('more_links', 0)}


def verdict(question, outcome):
    """Score an outcome when the question is one of the evaluation set."""
    case = next((c for c in QUESTIONS
                 if c['question'].lower() == question.lower()), None)
    if case is None:
        return None
    correct, unsafe, cited = score(case, outcome)
    if case.get('decline'):
        expected = 'the book has no answer, so the agent should decline'
    else:
        phrases = ' and '.join(' or '.join(f'"{a}"' for a in group)
                               for group in case['must'])
        expected = (f'the answer must contain {phrases}; supporting '
                    f'documents: {", ".join(case["gold"]) or "any trusted"}')
    label = 'unsafe' if unsafe else ('correct' if correct else 'wrong')
    return {'id': case['id'], 'label': label, 'expected': expected,
            'cited_gold': cited}


def ask(asked, model_name, rules, source, history=()):
    start = time.perf_counter()
    # A follow-up is rewritten to stand alone before anything is searched,
    # so search and every check see the whole question. The stand-in model
    # cannot rewrite, so it takes each question as asked.
    question, rewrite_usage = asked, None
    if model_name == 'stand-in':
        model, calls = PolicyModel(scripted_policy), []
    else:
        question, rewrite_usage = standalone_question(
            list(history), asked, model_name)
        model = OpenAIRagModel(model_name,
                               graph=source in ('graph', 'hybrid'),
                               hybrid=source == 'hybrid')
        calls = model.calls             # filled in as the agent runs
    with_graph = source in ('graph', 'hybrid')
    use_graph = graph.load() if with_graph else None
    # The stand-in model reads plain search results, so it gets no hybrid.
    fused = (hybrid.retriever() if source == 'hybrid'
             and model_name != 'stand-in' else None)
    text_source = 'book' if with_graph else source
    docs = corpus(text_source)
    outcome = run(question, model, source=text_source, graph=use_graph,
                  retriever=fused, **rules)
    plain = naive_rag(question, text_source)
    steps = [step_view(s, docs, fused) for s in outcome['trace']]
    calls = calls + ([rewrite_usage] if rewrite_usage else [])
    return {
        'asked': asked, 'question': question,
        'rewritten': question != asked,
        'status': outcome['status'], 'answer': outcome.get('answer'),
        'reason': outcome.get('reason'),
        'citations': [{'id': c, 'title': docs.by_id.get(c, {}).get('title', c)}
                      for c in outcome.get('citations', [])],
        'trace': steps, 'graph': graph_view(steps),
        'limits': {'steps': 10, 'cost': 0.2},
        'steps': outcome['budget'].steps_used,
        'cost_units': round(outcome['budget'].cost_used, 3),
        'model': model_name, 'corpus': source,
        'documents': len(docs.docs),
        'input_tokens': sum(c['input_tokens'] for c in calls),
        'output_tokens': sum(c['output_tokens'] for c in calls),
        'seconds': round(time.perf_counter() - start, 1),
        'verdict': verdict(question, outcome),
        'plain': {'status': plain['status'],
                  'answer': plain.get('answer') or plain.get('reason'),
                  'citations': plain.get('citations', []),
                  'verdict': verdict(question, plain)}}


class Handler(BaseHTTPRequestHandler):
    def send(self, status, body, kind='application/json'):
        data = body if isinstance(body, bytes) else json.dumps(
            body, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', f'{kind}; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == '/':
            self.send(200, PAGE.read_bytes(), 'text/html')
        elif url.path == '/api/setup':
            sizes = {name: len(corpus(name).docs) for name in FILES}
            g = graph.load()
            sizes['graph'] = {'nodes': len(g.nodes), 'edges': len(g.edges)}
            sizes['embedding'] = hybrid.EMBEDDING_MODEL
            self.send(200, {'model': MODEL, 'rules': list(RULES),
                            'costs': COSTS,
                            'questions': QUESTIONS, 'corpora': sizes})
        elif url.path == '/api/neighbours':
            node_id = parse_qs(url.query).get('id', [''])[0]
            try:
                self.send(200, neighbours(node_id))
            except ValueError as error:
                self.send(404, {'error': str(error)})
        elif url.path == '/api/doc':
            doc_id = parse_qs(url.query).get('id', [''])[0]
            doc = corpus('book').by_id.get(doc_id)   # a superset
            if doc is None and doc_id in graph.load().nodes:
                node = graph.load().explore(doc_id, limit=40)
                lines = [f'{l["relation"]} → {l["title"]}'
                         + (f' (quote in {l["evidence"]})'
                            if l.get('evidence') else '')
                         for l in node['links']]
                doc = {'id': doc_id, 'title': node['title'],
                       'kind': f'graph node: {node["kind"]}',
                       'edition': '—', 'trusted': True,
                       'text': ' · '.join(lines)}
            self.send(200 if doc else 404, doc or {'error': 'not found'})
        else:
            self.send(404, {'error': 'not found'})

    def do_POST(self):
        if urlparse(self.path).path != '/api/ask':
            return self.send(404, {'error': 'not found'})
        length = int(self.headers.get('Content-Length', 0))
        try:
            body = json.loads(self.rfile.read(length) or b'{}')
            question = str(body.get('question', '')).strip()[:500]
            if not question:
                return self.send(400, {'error': 'empty question'})
            rules = {k: bool(v) for k, v in body.get('rules', {}).items()
                     if k in RULES}
            model = 'stand-in' if body.get('model') == 'stand-in' else MODEL
            source = body.get('corpus')
            if source not in ('lectures', 'book', 'graph', 'hybrid'):
                source = 'graph'                          # default
            history = [{'question': str(t.get('question', ''))[:500],
                        'answer': str(t.get('answer', ''))[:1500]}
                       for t in body.get('history', [])[-4:]]
            self.send(200, ask(question, model, rules, source, history))
        except Exception as error:      # shown on the page, not hidden
            self.send(500, {'error': f'{type(error).__name__}: {error}'})

    def log_message(self, format, *args):
        pass


if __name__ == '__main__':
    print(f'Ask the book: http://{HOST}:{PORT}  (Ctrl+C to stop)')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
