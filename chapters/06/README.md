# Chapter 06: Context Engineering

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model, so your output will differ from the recorded runs in [output/](output/). Experiment 11 sends twelve requests of about 17,000 input tokens each (some 200,000 tokens in all); Experiment 12 sends ten small ones. Set `BOOK_MODEL` to use another model.

- `11_context_quantity.py` - Experiment 11: Context quantity. The same refund question with order 17 alone, among 999 other orders at three positions, and with its refund window missing. `python chapters/06/11_context_quantity.py`
- `12_context_selection.py` - Experiment 12: Context selection. The model answers from the top two facts under a good and a corrupted ranking. `python chapters/06/12_context_selection.py`

Kernel modules used: `agentic/context.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [11: LangChain prompt assembly for the same three contexts](../../framework_examples/11_context_quantity.py) - `python -m framework_examples.11_context_quantity`
- [12: LangChain select-to-budget stage](../../framework_examples/12_context_selection.py) - `python -m framework_examples.12_context_selection`
