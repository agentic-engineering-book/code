# Chapter 27: Budgets and the autonomy envelope

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (about fifteen requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Costs and risk scores are abstract units.

- `51_resource_budgets.py` - Experiment 51: Resource budgets. A real research agent that never finds its primary source, without a budget and under a cost and a step budget checked before each search. `python chapters/27/51_resource_budgets.py`
- `52_autonomy_envelope.py` - Experiment 52: Risk budget and autonomy envelope. A real model writes the plan; independent checks versus an envelope with a cumulative risk budget. `python chapters/27/52_autonomy_envelope.py`

Kernel modules used: `agentic/control.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See
[setup and boundaries](../../framework_examples/README.md).

- [51: LangGraph budget check as an edge before each action](../../framework_examples/51_resource_budgets.py) - `python -m framework_examples.51_resource_budgets`
- [52: LangGraph autonomy envelope with a cumulative risk budget](../../framework_examples/52_autonomy_envelope.py) - `python -m framework_examples.52_autonomy_envelope`
