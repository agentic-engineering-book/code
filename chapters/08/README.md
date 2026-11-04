# Chapter 08: Memory

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. All three experiments call a real model (about fifty requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `16_working_memory.py` - Experiment 16: Working memory. The agent loop with its tool results kept, then dropped. `python chapters/08/16_working_memory.py`
- `17_long_term_memory.py` - Experiment 17: Episodic and semantic memory. Naive, vague and explicit write policies, and what the assistant says a week later. `python chapters/08/17_long_term_memory.py`
- `18_procedural_memory.py` - Experiment 18: Procedural memory. Good, bad and stale procedures meet an assertion failure and a timeout. `python chapters/08/18_procedural_memory.py`

Kernel modules used: `agentic/memory.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [16: LangGraph state reducer and InMemorySaver](../../framework_examples/16_working_memory.py) - `python -m framework_examples.16_working_memory`
- [17: LangGraph InMemoryStore with typed search and a write policy](../../framework_examples/17_long_term_memory.py) - `python -m framework_examples.17_long_term_memory`
- [18: Procedure from InMemoryStore injected into a prompt](../../framework_examples/18_procedural_memory.py) - `python -m framework_examples.18_procedural_memory`
