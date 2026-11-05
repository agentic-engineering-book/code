# Chapter 26: Security

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. All three experiments call a real model (about twenty requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `48_prompt_injection.py` - Experiment 48: Prompt injection. A real model summarizes a page with an injected email instruction, without and with a task-scoped tool gate. `python chapters/26/48_prompt_injection.py`
- `49_memory_poisoning.py` - Experiment 49: Memory poisoning. A real memory writer reads a session with a poisoned web page, without and with a write policy; a real agent later sends a report. `python chapters/26/49_memory_poisoning.py`
- `50_sandboxing.py` - Experiment 50: Sandboxing. A real model writes three probes, run in a scrubbed child process with a timeout. `python chapters/26/50_sandboxing.py`

Kernel modules used: `agentic/tools.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See
[setup and boundaries](../../framework_examples/README.md).

- [48: LangChain tool calls behind a task-scoped authority gate](../../framework_examples/48_prompt_injection.py) - `python -m framework_examples.48_prompt_injection`
- [49: LangGraph store behind a memory write policy](../../framework_examples/49_memory_poisoning.py) - `python -m framework_examples.49_memory_poisoning`
- [50: LangChain tool running code in a limited child process](../../framework_examples/50_sandboxing.py) - `python -m framework_examples.50_sandboxing`
