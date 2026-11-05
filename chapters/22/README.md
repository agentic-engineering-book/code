# Chapter 22: Evaluation

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. All three experiments call real models (about thirty requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `38_evaluation.py` - Experiment 38: Task evaluation. A real model's answers scored by exact and numeric match. `python chapters/22/38_evaluation.py`
- `39_trajectory_eval.py` - Experiment 39: Trajectory evaluation. Two real agents' trajectories checked against invariants and one reference path. `python chapters/22/39_trajectory_eval.py`
- `40_llm_judge.py` - Experiment 40: LLM-as-judge. A real judge calibrated against trusted labels, and a swap test. `python chapters/22/40_llm_judge.py`

Kernel modules used: `agentic/eval.py`, `agentic/tools.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [38: LangChain batch evaluation](../../framework_examples/38_evaluation.py) - `python -m framework_examples.38_evaluation`
- [39: LangGraph trajectory invariants](../../framework_examples/39_trajectory_eval.py) - `python -m framework_examples.39_trajectory_eval`
- [40: LangChain pairwise judge swap test](../../framework_examples/40_llm_judge.py) - `python -m framework_examples.40_llm_judge`
