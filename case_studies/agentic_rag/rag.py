"""Shared parts of the Chapter 31 case study: corpus, tools and contract.

The corpus is the book itself (chapter questions, principles, takeaways and
experiments) plus planted documents that test the agent: an outdated draft
principle, a first-edition fact sheet, and an untrusted reader comment.
"""
from pathlib import Path
import json
import math
import re

from agentic.context import cosine, tokenize

HERE = Path(__file__).parent
CORPUS = json.loads((HERE / 'corpus.json').read_text(encoding='utf-8'))
DOCS = {doc['id']: doc for doc in CORPUS}
STOPWORDS = set(
    'a about an and are as at be book by did do doe does for from give has '
    'have how in is it its many much of on or say says that the this to was '
    'what when which who why with you your'.split())
COSTS = {'search': 0.02, 'read': 0.01, 'answer': 0.0, 'decline': 0.0}


def terms(text):
    """Content words: the book's tokenizer without stop words."""
    return [t for t in tokenize(text) if t not in STOPWORDS]


def document_frequencies():
    counts = {}
    for doc in CORPUS:
        for word in set(terms(doc['title'] + ' ' + doc['text'])):
            counts[word] = counts.get(word, 0) + 1
    return counts


# Rare words count for more (Chapter 7: from word counts towards embeddings).
IDF = {w: math.log(len(CORPUS) / n) for w, n in document_frequencies().items()}


def search(query, k=4):
    """Rank documents by TF-IDF cosine similarity to the query."""
    vocabulary = sorted(set(terms(query)) & IDF.keys())
    if not vocabulary:
        return []

    def vector(text):
        words = terms(text)
        return [words.count(t) * IDF[t] for t in vocabulary]
    query_vector = vector(query)
    scored = []
    for doc in CORPUS:
        similarity = cosine(query_vector, vector(doc['title'] + ' '
                                                 + doc['text']))
        scored.append((round(similarity, 3), doc))
    scored.sort(key=lambda pair: -pair[0])
    return [(score, doc) for score, doc in scored[:k] if score > 0]


def read(doc_id):
    if doc_id not in DOCS:
        raise ValueError(f'unknown document: {doc_id!r}')
    return DOCS[doc_id]


# The decision contract (Chapter 2): every model decision must match one.
CONTRACT = {'search': {'query': str}, 'read': {'doc_id': str},
            'answer': {'text': str, 'citations': list},
            'decline': {'reason': str}}


def validate(decision):
    """Return the decision if it satisfies the contract; raise otherwise."""
    if not isinstance(decision, dict) or (
            decision.get('action') not in CONTRACT):
        raise ValueError(f'unknown action: {decision!r}'[:120])
    for field, kind in CONTRACT[decision['action']].items():
        if not isinstance(decision.get(field), kind):
            raise ValueError(f'{decision["action"]} needs {field} '
                             f'as {kind.__name__}')
    return decision


def sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
