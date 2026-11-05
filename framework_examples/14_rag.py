"""Experiment 14: The smallest RAG pipeline in LangChain. See README."""
import re

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from agentic.context import retrieve
from framework_examples.support import chat

POLICIES = [
    Document("Refund window is 30 days.", metadata={"effective_year": 2025}),
    Document("Refund window is 14 days.", metadata={"effective_year": 2026}),
]
QUESTION = "What is the current refund window?"


def dated(doc):
    return f"[effective {doc.metadata['effective_year']}] {doc.page_content}"


def run():
    scored = retrieve(QUESTION, POLICIES, k=2,
                      text=lambda doc: doc.page_content)
    old, new = [doc for score, doc in scored]  # equal scores: list order
    evidence = {
        "TOP CANDIDATE ONLY": old.page_content,
        "BOTH, OLD POLICY FIRST": old.page_content + "\n" + new.page_content,
        "BOTH, NEW POLICY FIRST": new.page_content + "\n" + old.page_content,
        "BOTH, NEW FIRST, WITH DATES": dated(new) + "\n" + dated(old),
    }
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Answer the question from the evidence only. "
                   "Reply in one short sentence."),
        ("human", "Evidence:\n{evidence}\n\nQuestion: {question}")])
    chain = prompt | chat() | StrOutputParser()
    lines = ["SIMILARITY: " + ", ".join(f"{s:.2f}" for s, d in scored)]
    for name, text in evidence.items():
        replies = chain.batch([{"evidence": text, "question": QUESTION}] * 3)
        days = [re.search(r"\d+ days", reply) for reply in replies]
        answers = [m.group(0) if m else "no number" for m in days]
        lines.append(f"{name:<28} answers: {', '.join(answers)}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
