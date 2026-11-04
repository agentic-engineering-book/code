# Chapter 09: Context Compression

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (about thirty requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `19_context_compression.py` - Experiment 19: Compress working context. Full transcript, a six-message window and a model summary; does the agent still ask for approval? `python chapters/09/19_context_compression.py`
- `20_memory_consolidation.py` - Experiment 20: Memory consolidation. Plain, guarded and code-checked consolidators on consistent, conflicting and single-episode evidence. `python chapters/09/20_memory_consolidation.py`

Kernel module used: `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [19: LangChain compressor runnable](../../framework_examples/19_context_compression.py) - `python -m framework_examples.19_context_compression`
- [20: LangGraph count-then-consolidate sequence](../../framework_examples/20_memory_consolidation.py) - `python -m framework_examples.20_memory_consolidation`
