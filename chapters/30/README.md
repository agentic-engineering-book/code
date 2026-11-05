# Chapter 30: Self-improvement and learning

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. All three experiments call a real model (about sixty requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `57_self_improvement.py` - Experiment 57: Prompt self-improvement. A real model classifies tickets; a real model revises the prompt from development failures; validation selects, a held-out test decides promotion. `python chapters/30/57_self_improvement.py`
- `58_experience_learning.py` - Experiment 58: Experience learning. Naive versus validated lessons from six episodes; a real agent acts on each set in three new situations. `python chapters/30/58_experience_learning.py`
- `59_reward_optimization.py` - Experiment 59: Reward and reward hacking. A real model told a proxy reward, then a policy search against the proxy, the true objective, and the proxy plus a hard rule. `python chapters/30/59_reward_optimization.py`

Kernel modules used: `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See
[setup and boundaries](../../framework_examples/README.md).

- [57: LangChain prompt candidates chosen on held-out data](../../framework_examples/57_self_improvement.py) - `python -m framework_examples.57_self_improvement`
- [58: LangGraph store with validated, scoped lessons](../../framework_examples/58_experience_learning.py) - `python -m framework_examples.58_experience_learning`
- [59: LangChain policy search that exposes reward hacking](../../framework_examples/59_reward_optimization.py) - `python -m framework_examples.59_reward_optimization`
