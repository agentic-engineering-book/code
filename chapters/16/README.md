# Chapter 16: Parallelism

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (about fifteen requests in all, a fraction of a cent), so your output and times will differ from the recorded runs in [output/](output/). Set `BOOK_MODEL` to use another model.

- `29_parallelism.py` - Experiment 29: Parallel execution. Three model calls made sequentially and concurrently (calls, tokens, wall-clock time), and an exchange-rate dependency run in parallel and in order. `python chapters/16/29_parallelism.py`
- `30_fanout_fanin.py` - Experiment 30: Fan-out/fan-in. Three model reviewers run concurrently; an over-summarizing fan-in versus a complete one, then one reviewer times out. `python chapters/16/30_fanout_fanin.py`

Kernel modules used: `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [29: LangChain parallel runnables, then a dependent sequence](../../framework_examples/29_parallelism.py) - `python -m framework_examples.29_parallelism`
- [30: LangGraph Send fan-out, reducer, and complete fan-in](../../framework_examples/30_fanout_fanin.py) - `python -m framework_examples.30_fanout_fanin`
