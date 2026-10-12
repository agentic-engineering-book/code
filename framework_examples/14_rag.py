"""Experiment 14: LangChain retriever, metadata filter, prompt, generator."""
import re

from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableLambda

POLICIES = [
    Document("Refund window is 30 days.", metadata={"effective_year": 2025}),
    Document("Refund window is 14 days.", metadata={"effective_year": 2026}),
]


class KeywordRetriever(BaseRetriever):
    documents: list[Document]

    def _get_relevant_documents(self, query, *, run_manager):
        terms = set(re.findall(r"[a-z]+", query.lower()))
        return [d for d in self.documents
                if terms & set(re.findall(r"[a-z]+", d.page_content.lower()))]


def newest(docs):
    doc = max(docs, key=lambda d: d.metadata["effective_year"])
    return {"evidence": doc.page_content,
            "year": doc.metadata["effective_year"]}


def fake_generator(prompt_value):
    """Deterministic stand-in for a model: quotes the days in its evidence."""
    days = re.search(r"(\d+) days", prompt_value.to_string())
    return days.group(1) + " days" if days else "not in evidence"


def run():
    retriever = KeywordRetriever(documents=POLICIES)
    prompt = PromptTemplate.from_template(
        "Evidence ({year}): {evidence}\nWhat is the current refund window?")
    select = RunnableLambda(newest)
    answer = select | prompt | RunnableLambda(fake_generator)
    candidates = retriever.invoke("current refund window")
    return {"candidates": len(candidates),
            "answer": answer.invoke(candidates),
            "source_year": newest(candidates)["year"]}


if __name__ == "__main__":
    print(run())
