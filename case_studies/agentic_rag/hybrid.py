"""Hybrid retrieval for the Chapter 31 agent: vector search plus graph search.

Vector search ranks the full-book documents by the cosine similarity of
their embeddings to the query's. Graph search links the query to graph
nodes (a chapter or experiment it names, concepts it mentions, the author)
and to the top vector hits, then walks typed links to the documents and
compiled relations they lead to. Reciprocal rank fusion merges the two
rankings, and every result carries a short snippet and the route that found
it, so the model can see why a document was suggested. Retrieval only
suggests: the agent must still read a document to cite it.

Build the embedding index once (from the repository root, with
OPENAI_API_KEY set; about 100,000 tokens):
  python -m case_studies.agentic_rag.hybrid
"""
from functools import lru_cache
from pathlib import Path
import json
import re

import numpy as np

from case_studies.agentic_rag.graph import concept_names, load
from case_studies.agentic_rag.rag import corpus, sentences, terms

HERE = Path(__file__).parent
INDEX = HERE / 'book_embeddings.npy'
INDEX_META = HERE / 'book_embeddings.json'
EMBEDDING_MODEL = 'text-embedding-3-small'
RRF_K = 60                      # the usual constant for rank fusion
SNIPPET_WORDS = 60


def embed(texts, client=None):
    if client is None:
        from openai import OpenAI
        client = OpenAI()
    vectors = []
    for start in range(0, len(texts), 100):
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=[t[:8000] for t in texts[start:start + 100]])
        vectors += [item.embedding for item in response.data]
    matrix = np.array(vectors, dtype=np.float32)
    return matrix / np.linalg.norm(matrix, axis=1, keepdims=True)


def build_index():
    docs = corpus('book').docs
    matrix = embed([d['title'] + '\n' + d['text'] for d in docs])
    np.save(INDEX, matrix.astype(np.float16))
    INDEX_META.write_text(json.dumps({
        'model': EMBEDDING_MODEL, 'ids': [d['id'] for d in docs]}),
        encoding='utf-8')
    return matrix


def snippet(doc, query):
    """The document's sentences that share most words with the query, in
    their original order, up to about SNIPPET_WORDS words."""
    text = doc['text']
    if len(text.split()) <= SNIPPET_WORDS:
        return text
    wanted = set(terms(query))
    ranked = sorted(enumerate(sentences(text)),
                    key=lambda pair: -len(wanted & set(terms(pair[1]))))
    chosen, size = [], 0
    for index, sentence in ranked:
        if size and size + len(sentence.split()) > SNIPPET_WORDS:
            break
        chosen.append((index, sentence))
        size += len(sentence.split())
    return ' … '.join(s for _, s in sorted(chosen))


class Hybrid:
    def __init__(self, client=None):
        meta = json.loads(INDEX_META.read_text(encoding='utf-8'))
        self.docs = corpus('book')
        self.ids = meta['ids']
        self.matrix = np.load(INDEX).astype(np.float32)
        self.graph = load()
        self.client = client
        self.cache = {}
        # Concepts named in a query seed graph search. The book's own title
        # ("Agentic Engineering") is not a useful seed: every question is
        # about it, and models often add it to their queries.
        title = 'agentic engineering from first principles'
        self.concepts = sorted(
            ((name, node['id']) for node in self.graph.nodes.values()
             if node['kind'] == 'concept'
             for name in node.get('names', [node['title']])
             if len(name) >= 4 and name.lower() not in title),
            key=lambda pair: -len(pair[0]))

    def vector_search(self, query, k=8):
        if query not in self.cache:
            self.cache[query] = embed([query], self.client)[0]
        scores = self.matrix @ self.cache[query]
        order = np.argsort(-scores)[:k]
        return [(self.ids[i], float(scores[i])) for i in order]

    def seeds(self, query):
        """Graph nodes the query names directly."""
        found = []
        for word, number in re.findall(
                r'\b(chapter|experiment|part)s?\s+(\d+|[ivx]+)\b',
                query, re.I):
            node = self.graph.resolve(f'{word} {number}')
            if node:
                found.append((node, f'named in the question: {word} '
                                    f'{number}'))
        if re.search(r'\b(author|wrote|written)\b', query, re.I):
            found.append(('author', 'the question asks about the author'))
        lower, taken = query.lower(), []
        for name, node in self.concepts:
            if node in taken or len(taken) >= 3:
                continue
            if re.search(rf'(?<![\w-]){re.escape(name.lower())}s?(?![\w-])',
                         lower):
                taken.append(node)
                found.append((node, f'concept in the question: {name}'))
        return found

    def walk(self, node_id):
        """Documents one or two typed hops from a node, best first."""
        g, out = self.graph, []
        node = g.nodes[node_id]
        if node.get('doc'):
            return [(r['id'], r['relation']) for r in g.related(node_id)]
        for e in g.out[node_id]:
            target = g.nodes[e['target']]
            if target.get('doc') and e['relation'] != 'next_section':
                out.append((e['target'], e['relation']))
            elif e['relation'] == 'developed_in':      # concept -> chapter
                for c in g.out[e['target']]:
                    if c['relation'] == 'has_principle':
                        out.append((c['target'], f'principle of '
                                    f'{e["target"]}, where it is developed'))
        for e in g.into[node_id]:
            source = g.nodes[e['source']]
            if source.get('doc') and source['trusted']:
                out.append((e['source'], e['relation']))
        order = {'has_principle': 0, 'defined_by': 0, 'described_in': 0,
                 'has_question': 1, 'has_experiment': 2, 'has_takeaways': 3}
        out.sort(key=lambda pair: order.get(pair[1], 4))
        return out

    def facts(self, seeds, limit=6):
        """Compiled relations around the seed concepts, with evidence."""
        g, found = self.graph, []
        for node_id, _ in seeds:
            for e in g.out[node_id] + g.into[node_id]:
                if e['kind'] == 'extracted' and len(found) < limit:
                    found.append({
                        'fact': f'{g.nodes[e["source"]]["title"]} '
                                f'{e["relation"].replace("_", " ")} '
                                f'{g.nodes[e["target"]]["title"]}',
                        'evidence': e['evidence'], 'quote': e['quote']})
        return found

    def graph_search(self, query, vector_hits, k=8):
        ranked, seen = [], set()
        seeds = self.seeds(query)
        starts = seeds + [(doc_id, 'top vector hit')
                          for doc_id, _ in vector_hits[:5]]
        for node_id, why in starts:
            steps = self.walk(node_id)
            if why == 'top vector hit':     # follow only the strong links
                steps = [(d, r) for d, r in steps
                         if r == 'newer version'
                         or r.startswith(('principle of chapter',
                                          'question of chapter'))]
            for doc_id, relation in steps:
                if doc_id not in seen:
                    seen.add(doc_id)
                    title = self.graph.nodes[node_id]['title']
                    ranked.append((doc_id, f'{relation} of {title} ({why})'
                                   if not why.startswith('top')
                                   else f'{relation} (via {node_id})'))
        return ranked[:k], seeds

    def search(self, query, k=6):
        vector = self.vector_search(query)
        graph_hits, seeds = self.graph_search(query, vector)
        fused = {}
        for rank, (doc_id, score) in enumerate(vector):
            entry = fused.setdefault(doc_id, {'score': 0, 'via': []})
            entry['score'] += 1 / (RRF_K + rank)
            entry['via'].append(f'vector {score:.2f}')
        for rank, (doc_id, route) in enumerate(graph_hits):
            entry = fused.setdefault(doc_id, {'score': 0, 'via': []})
            entry['score'] += 1 / (RRF_K + rank)
            entry['via'].append(f'graph: {route}')
        best = sorted(fused.items(), key=lambda pair: -pair[1]['score'])[:k]
        hits = []
        for doc_id, entry in best:
            doc = self.docs.by_id[doc_id]
            hits.append({'id': doc_id, 'title': doc['title'],
                         'score': round(entry['score'] * 100, 2),
                         'trusted': doc['trusted'],
                         'edition': doc['edition'], 'via': entry['via'],
                         'snippet': snippet(doc, query)})
        return {'hits': hits, 'facts': self.facts(seeds)}


@lru_cache(maxsize=None)
def retriever():
    return Hybrid()


if __name__ == '__main__':
    matrix = build_index()
    print(f'embedded {matrix.shape[0]} documents with {EMBEDDING_MODEL}; '
          f'saved {INDEX.name}')
