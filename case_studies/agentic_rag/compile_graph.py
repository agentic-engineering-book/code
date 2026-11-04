"""Compile concept relations into the knowledge graph with a real model.

The compile step of an LLM knowledge base: for each chapter, a model reads
the chapter's documents and proposes typed relations between concepts
("reflection requires a verifier"). The model proposes; software accepts a
relation only if its type is in the vocabulary, its evidence is a trusted
document of that chapter, and its quote appears verbatim in that document.
Every rejection is counted with its reason (the lint report), and every
accepted edge keeps its evidence, so each claim in the graph links to its
source.

Usage (from the repository root, with OPENAI_API_KEY set; build the
structural graph first with python -m case_studies.agentic_rag.graph):
  python -m case_studies.agentic_rag.compile_graph [--model MODEL]
"""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import argparse
import json
import re

from case_studies.agentic_rag.graph import GRAPH, concept_names, save
from case_studies.agentic_rag.openai_model import MODEL
from case_studies.agentic_rag.rag import corpus

RELATIONS = ['is_a', 'part_of', 'requires', 'enables', 'mitigates',
             'causes', 'contrasts_with', 'measures', 'implements']
INSTRUCTIONS = f"""You compile a knowledge graph of one chapter of the book
"Agentic Engineering from First Principles". Propose up to 15 relations
between concepts that the chapter's documents state explicitly. Use the
glossary names where they fit; otherwise use a short noun phrase from the
text. Relation types: {', '.join(RELATIONS)}. For each relation give the id
of the document that states it and a quote of 8 to 40 words copied exactly,
character for character, from that document. Do not infer relations the
text does not state."""
SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['relations'],
    'properties': {'relations': {'type': 'array', 'items': {
        'type': 'object', 'additionalProperties': False,
        'required': ['source', 'relation', 'target', 'evidence', 'quote'],
        'properties': {
            'source': {'type': 'string'},
            'relation': {'type': 'string', 'enum': RELATIONS},
            'target': {'type': 'string'},
            'evidence': {'type': 'string'},
            'quote': {'type': 'string'}}}}}}


def normal(text):
    text = text.replace('’', "'").replace('‘', "'")
    text = text.replace('“', '"').replace('”', '"')
    return ' '.join(text.lower().split())


def slug(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def chapter_documents(n):
    return [d for d in corpus('book').docs
            if d.get('chapter') == n and d['trusted']
            and d['kind'] != 'glossary' and not d.get('superseded_by')]


def propose(client, model, n, glossary):
    docs = chapter_documents(n)
    text = '\n\n'.join(f'[{d["id"]}] {d["title"]}\n{d["text"]}'
                       for d in docs)
    response = client.chat.completions.create(
        model=model, messages=[
            {'role': 'system', 'content': INSTRUCTIONS},
            {'role': 'user', 'content': f'Glossary names: {glossary}\n\n'
             f'Chapter {n} documents:\n\n{text}'}],
        response_format={'type': 'json_schema', 'json_schema': {
            'name': 'relations', 'strict': True, 'schema': SCHEMA}})
    found = json.loads(response.choices[0].message.content)['relations']
    usage = (response.usage.prompt_tokens, response.usage.completion_tokens)
    return n, found, usage


def verify(n, relation, concepts):
    """The reason to reject a proposed relation, or None to accept it."""
    docs = {d['id']: d for d in chapter_documents(n)}
    if relation['relation'] not in RELATIONS:
        return 'unknown relation type'
    if relation['evidence'] not in docs:
        return 'evidence is not a trusted document of this chapter'
    quote = normal(relation['quote'])
    if len(quote.split()) < 6:
        return 'quote too short'
    if quote not in normal(docs[relation['evidence']]['text']):
        return 'quote not found verbatim in the evidence'
    if slug(relation['source']) == slug(relation['target']):
        return 'relation from a concept to itself'
    for name in (relation['source'], relation['target']):
        if len(name.split()) > 6:
            return 'concept name too long'
    return None


def main():
    from openai import OpenAI
    import openai
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default=MODEL)
    model = parser.parse_args().model
    data = json.loads(GRAPH.read_text(encoding='utf-8'))
    data['edges'] = [e for e in data['edges'] if e['kind'] != 'extracted']
    concepts = {}
    for node in data['nodes'].values():
        if node['kind'] == 'concept':
            for name in node.get('names', [node['title']]):
                concepts[slug(name)] = node['id']
    glossary = ', '.join(n['title'] for n in data['nodes'].values()
                         if n['kind'] == 'concept' and not n.get('new'))
    client = OpenAI()
    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda n: propose(client, model, n,
                                                  glossary), range(1, 31)))
    reasons, accepted, tokens = Counter(), 0, [0, 0]
    for n, relations, usage in results:
        tokens[0] += usage[0]
        tokens[1] += usage[1]
        for relation in relations:
            # The input shows ids as [ch19-s02]; accept that format.
            relation['evidence'] = relation['evidence'].strip().strip('[]')
            reason = verify(n, relation, concepts)
            if reason:
                reasons[reason] += 1
                continue
            ends = []
            for name in (relation['source'], relation['target']):
                node_id = concepts.get(slug(name)) or concepts.get(
                    slug(name).removesuffix('s'))
                if node_id is None:     # a concept the glossary lacks
                    node_id = f'concept:{slug(name)}'
                    concepts[slug(name)] = node_id
                    data['nodes'][node_id] = {
                        'id': node_id, 'kind': 'concept', 'title': name,
                        'names': [name], 'trusted': True, 'new': True}
                ends.append(node_id)
            data['edges'].append({
                'source': ends[0], 'relation': relation['relation'],
                'target': ends[1], 'kind': 'extracted',
                'evidence': relation['evidence'],
                'quote': relation['quote'], 'chapter': n})
            accepted += 1
    # Concepts added by an earlier compile and no longer used are removed.
    used = {e[end] for e in data['edges'] for end in ('source', 'target')}
    data['nodes'] = {k: v for k, v in data['nodes'].items()
                     if not v.get('new') or k in used}
    proposed = accepted + sum(reasons.values())
    data['compiled'] = {
        'model': model, 'openai_sdk': openai.__version__,
        'compiled_at': datetime.now(timezone.utc).isoformat(
            timespec='seconds'),
        'proposed': proposed, 'accepted': accepted,
        'rejected': dict(reasons), 'input_tokens': tokens[0],
        'output_tokens': tokens[1]}
    save(data)
    print(f'proposed {proposed}, accepted {accepted}, rejected '
          f'{sum(reasons.values())}: {dict(reasons)}')
    new = sum(1 for n in data['nodes'].values() if n.get('new'))
    print(f'{len(data["nodes"])} nodes ({new} new concepts), '
          f'{len(data["edges"])} edges; tokens {tokens[0]} in, '
          f'{tokens[1]} out')


if __name__ == '__main__':
    main()
