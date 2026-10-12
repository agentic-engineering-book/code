# Chapter 12 experiments

Run from the repository root, for example:

    PYTHONPATH=. python chapters/12/23_planning.py

(On Windows PowerShell: `$env:PYTHONPATH='.'; python chapters/12/23_planning.py`.)

- `23_planning.py` - a dependency-explicit plan, validated against available tools, then executed
- `24_plan_execute.py` - reactive, fixed plan-first, and plan-plus-replan controllers on a blocked route

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [23: Planner, validator, and executor as LangChain runnables](../../framework_examples/23_planning.py) - `python -m framework_examples.23_planning`
- [24: Plan, execute, and replan as a LangGraph cycle](../../framework_examples/24_plan_execute.py) - `python -m framework_examples.24_plan_execute`
