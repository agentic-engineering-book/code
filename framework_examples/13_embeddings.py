"""Experiment 13: Word counts vs embeddings in LangChain. See README."""
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings

from agentic.context import retrieve

DOCUMENTS = ["Shipping usually takes 3 to 5 days.",
             "Refunds are accepted within 30 days.",
             "Gold customers receive free delivery."]
QUERIES = ["refund days", "Can I get my money back?",
           "How long until my parcel arrives?", "Do I pay for postage?"]


def run():
    store = InMemoryVectorStore(
        OpenAIEmbeddings(model="text-embedding-3-small"))
    store.add_texts(DOCUMENTS)
    lines = []
    for query in QUERIES:
        lines.append("QUERY: " + query)
        score, best = retrieve(query, DOCUMENTS, k=1)[0]
        lines.append(f"  word counts  {score:.2f}  "
                     f"{best if score else '(no word in common)'}")
        doc, score = store.similarity_search_with_score(query, k=1)[0]
        lines.append(f"  embeddings   {score:.2f}  {doc.page_content}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
