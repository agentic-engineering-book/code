"""Context selection, retrieval and compression helpers (Chapters 6, 7, 9)."""
import math
import re


def coverage(context, required):
    """Fraction of the required fact names present in a context dict."""
    return len(required & context.keys()) / len(required)


def select_top(facts, budget):
    """Keep the `budget` highest-scoring (fact, score) pairs."""
    ranked = sorted(facts, key=lambda fact: fact[1], reverse=True)
    return ranked[:budget]


def tokenize(text):
    """Lowercase words without punctuation; a trailing plural s is dropped."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words]


def vectorize(text, vocabulary):
    words = tokenize(text)
    return [words.count(term) for term in vocabulary]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def retrieve(query, documents, k=3, text=lambda doc: doc):
    """Rank documents by bag-of-words cosine similarity to the query."""
    vocabulary = sorted(set(tokenize(query)))
    query_vector = vectorize(query, vocabulary)
    scored = [(cosine(query_vector, vectorize(text(doc), vocabulary)), doc)
              for doc in documents]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return scored[:k]


def compress(context, keep):
    """Keep only the fields declared necessary for the next phase."""
    return {key: value for key, value in context.items() if key in keep}
