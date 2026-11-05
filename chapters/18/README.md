# Chapter 18: Supervisors and hierarchy

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (about twenty requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `32_supervisor_workers.py` - Experiment 32: Supervisor and workers. A model supervisor's plan and a hand-written bad plan, run naively and with a dependency-aware supervisor; the analyst and writer are real models. `python chapters/18/32_supervisor_workers.py`
- `33_hierarchy.py` - Experiment 33: Hierarchy. Flat team versus two-level hierarchy; model leads with a 10-word and a 6-word limit, and a structured caveats field. `python chapters/18/33_hierarchy.py`

Kernel modules used: `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [32: LangGraph supervisor routing with Command](../../framework_examples/32_supervisor_workers.py) - `python -m framework_examples.32_supervisor_workers`
- [33: LangGraph root over team-lead subgraphs](../../framework_examples/33_hierarchy.py) - `python -m framework_examples.33_hierarchy`
