# Chapter 01: From an LLM to an Agent

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (a fraction of a cent per run), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `01_llm_call.py` - Experiment 1: One real model call. `python chapters/01/01_llm_call.py`
- `02_llm_to_agent.py` - Experiment 2: The model asks for the calculator; the program runs it. `python chapters/01/02_llm_to_agent.py`

## Framework companions

Install `requirements-frameworks.txt` from the repository root (Python 3.12+). See [setup and boundaries](../../framework_examples/README.md).

- [01: A model call](../../framework_examples/01_llm_call.py) - `python -m framework_examples.01_llm_call`
- [02: From model to agent](../../framework_examples/02_llm_to_agent.py) - `python -m framework_examples.02_llm_to_agent`
