# Chapter 03: The Agent Loop

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (Experiment 6 makes up to twenty requests, still a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `05_agent_loop.py` - Experiment 5: The smallest agent loop. `python chapters/03/05_agent_loop.py`
- `06_stopping.py` - Experiment 6: The agent that never finishes. `python chapters/03/06_stopping.py`

## Framework companions

Install `requirements-frameworks.txt` from the repository root (Python 3.12+). See [setup and boundaries](../../framework_examples/README.md).

- [05: The smallest agent loop](../../framework_examples/05_agent_loop.py) - `python -m framework_examples.05_agent_loop`
- [06: The agent that never finishes](../../framework_examples/06_stopping.py) - `python -m framework_examples.06_stopping`
