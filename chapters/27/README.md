# Chapter 27 experiments: Budgets and Stopping

Run from the repository root with `PYTHONPATH=.` (or after `pip install -e .`).
Both experiments use `agentic/control.py` (`Budget`).

- `51_resource_budgets.py` - an evidence loop that never finds enough runs
  100 searches when unbounded; with a budget checked before each search it
  stops with `BUDGET_EXHAUSTED` and an explicit reason.
- `52_autonomy_envelope.py` - each action passes an independent risk check,
  but a cumulative risk budget escalates `delete_record`; the envelope
  contracts when sensitive data is detected.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See
[setup and boundaries](../../framework_examples/README.md).

- [51: LangGraph budget check as an edge before each action](../../framework_examples/51_resource_budgets.py) - `python -m framework_examples.51_resource_budgets`
- [52: LangGraph autonomy envelope with a cumulative risk budget](../../framework_examples/52_autonomy_envelope.py) - `python -m framework_examples.52_autonomy_envelope`
