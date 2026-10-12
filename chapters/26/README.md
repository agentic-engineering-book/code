# Chapter 26 experiments: Security

Run from the repository root with `PYTHONPATH=.` (or after `pip install -e .`).

- `48_prompt_injection.py` - a scripted model obeys an injected web page and
  proposes `send_email`; without a gate it runs, with a task-scoped tool
  allowlist it is blocked and the summary still runs.
- `49_memory_poisoning.py` - "store everything" persists an injected
  preference that redirects a later report; a write policy that requires an
  authenticated writer for preferences rejects it.
- `50_sandboxing.py` - runs untrusted snippets in a child process with an
  empty environment, a temp directory and a timeout. It contains the secret
  and the runaway loop but NOT filesystem access: it is not a sandbox.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See
[setup and boundaries](../../framework_examples/README.md).

- [48: LangChain tool calls behind a task-scoped authority gate](../../framework_examples/48_prompt_injection.py) - `python -m framework_examples.48_prompt_injection`
- [49: LangGraph store behind a memory write policy](../../framework_examples/49_memory_poisoning.py) - `python -m framework_examples.49_memory_poisoning`
- [50: LangChain tool running code in a limited child process](../../framework_examples/50_sandboxing.py) - `python -m framework_examples.50_sandboxing`
