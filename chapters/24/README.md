# Chapter 24 experiments

- `43_retry_fallback.py` - Experiment 43: bounded retry with seeded
  exponential backoff and jitter, no retry for permanent errors, fallback.
- `44_idempotency.py` - Experiment 44: a lost response after a payment;
  blind retry charges twice, an idempotency key charges once.
- `45_checkpoint_resume.py` - Experiment 45: a five-step task crashes at
  verify, resumes from a JSON checkpoint, and restarts when the checkpoint
  is stale.

Run from the repository root, e.g. `PYTHONPATH=. python chapters/24/43_retry_fallback.py`

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [43: LangChain retry and fallback](../../framework_examples/43_retry_fallback.py) - `python -m framework_examples.43_retry_fallback`
- [44: LangGraph idempotency key](../../framework_examples/44_idempotency.py) - `python -m framework_examples.44_idempotency`
- [45: LangGraph checkpoint and resume after failure](../../framework_examples/45_checkpoint_resume.py) - `python -m framework_examples.45_checkpoint_resume`
