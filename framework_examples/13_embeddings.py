"""Experiment 13: LangChain Embeddings interface, in-memory vector store."""
import re

from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore

DOCUMENTS = ["Shipping usually takes 3 to 5 days.",
             "Refunds are accepted within 30 days.",
             "Gold customers receive free delivery."]
VOCABULARY = ["refund", "day", "shipping", "gold", "delivery"]


class BagOfWordsEmbeddings(Embeddings):
    """Transparent stand-in for a learned embedding model."""

    def embed_query(self, text):
        words = [w[:-1] if len(w) > 3 and w.endswith("s") else w
                 for w in re.findall(r"[a-z0-9]+", text.lower())]
        return [float(words.count(term)) for term in VOCABULARY]

    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]


def run():
    store = InMemoryVectorStore(BagOfWordsEmbeddings())
    store.add_texts(DOCUMENTS)
    hits = store.similarity_search_with_score("refund days", k=3)
    return [[doc.page_content, round(score, 2)] for doc, score in hits]


if __name__ == "__main__":
    print(run())
