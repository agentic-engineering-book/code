# Chapter 25 experiments

- `46_human_approval.py` - Experiment 46: approval as a state transition
  bound to a SHA-256 hash of the exact action, with expiry.
- `47_permissions.py` - Experiment 47: permission checks at the tool
  boundary, delegation that cannot exceed the parent, and revocation.

Run from the repository root, e.g. `PYTHONPATH=. python chapters/25/46_human_approval.py`

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [46: LangGraph interrupt bound to an action hash](../../framework_examples/46_human_approval.py) - `python -m framework_examples.46_human_approval`
- [47: LangGraph authorization gate](../../framework_examples/47_permissions.py) - `python -m framework_examples.47_permissions`
