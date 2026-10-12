"""Experiment 13 (Chapter 7): Bag-of-words retrieval."""
from agentic.context import retrieve, tokenize

documents = [
    "Shipping usually takes 3 to 5 days.",
    "Refunds are accepted within 30 days.",
    "Gold customers receive free delivery.",
]
query = "refund days"

print("QUERY TERMS:", tokenize(query))
for score, doc in retrieve(query, documents, k=3):
    print(f"  {score:.2f}  {doc}")

best_score, best = retrieve(query, documents, k=1)[0]
print("RETRIEVED:", best)
