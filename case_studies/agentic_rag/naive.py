"""Plain RAG, the baseline: retrieve once, answer from the top document."""
from case_studies.agentic_rag.rag import search, sentences, terms


def naive_rag(question):
    hits = search(question, k=1)
    if not hits:
        return {'status': 'declined', 'reason': 'nothing retrieved',
                'citations': [], 'calls': 1}
    doc = hits[0][1]
    wanted = set(terms(question))
    best = max(sentences(doc['text']),
               key=lambda s: len(wanted & set(terms(s))))
    return {'status': 'answered', 'answer': f'{doc["title"]}: {best}',
            'citations': [doc['id']], 'calls': 2}  # one search, one answer
