# Chapter 15: Routing

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call real models (about forty requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model in Experiment 27.

- `27_routing.py` - Experiment 27: Task routing. A rule router and a model router with plain and sharper route descriptions, scored by accuracy and misroute cost. `python chapters/15/27_routing.py`
- `28_model_routing.py` - Experiment 28: Model routing. A small and a larger model under always-fast, always-strong, oracle, length-router and cheap-first-cascade strategies. `python chapters/15/28_model_routing.py`

Kernel modules used: `agentic/tools.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [27: Rule router as a LangGraph conditional edge](../../framework_examples/27_routing.py) - `python -m framework_examples.27_routing`
- [28: Cheap-first model cascade with LangChain fallbacks](../../framework_examples/28_model_routing.py) - `python -m framework_examples.28_model_routing`
