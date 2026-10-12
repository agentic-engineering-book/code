"""Experiment 15: LangChain reranking stage and its zero-recall boundary."""
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

HISTORY = Document("Refund policy history ... 30 days", id="history")
CURRENT = Document("Current refund window: 14 days", id="current")
SHIPPING = Document("Shipping takes 3-5 days", id="shipping")


def rerank_score(doc):
    text = doc.page_content.lower()
    return ("refund" in text) + 2 * ("current" in text)


def run():
    rerank = RunnableLambda(
        lambda docs: sorted(docs, key=rerank_score, reverse=True))
    ids = RunnableLambda(lambda docs: [doc.id for doc in docs])
    pipeline = rerank | ids
    return {"after": pipeline.invoke([HISTORY, CURRENT, SHIPPING]),
            "zero_recall": pipeline.invoke([HISTORY, SHIPPING])}


if __name__ == "__main__":
    print(run())
