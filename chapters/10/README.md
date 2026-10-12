# Chapter 10 experiments: Model Context Protocol (MCP)

Run from the repository root, for example:

    PYTHONPATH=. python chapters/10/21_mcp_calculator.py

- `21_mcp_calculator.py` - In-process simulation of MCP JSON-RPC messages: initialize, tools/list, tools/call (not the MCP SDK)

## Framework companions

Install `requirements-frameworks.txt` from the repository root. See [setup and boundaries](../../framework_examples/README.md).

- [21: LangChain StructuredTool built from an MCP-shaped tools/list entry](../../framework_examples/21_mcp_calculator.py) - `python -m framework_examples.21_mcp_calculator`
