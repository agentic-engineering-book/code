# Chapter 10: Model Context Protocol (MCP)

Run from the repository root after `python -m pip install -e .`, with `OPENAI_API_KEY` set. The experiment calls a real model (two requests, a fraction of a cent), so your output will differ from the recorded run in [output/](output/). Set `BOOK_MODEL` to use another model.

- `21_mcp_calculator.py` - Experiment 21: A minimal MCP-shaped calculator. An in-process simulation of the MCP JSON-RPC messages (initialize, tools/list, tools/call; not the MCP SDK); a real model chooses from the listed tools, and two hand-written proposals exercise the error paths. `python chapters/10/21_mcp_calculator.py`

Kernel modules used: `agentic/tools.py`, `agentic/live.py`.

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [21: LangChain StructuredTool built from an MCP-shaped tools/list entry](../../framework_examples/21_mcp_calculator.py) - `python -m framework_examples.21_mcp_calculator`
