"""Experiment 15: Reranking with a LangChain model judge. See README."""
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from agentic.context import retrieve
from framework_examples.support import chat

DOCUMENTS = [
    Document("Refund window history: the refund window was 30 days when "
             "the refund window was introduced in 2025.", id="history"),
    Document("Current policy: claims must be made within 14 days.",
             id="current"),
    Document("Shipping takes 3 to 5 days.", id="shipping"),
]
QUESTION = "What is the current refund window?"


def first_stage(k):
    """Fast retrieval by word overlap: the candidate set."""
    return RunnableLambda(lambda question: [
        (round(score, 2), doc) for score, doc in
        retrieve(question, DOCUMENTS, k=k, text=lambda d: d.page_content)])


def reranker():
    """Slow, task-aware scoring: the model reads question and passage."""
    judge = ChatPromptTemplate.from_messages([
        ("system", "Rate how well the passage answers the question, from "
                   "0 (not at all) to 10 (fully). Reply with the number "
                   "only."),
        ("human", "Question: {question}\nPassage: {passage}"),
    ]) | chat() | StrOutputParser()

    def rerank(candidates):
        docs = [doc for _, doc in candidates]
        scores = judge.batch([{"question": QUESTION,
                               "passage": doc.page_content} for doc in docs])
        return sorted(zip(map(int, scores), docs),
                      key=lambda pair: pair[0], reverse=True)
    return RunnableLambda(rerank)


def show(title, ranking, unit=""):
    return [title] + [f"  {rank}. {doc.id:<9} {score}{unit}"
                      for rank, (score, doc) in enumerate(ranking, 1)]


def run():
    lines = []
    for k in (3, 1):
        candidates = first_stage(k).invoke(QUESTION)
        lines += show(f"FIRST STAGE (word overlap, k={k}):", candidates)
        lines += show("RERANKED (model):",
                      reranker().invoke(candidates), "/10")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
