"""Experiment 15 (Chapter 7): Reranking."""
from agentic.context import retrieve
from agentic.live import OpenAIModel

judge = OpenAIModel(system="Rate how well the passage answers the "
                           "question, from 0 (not at all) to 10 (fully). "
                           "Reply with the number only.")

documents = {
    "history": "Refund window history: the refund window was 30 days "
               "when the refund window was introduced in 2025.",
    "current": "Current policy: claims must be made within 14 days.",
    "shipping": "Shipping takes 3 to 5 days.",
}
QUESTION = "What is the current refund window?"


def first_stage(k):
    """Fast retrieval by word overlap: the candidate set."""
    return [(round(score, 2), name) for score, name in
            retrieve(QUESTION, documents, k=k, text=documents.get)]


def rerank(candidates):
    """Slow, task-aware scoring: the model reads question and passage."""
    scored = []
    for _, name in candidates:
        prompt = f"Question: {QUESTION}\nPassage: {documents[name]}"
        reply = judge.generate([{"role": "user", "content": prompt}])
        scored.append((int(reply["answer"]), name))
    return sorted(scored, reverse=True)


def show(title, ranking, unit=""):
    print(title)
    for rank, (score, name) in enumerate(ranking, start=1):
        print(f"  {rank}. {name:<9} {score}{unit}")


candidates = first_stage(k=3)
show("FIRST STAGE (word overlap):", candidates)
show("RERANKED (model):", rerank(candidates), "/10")

candidates = first_stage(k=1)
show("FIRST STAGE WITH k=1:", candidates)
show("RERANKED (model):", rerank(candidates), "/10")
