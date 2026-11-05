# Chapter 17: Agent as tool

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. The experiment calls a real model (about fifteen requests, a fraction of a cent), so your output will differ from the recorded run in [output/](output/). Set `BOOK_MODEL` to use another model.

- `31_agent_as_tool.py` - Experiment 31: Agent as tool. A parent agent with `researcher` and `calculator` tools; the researcher is a child agent with its own model, search tool and step budget. Three sources: the value, nothing, and a chain of reports. `python chapters/17/31_agent_as_tool.py`

Kernel modules used: `agentic/agent.py`, `agentic/tools.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [31: bounded LangGraph child agent exposed as a tool](../../framework_examples/31_agent_as_tool.py) - `python -m framework_examples.31_agent_as_tool`
