# Chapter 20: Blackboard

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. The workers that publish facts are real models (five requests, a fraction of a cent), so your output may differ from the recorded run in [output/](output/). The board itself is ordinary code. Set `BOOK_MODEL` to use another model.

- `36_blackboard.py` - Experiment 36: Blackboard. Model workers extract facts from their sources; the board keeps claims with provenance, resolves conflicts by authority, claims tasks atomically and rejects a stale write. `python chapters/20/36_blackboard.py`

Kernel modules used: `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [36: reducer-backed LangGraph blackboard with provenance](../../framework_examples/36_blackboard.py) - `python -m framework_examples.36_blackboard`
