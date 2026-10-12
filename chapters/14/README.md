# Chapter 14 experiments

Run from the repository root, for example:

    PYTHONPATH=. python chapters/14/26_tree_reasoning.py

(On Windows PowerShell: `$env:PYTHONPATH='.'; python chapters/14/26_tree_reasoning.py`.)

- `26_tree_reasoning.py` - beam search on the 2 -> 13 puzzle with widths 1-3, greedy closeness versus look-ahead scoring

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [26: Beam search as a bounded LangGraph loop](../../framework_examples/26_tree_reasoning.py) - `python -m framework_examples.26_tree_reasoning`
