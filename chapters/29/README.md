# Chapter 29 experiments: Computer-Use and Multimodal Agents

Run from the repository root with `PYTHONPATH=.` (or after `pip install -e .`).
Standard library only.

- `55_computer_use.py` - a toy screen whose layout shifts after observation:
  reusing the old coordinate presses Delete; re-observing and grounding by
  label just before acting presses Submit, and the postcondition is checked
  on a fresh observation.
- `56_multimodal.py` - compares a (simulated) perception of a package label
  with the order record. Naive fusion ships the wrong quantity; the
  provenance-preserving comparison escalates the conflict and asks for a
  re-capture when confidence is low or the field is occluded.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See
[setup and boundaries](../../framework_examples/README.md).

- [55: LangGraph approve -> re-ground -> act -> verify workflow](../../framework_examples/55_computer_use.py) - `python -m framework_examples.55_computer_use`
- [56: LangChain multimodal message, provenance-keeping fusion](../../framework_examples/56_multimodal.py) - `python -m framework_examples.56_multimodal`
