# Chapter 29: Computer use and multimodal agents

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (five requests in all, a fraction of a cent), so your output may differ from the recorded runs in [output/](output/). Experiment 56 needs Pillow and a vision-capable model.

- `55_computer_use.py` - Experiment 55: Computer use. A real model grounds "submit the form" on a toy screen whose layout shifts; stale coordinates versus re-grounding and a postcondition check. `python chapters/29/55_computer_use.py`
- `56_multimodal.py` - Experiment 56: Multimodal reasoning. A rendered label photo read by a real vision model, compared with an order record; a second photo has the quantity smudged. `python chapters/29/56_multimodal.py`

Kernel modules used: `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See
[setup and boundaries](../../framework_examples/README.md).

- [55: LangGraph approve -> re-ground -> act -> verify workflow](../../framework_examples/55_computer_use.py) - `python -m framework_examples.55_computer_use`
- [56: LangChain multimodal message, provenance-keeping fusion](../../framework_examples/56_multimodal.py) - `python -m framework_examples.56_multimodal`
