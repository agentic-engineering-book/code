# Chapter 25: Human-in-the-loop

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. In both experiments a real model proposes the action (one request each, a fraction of a cent); approval and permissions are ordinary code. Your output may differ from the recorded runs in [output/](output/).

- `46_human_approval.py` - Experiment 46: Human approval. A real agent proposes `send_email`; approval bound to a hash of the exact action, with expiry and a hand-applied change of recipient. `python chapters/25/46_human_approval.py`
- `47_permissions.py` - Experiment 47: Permissions. A real agent chooses between drafting and sending; the capability enforces `email:send`; delegation and revocation. `python chapters/25/47_permissions.py`

Kernel modules used: `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [46: LangGraph interrupt bound to an action hash](../../framework_examples/46_human_approval.py) - `python -m framework_examples.46_human_approval`
- [47: LangGraph authorization gate](../../framework_examples/47_permissions.py) - `python -m framework_examples.47_permissions`
