# Chapter 14: Tree reasoning

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. The experiment calls a real model (fourteen requests, a fraction of a cent), so your output will differ from the recorded run in [output/](output/). Set `BOOK_MODEL` to use another model.

- `26_tree_reasoning.py` - Experiment 26: Tree reasoning. The model answers the 2 -> 13 puzzle directly, then a one-level tree search prunes first moves with a model judge or an exact judge. `python chapters/14/26_tree_reasoning.py`

Kernel modules used: `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [26: Beam search as a bounded LangGraph loop](../../framework_examples/26_tree_reasoning.py) - `python -m framework_examples.26_tree_reasoning`
