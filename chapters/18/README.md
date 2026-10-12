# Chapter 18 experiments

Run from the repository root, for example:

```bash
PYTHONPATH=. python chapters/18/32_supervisor_workers.py
```

- `32_supervisor_workers.py` - Experiment 32: Supervisor and workers - good vs bad decomposition, and a dependency-aware supervisor
- `33_hierarchy.py` - Experiment 33: Hierarchy - flat vs two-level team; lossy lead summaries drop a caveat, structured ones keep it

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [32: LangGraph supervisor routing with Command](../../framework_examples/32_supervisor_workers.py) - `python -m framework_examples.32_supervisor_workers`
- [33: LangGraph root over team-lead subgraphs](../../framework_examples/33_hierarchy.py) - `python -m framework_examples.33_hierarchy`
