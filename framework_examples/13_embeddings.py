"""Experiment 13: LangChain embeddings interface and vector retrieval. See framework_examples/README.md."""
from langchain_core.embeddings import Embeddings
from langchain_core.vectorstores import InMemoryVectorStore


def run():
    class CharacterEmbeddings(Embeddings):
        def embed_documents(self, texts):
            return [[float(t.lower().count(c)) for c in 'agent'] for t in texts]
        def embed_query(self, text):
            return self.embed_documents([text])[0]
    store = InMemoryVectorStore(CharacterEmbeddings())
    store.add_texts(['agent memory', 'zzzz'])
    return store.similarity_search('memory for agents', k=1)[0].page_content


if __name__ == "__main__":
    print(run())
