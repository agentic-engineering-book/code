# Chapter 23 experiments

- `41_tracing.py` - Experiment 41: hierarchical spans with trace, span and
  parent IDs and a manual clock (uses `agentic/trace.py`, `agentic/tools.py`).
- `42_cost_latency.py` - Experiment 42: span cost and latency breakdown,
  inclusive vs exclusive cost, total branch work vs critical path.

Run from the repository root, e.g. `PYTHONPATH=. python chapters/23/41_tracing.py`

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [41: LangChain callbacks as parent-child spans](../../framework_examples/41_tracing.py) - `python -m framework_examples.41_tracing`
- [42: LangChain parallel branches and critical path](../../framework_examples/42_cost_latency.py) - `python -m framework_examples.42_cost_latency`
