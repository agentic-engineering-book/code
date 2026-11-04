# Chapter 07: Retrieval and RAG

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. All three experiments call a real model or embedding model (about twenty requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` or `BOOK_EMBEDDING_MODEL` to use other models.

- `13_embeddings.py` - Experiment 13: Retrieval. Word counts vs embeddings for four questions. `python chapters/07/13_embeddings.py`
- `14_rag.py` - Experiment 14: The smallest RAG pipeline. The model answers from stale, conflicting and dated evidence. `python chapters/07/14_rag.py`
- `15_reranking.py` - Experiment 15: Reranking. The model rescores word-overlap candidates; with k=1 it cannot recover the missing one. `python chapters/07/15_reranking.py`

Kernel modules used: `agentic/context.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [13: LangChain Embeddings interface and InMemoryVectorStore](../../framework_examples/13_embeddings.py) - `python -m framework_examples.13_embeddings`
- [14: LangChain retriever, metadata selection, prompt and stand-in generator](../../framework_examples/14_rag.py) - `python -m framework_examples.14_rag`
- [15: LangChain reranking runnable](../../framework_examples/15_reranking.py) - `python -m framework_examples.15_reranking`
