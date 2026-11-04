# Chapter 11: ReAct

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. The experiment calls a real model (about eight requests, a fraction of a cent), so your output will differ from the recorded run in [output/](output/). Set `BOOK_MODEL` to use another model.

- `22_react.py` - Experiment 22: ReAct as feedback control. The same price-plus-VAT task without tools, in the ReAct loop, and with observations never fed back. `python chapters/11/22_react.py`

Kernel modules used: `agentic/tools.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [22: ReAct loop in LangGraph with lookup and calculator tools](../../framework_examples/22_react.py) - `python -m framework_examples.22_react`
