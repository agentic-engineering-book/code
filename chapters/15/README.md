# Chapter 15 experiments

Run from the repository root, for example:

    PYTHONPATH=. python chapters/15/27_routing.py

(On Windows PowerShell: `$env:PYTHONPATH='.'; python chapters/15/27_routing.py`.)

- `27_routing.py` - rule, always-write, and scripted semantic routers scored by accuracy and misroute cost
- `28_model_routing.py` - always-fast, always-strong, oracle, feature router, and cheap-first cascade compared on success and cost

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [27: Rule router as a LangGraph conditional edge](../../framework_examples/27_routing.py) - `python -m framework_examples.27_routing`
- [28: Cheap-first model cascade with LangChain fallbacks](../../framework_examples/28_model_routing.py) - `python -m framework_examples.28_model_routing`
