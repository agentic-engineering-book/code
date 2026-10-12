# Chapter 21 experiments

- `37_agent_to_agent.py` - Experiment 37: agent-to-agent communication. An
  in-process stand-in for an A2A server: agent card discovery, server-assigned
  task IDs, messageId deduplication of retries, caller rejection, and artifact
  schema validation. No network or real authentication.

Run from the repository root: `PYTHONPATH=. python chapters/21/37_agent_to_agent.py`

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [37: LangGraph remote-task lifecycle](../../framework_examples/37_agent_to_agent.py) - `python -m framework_examples.37_agent_to_agent`
