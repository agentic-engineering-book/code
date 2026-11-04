"""Experiment 13 (Chapter 7): Word counts vs embeddings."""
from agentic.context import cosine, retrieve
from agentic.live import embed

documents = [
    "Shipping usually takes 3 to 5 days.",
    "Refunds are accepted within 30 days.",
    "Gold customers receive free delivery.",
]
queries = [
    "refund days",
    "Can I get my money back?",
    "How long until my parcel arrives?",
    "Do I pay for postage?",
]

document_vectors = embed(documents)
for query, query_vector in zip(queries, embed(queries)):
    print("QUERY:", query)
    score, best = retrieve(query, documents, k=1)[0]
    print(f"  word counts  {score:.2f}  "
          f"{best if score else '(no word in common)'}")
    score, best = max((cosine(query_vector, vector), document)
                      for vector, document in zip(document_vectors,
                                                  documents))
    print(f"  embeddings   {score:.2f}  {best}")
