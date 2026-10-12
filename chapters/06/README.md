# Chapter 6 experiments: Context Engineering

Run from the repository root, for example:

    PYTHONPATH=. python chapters/06/11_context_quantity.py

- `11_context_quantity.py` - Context quantity: coverage, size and distractors for three refund contexts
- `12_context_selection.py` - Context selection: top-2 selection under a good and a corrupted ranking

Kernel module used: `agentic/context.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [11: LangChain prompt assembly for the same three contexts](../../framework_examples/11_context_quantity.py) - `python -m framework_examples.11_context_quantity`
- [12: LangChain select-to-budget stage](../../framework_examples/12_context_selection.py) - `python -m framework_examples.12_context_selection`
