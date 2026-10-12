# Chapter 7 experiments: Retrieval and RAG

Run from the repository root, for example:

    PYTHONPATH=. python chapters/07/13_embeddings.py

- `13_embeddings.py` - Bag-of-words retrieval with cosine similarity
- `14_rag.py` - Smallest RAG pipeline: naive vs metadata selection before generation
- `15_reranking.py` - Reranking, and the zero-recall boundary

Kernel module used: `agentic/context.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [13: LangChain Embeddings interface and InMemoryVectorStore](../../framework_examples/13_embeddings.py) - `python -m framework_examples.13_embeddings`
- [14: LangChain retriever, metadata selection, prompt and stand-in generator](../../framework_examples/14_rag.py) - `python -m framework_examples.14_rag`
- [15: LangChain reranking runnable](../../framework_examples/15_reranking.py) - `python -m framework_examples.15_reranking`
