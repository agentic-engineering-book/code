"""Experiment 14 (Chapter 7): The smallest RAG pipeline."""
import re

from agentic import PolicyModel
from agentic.context import retrieve

documents = [
    {"text": "Refund window is 30 days.", "effective_year": 2025},
    {"text": "Refund window is 14 days.", "effective_year": 2026},
]
QUESTION = "What is the current refund window?"


def answer_from_context(messages):
    """Stand-in generator: quotes the number of days in its evidence."""
    days = re.search(r"(\d+) days", messages[-1]["content"])
    return {"done": True, "answer": f"{days.group(1)} days" if days
            else "not in evidence"}


model = PolicyModel(answer_from_context)


def generate(doc):
    prompt = f"Evidence: {doc['text']}\nQuestion: {QUESTION}"
    answer = model.generate([{"role": "user", "content": prompt}])
    print("  ANSWER:", answer["answer"])
    print("  SOURCE: policy effective", doc["effective_year"])


candidates = [doc for score, doc in retrieve(
    "current refund window", documents, k=2, text=lambda d: d["text"])]
print("CANDIDATES:", len(candidates), "(equal similarity)")

print("Naive: take the top-ranked candidate")
generate(candidates[0])

print("Metadata: take the newest effective policy")
generate(max(candidates, key=lambda doc: doc["effective_year"]))
