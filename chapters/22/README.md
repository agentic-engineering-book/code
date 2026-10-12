# Chapter 22 experiments

- `38_evaluation.py` - Experiment 38: task evaluation with exact and numeric
  match (uses `agentic/eval.py`).
- `39_trajectory_eval.py` - Experiment 39: trajectory invariants versus a
  single reference path.
- `40_llm_judge.py` - Experiment 40: calibrating a (deliberately biased)
  stand-in judge against trusted labels, plus an order-swap test.

Run from the repository root, e.g. `PYTHONPATH=. python chapters/22/38_evaluation.py`

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [38: LangChain batch evaluation](../../framework_examples/38_evaluation.py) - `python -m framework_examples.38_evaluation`
- [39: LangGraph trajectory invariants](../../framework_examples/39_trajectory_eval.py) - `python -m framework_examples.39_trajectory_eval`
- [40: LangChain pairwise judge swap test](../../framework_examples/40_llm_judge.py) - `python -m framework_examples.40_llm_judge`
