"""Experiment 14 (Chapter 7): The smallest RAG pipeline."""
import re

from agentic.context import retrieve
from agentic.live import OpenAIModel

model = OpenAIModel(system="Answer the question from the evidence only. "
                           "Reply in one short sentence.")

documents = [
    {"text": "Refund window is 30 days.", "effective_year": 2025},
    {"text": "Refund window is 14 days.", "effective_year": 2026},
]
QUESTION = "What is the current refund window?"

scored = retrieve(QUESTION, documents, k=2, text=lambda doc: doc["text"])
print("SIMILARITY:", ", ".join(f"{score:.2f}" for score, doc in scored))
old, new = [doc for score, doc in scored]  # equal scores: list order


def dated(doc):
    return f"[effective {doc['effective_year']}] {doc['text']}"


EVIDENCE = {
    "TOP CANDIDATE ONLY": old["text"],
    "BOTH, OLD POLICY FIRST": old["text"] + "\n" + new["text"],
    "BOTH, NEW POLICY FIRST": new["text"] + "\n" + old["text"],
    "BOTH, NEW FIRST, WITH DATES": dated(new) + "\n" + dated(old),
}

for name, evidence in EVIDENCE.items():
    prompt = f"Evidence:\n{evidence}\n\nQuestion: {QUESTION}"
    messages = [{"role": "user", "content": prompt}]
    answers = []
    for trial in range(3):
        answer = model.generate(messages)["answer"]
        days = re.search(r"(\d+) days", answer)
        answers.append(days.group(0) if days else "no number")
    print(f"{name:<28} answers: {', '.join(answers)}")
