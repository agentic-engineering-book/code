# Chapter 28 experiments: Coding Agents

Run from the repository root with `PYTHONPATH=.` (or after `pip install -e .`).
Both experiments create a throwaway repository in a temporary directory and
run its tests in a child process with an empty environment and a timeout.
That limits accidents; it is NOT a sandbox.

- `53_coding_agent.py` - a scripted model lists files, runs the failing test,
  reads `calculator.py`, applies a one-line patch and reruns the test; the
  passing test ends the loop. Paths outside the workspace are refused.
- `54_iterative_repair.py` - `divide(a, 0)` must return None. Test failures
  become the next observation; the second patch passes the targeted test but
  breaks normal division, which only the full suite catches.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See
[setup and boundaries](../../framework_examples/README.md).

- [53: LangGraph inspect -> patch -> test loop on a temp repo](../../framework_examples/53_coding_agent.py) - `python -m framework_examples.53_coding_agent`
- [54: LangGraph repair loop fed by full-suite test failures](../../framework_examples/54_iterative_repair.py) - `python -m framework_examples.54_iterative_repair`
