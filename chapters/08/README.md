# Chapter 8 experiments: Memory

Run from the repository root, for example:

    PYTHONPATH=. python chapters/08/16_working_memory.py

- `16_working_memory.py` - Working memory: accumulate vs replace task state
- `17_long_term_memory.py` - Episodic and semantic memory with a naive and a durable-only write policy
- `18_procedural_memory.py` - Procedural memory: none, good and bad stored procedures

Kernel module used: `agentic/memory.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [16: LangGraph state reducer and InMemorySaver](../../framework_examples/16_working_memory.py) - `python -m framework_examples.16_working_memory`
- [17: LangGraph InMemoryStore with typed search and a write policy](../../framework_examples/17_long_term_memory.py) - `python -m framework_examples.17_long_term_memory`
- [18: Procedure from InMemoryStore injected into a prompt](../../framework_examples/18_procedural_memory.py) - `python -m framework_examples.18_procedural_memory`
