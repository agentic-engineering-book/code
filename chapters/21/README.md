# Chapter 21: Agent-to-agent communication

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. The remote agent's work is done by a real model (two requests, a fraction of a cent), so your output may differ from the recorded run in [output/](output/). The protocol machinery is ordinary code. Set `BOOK_MODEL` to use another model.

- `37_agent_to_agent.py` - Experiment 37: Agent-to-agent communication. Agent card, server-assigned task IDs, `messageId` deduplication, caller rejection, artifacts, and schema validation; a drifted agent whose instructions lost the schema line. `python chapters/21/37_agent_to_agent.py`

Kernel modules used: `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [37: LangGraph remote-task lifecycle](../../framework_examples/37_agent_to_agent.py) - `python -m framework_examples.37_agent_to_agent`
