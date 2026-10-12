"""Experiment 15 (Chapter 7): Reranking."""
history = {"id": "history", "text": "Refund policy history ... 30 days"}
current = {"id": "current", "text": "Current refund window: 14 days"}
shipping = {"id": "shipping", "text": "Shipping takes 3-5 days"}


def rerank_score(doc):
    score = 0
    if "refund" in doc["text"].lower():
        score += 1
    if "current" in doc["text"].lower():
        score += 2
    return score


def show(title, docs):
    print(title)
    for rank, doc in enumerate(docs, start=1):
        print(f"{rank}. {doc['id']}")


retrieved = [history, current, shipping]
show("BEFORE:", retrieved)
show("AFTER:", sorted(retrieved, key=rerank_score, reverse=True))

retrieved = [history, shipping]
show("ZERO RECALL, AFTER:", sorted(retrieved, key=rerank_score,
                                  reverse=True))
