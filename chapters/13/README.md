# Chapter 13: Reflection

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. The experiment calls a real model (twelve requests, a fraction of a cent), so your output will differ from the recorded run in [output/](output/). Set `BOOK_MODEL` to use another model.

- `25_reflection.py` - Experiment 25: Reflection. A careful and a hasty critic review a wrong and a correct draft; each proposal is applied always, or only when a calculator confirms it. `python chapters/13/25_reflection.py`

Kernel modules used: `agentic/tools.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [25: Reflection with a verification gate in LangGraph](../../framework_examples/25_reflection.py) - `python -m framework_examples.25_reflection`
