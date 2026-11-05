# Chapter 23: Observability

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (about ten requests in all, a fraction of a cent), so your durations and tokens will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `41_tracing.py` - Experiment 41: Tracing. A real tool-using agent traced with a real clock; model spans carry tokens; the same spans printed with and without parent links. `python chapters/23/41_tracing.py`
- `42_cost_latency.py` - Experiment 42: Cost and latency. Three real calls of different length: inclusive versus exclusive tokens, and branch work versus wall-clock time in parallel. `python chapters/23/42_cost_latency.py`

Kernel modules used: `agentic/trace.py`, `agentic/tools.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [41: LangChain callbacks as parent-child spans](../../framework_examples/41_tracing.py) - `python -m framework_examples.41_tracing`
- [42: LangChain parallel branches and critical path](../../framework_examples/42_cost_latency.py) - `python -m framework_examples.42_cost_latency`
