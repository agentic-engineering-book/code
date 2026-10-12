# Chapter 16 experiments

Run from the repository root, for example:

```bash
PYTHONPATH=. python chapters/16/29_parallelism.py
```

- `29_parallelism.py` - Experiment 29: Parallel execution - asyncio sequential vs concurrent timing (simulated seconds) and a violated vs respected dependency
- `30_fanout_fanin.py` - Experiment 30: Fan-out/fan-in - three asyncio reviewers, a lossy vs complete fan-in, and partial failure via return_exceptions

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [29: LangChain parallel runnables, then a dependent sequence](../../framework_examples/29_parallelism.py) - `python -m framework_examples.29_parallelism`
- [30: LangGraph Send fan-out, reducer, and complete fan-in](../../framework_examples/30_fanout_fanin.py) - `python -m framework_examples.30_fanout_fanin`
