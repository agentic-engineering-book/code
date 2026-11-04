# Chapter 12: Planning

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (about fifteen requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `23_planning.py` - Experiment 23: Planning. The model writes JSON plans for a euro total and a dollar total; each plan is validated and executed. `python chapters/12/23_planning.py`
- `24_plan_execute.py` - Experiment 24: Plan, execute, replan. Reactive, plan-first and plan-plus-replan controllers meet a blocked route. `python chapters/12/24_plan_execute.py`

Kernel modules used: `agentic/tools.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [23: Planner, validator, and executor as LangChain runnables](../../framework_examples/23_planning.py) - `python -m framework_examples.23_planning`
- [24: Plan, execute, and replan as a LangGraph cycle](../../framework_examples/24_plan_execute.py) - `python -m framework_examples.24_plan_execute`
