# Chapter 02: Structured Decisions

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (a fraction of a cent per run), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `03_structured_output.py` - Experiment 3: Structured output. `python chapters/02/03_structured_output.py`
- `04_validation.py` - Experiment 4: Reject an invalid decision. `python chapters/02/04_validation.py`

## Framework companions

Install `requirements-frameworks.txt` from the repository root (Python 3.12+). See [setup and boundaries](../../framework_examples/README.md).

- [03: Structured output](../../framework_examples/03_structured_output.py) - `python -m framework_examples.03_structured_output`
- [04: Reject an invalid decision](../../framework_examples/04_validation.py) - `python -m framework_examples.04_validation`
