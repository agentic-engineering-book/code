# Chapter 9 experiments: Context Compression

Run from the repository root, for example:

    PYTHONPATH=. python chapters/09/19_context_compression.py

- `19_context_compression.py` - Field-keeping compressor, and a broken one that drops the approval constraint
- `20_memory_consolidation.py` - Blind vs guarded consolidation of consistent and conflicting episodes

Kernel module used: `agentic/context.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [19: LangChain compressor runnable](../../framework_examples/19_context_compression.py) - `python -m framework_examples.19_context_compression`
- [20: LangGraph count-then-consolidate sequence](../../framework_examples/20_memory_consolidation.py) - `python -m framework_examples.20_memory_consolidation`
