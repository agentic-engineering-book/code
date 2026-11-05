# Chapter 24: Reliability and recovery

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. All three experiments call real models (about twenty requests in all, a fraction of a cent), so your output will differ from the recorded runs in [output/](output/). Timeouts and crashes are injected; everything else is real.

- `43_retry_fallback.py` - Experiment 43: Retry, backoff, fallback. Injected timeouts before a real call, a real permanent error (unknown model), and a smaller real model as fallback. `python chapters/24/43_retry_fallback.py`
- `44_idempotency.py` - Experiment 44: Idempotency. A real payment agent sees a lost response and is asked to try again, without and with an idempotency key. `python chapters/24/44_idempotency.py`
- `45_checkpoint_resume.py` - Experiment 45: Checkpoint and resume. Each step is a real model call; resume after a crash, and restart on a stale checkpoint. `python chapters/24/45_checkpoint_resume.py`

Kernel modules used: `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [43: LangChain retry and fallback](../../framework_examples/43_retry_fallback.py) - `python -m framework_examples.43_retry_fallback`
- [44: LangGraph idempotency key](../../framework_examples/44_idempotency.py) - `python -m framework_examples.44_idempotency`
- [45: LangGraph checkpoint and resume after failure](../../framework_examples/45_checkpoint_resume.py) - `python -m framework_examples.45_checkpoint_resume`
