# Chapter 30 experiments: Self-Improving Agents

Run from the repository root with `PYTHONPATH=.` (or after `pip install -e .`).
Standard library only.

- `57_self_improvement.py` - two revised classifier prompts both score 4/4
  on the development examples they were written from; validation exposes the
  overfit one, and the selected prompt is promoted only on held-out gain with
  no slice regression.
- `58_experience_learning.py` - naive learning turns every success into a
  global rule (including "Always retry immediately"); validated learning
  promotes only lessons with enough evidence and applies them within scope.
- `59_reward_optimization.py` - optimizing "+1 when the ticket is closed"
  selects closing tickets without solving them; the true objective or a hard
  constraint selects solving.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See
[setup and boundaries](../../framework_examples/README.md).

- [57: LangChain prompt candidates chosen on held-out data](../../framework_examples/57_self_improvement.py) - `python -m framework_examples.57_self_improvement`
- [58: LangGraph store with validated, scoped lessons](../../framework_examples/58_experience_learning.py) - `python -m framework_examples.58_experience_learning`
- [59: LangChain policy search that exposes reward hacking](../../framework_examples/59_reward_optimization.py) - `python -m framework_examples.59_reward_optimization`
