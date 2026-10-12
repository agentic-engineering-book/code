"""Experiment 21: LangChain tool built from an MCP-shaped tools/list entry."""
from langchain_core.tools import StructuredTool, ToolException

from agentic import calculator

# What a server's tools/list result would contain (simulated; no MCP SDK).
LISTED_TOOL = {
    "name": "calculator",
    "description": "Evaluate basic arithmetic such as 18*7.",
    "inputSchema": {"type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"]},
}


def tools_call(name, arguments):
    """Simulated tools/call: returns a CallToolResult-shaped dict."""
    try:
        text, is_error = str(calculator(**arguments)), False
    except (ValueError, SyntaxError):
        text, is_error = "invalid arithmetic expression", True
    return {"content": [{"type": "text", "text": text}], "isError": is_error}


def to_langchain(listed):
    """Roughly what an MCP adapter does: schema in, LangChain tool out."""
    def call(**arguments):
        result = tools_call(listed["name"], arguments)
        text = result["content"][0]["text"]
        if result["isError"]:
            raise ToolException(text)
        return text

    return StructuredTool.from_function(
        call, name=listed["name"], description=listed["description"],
        args_schema=listed["inputSchema"], handle_tool_error=True)


def run():
    tool = to_langchain(LISTED_TOOL)
    return {"name": tool.name,
            "args": sorted(tool.args),
            "ok": tool.invoke({"expression": "18*7"}),
            "tool_error": tool.invoke({"expression": "delete all invoices"})}


if __name__ == "__main__":
    print(run())
