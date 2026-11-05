# Chapter 28: Coding agents

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. Both experiments call a real model (about ten requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Tests run in a child process with an empty environment and a timeout; this is not a sandbox.

- `53_coding_agent.py` - Experiment 53: The smallest coding agent. A real model lists, reads, patches and tests a one-bug repository; the passing test ends the loop. `python chapters/28/53_coding_agent.py`
- `54_iterative_repair.py` - Experiment 54: Iterative repair. A real model implements `parse_price` against tests it cannot see; failures are fed back and regressions flagged. `python chapters/28/54_iterative_repair.py`

Kernel modules used: `agentic/tools.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See
[setup and boundaries](../../framework_examples/README.md).

- [53: LangGraph inspect -> patch -> test loop on a temp repo](../../framework_examples/53_coding_agent.py) - `python -m framework_examples.53_coding_agent`
- [54: LangGraph repair loop fed by full-suite test failures](../../framework_examples/54_iterative_repair.py) - `python -m framework_examples.54_iterative_repair`
