"""Experiment 14: LangChain retriever-to-prompt RAG composition. See framework_examples/README.md."""
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda


def run():
    class KeywordRetriever(BaseRetriever):
        documents: list[Document]
        def _get_relevant_documents(self, query, *, run_manager):
            return [d for d in self.documents if query.lower() in d.page_content.lower()]
    retriever = KeywordRetriever(documents=[Document(page_content=t) for t in
        ['Paris is in France.', 'Pretoria is in South Africa.']])
    context = retriever | RunnableLambda(lambda ds: {'evidence': ds[0].page_content})
    prompt = PromptTemplate.from_template('Answer using: {evidence}')
    return (context | prompt).invoke('Pretoria').to_string()


if __name__ == "__main__":
    print(run())
