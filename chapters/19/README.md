# Chapter 19 experiments

Run from the repository root, for example:

```bash
PYTHONPATH=. python chapters/19/34_voting.py
```

- `34_voting.py` - Experiment 34: Voting - majority vote vs ground truth for independent and correlated errors, Oracle@N, explicit ties
- `35_debate_judge.py` - Experiment 35: Judge and debate - an unverified longest-argument judge vs a calculator-grounded judge

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [34: LangGraph parallel voters with an explicit vote policy](../../framework_examples/34_voting.py) - `python -m framework_examples.34_voting`
- [35: LangGraph debaters and a tool-grounded judge](../../framework_examples/35_debate_judge.py) - `python -m framework_examples.35_debate_judge`
