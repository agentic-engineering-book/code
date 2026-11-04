"""Shared parts of the Chapter 31 case study: corpora, tools and contract.

Two corpora. 'lectures' is the book as short typed documents (chapter
questions, principles, takeaways and experiments) plus planted documents
that test the agent: an outdated draft principle, a first-edition fact
sheet, and an untrusted reader comment. 'book' adds every section of
Chapters 1 to 30, chunked at section and paragraph boundaries.
"""
from functools import lru_cache
from pathlib import Path
import json
import math
import re

from agentic.context import cosine, tokenize

HERE = Path(__file__).parent
FILES = {'lectures': 'corpus.json', 'book': 'book_corpus.json'}
STOPWORDS = set(
    'a about an and are as at be book by did do doe does for from give has '
    'have how in is it its many much of on or say says that the this to was '
    'what when which who why with you your'.split())
COSTS = {'search': 0.02, 'read': 0.01, 'explore': 0.01, 'answer': 0.0,
         'decline': 0.0}


def terms(text):
    """Content words: the book's tokenizer without stop words."""
    return [t for t in tokenize(text) if t not in STOPWORDS]


class Corpus:
    def __init__(self, docs):
        self.docs = docs
        self.by_id = {doc['id']: doc for doc in docs}
        self.words = [terms(d['title'] + ' ' + d['text']) for d in docs]
        counts = {}
        for words in self.words:
            for word in set(words):
                counts[word] = counts.get(word, 0) + 1
        # Rare words count for more (Chapter 7: word counts to embeddings).
        self.idf = {w: math.log(len(docs) / n) for w, n in counts.items()}

    def search(self, query, k=4):
        """Rank documents by TF-IDF cosine similarity to the query."""
        vocabulary = sorted(set(terms(query)) & self.idf.keys())
        if not vocabulary:
            return []

        def vector(words):
            return [words.count(t) * self.idf[t] for t in vocabulary]
        query_vector = vector(terms(query))
        scored = []
        for doc, words in zip(self.docs, self.words):
            similarity = cosine(query_vector, vector(words))
            scored.append((round(similarity, 3), doc))
        scored.sort(key=lambda pair: -pair[0])
        return [(score, doc) for score, doc in scored[:k] if score > 0]

    def read(self, doc_id):
        if doc_id not in self.by_id:
            raise ValueError(f'unknown document: {doc_id!r}')
        return self.by_id[doc_id]


@lru_cache(maxsize=None)
def corpus(name='lectures'):
    path = HERE / FILES[name]
    return Corpus(json.loads(path.read_text(encoding='utf-8')))


DEFAULT = corpus('lectures')
CORPUS, DOCS, IDF = DEFAULT.docs, DEFAULT.by_id, DEFAULT.idf
search, read = DEFAULT.search, DEFAULT.read


# The decision contract (Chapter 2): every model decision must match one.
CONTRACT = {'search': {'query': str}, 'read': {'doc_id': str},
            'explore': {'node': str},
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


# A full stop ends a sentence unless it follows an initial ("M.") or a
# common abbreviation ("e.g.", "i.e.", "et al.", "vs.").
SENTENCE_END = re.compile(
    r'(?<!\b[A-Z]\.)(?<!\be\.g\.)(?<!\bi\.e\.)(?<!\bal\.)(?<!\bvs\.)'
    r'(?<=[.!?])\s+')


def sentences(text):
    return [s.strip() for s in SENTENCE_END.split(text) if s.strip()]
