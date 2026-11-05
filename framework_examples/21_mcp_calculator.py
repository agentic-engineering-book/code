"""Experiment 21: MCP-shaped tool in LangChain. See README."""
import json
import textwrap

from langchain_core.tools import StructuredTool, ToolException

from agentic import calculator
from framework_examples.support import chat

# A simulated server, in process: no MCP SDK, transport or initialization.
TOOLS = [{
    "name": "calculator",
    "description": "Evaluate basic arithmetic such as 18*7.",
    "inputSchema": {"type": "object",
                    "properties": {"expression": {"type": "string"}},
                    "required": ["expression"]},
}]


def handle(request):
    """Server side: one JSON-RPC 2.0 request in, one response out."""
    method, params = request["method"], request.get("params", {})
    if method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call" and params["name"] == "calculator":
        try:
            text = str(calculator(**params["arguments"]))
            result = {"content": [{"type": "text", "text": text}],
                      "isError": False}
        except (ValueError, SyntaxError):
            text = "invalid arithmetic expression"
            result = {"content": [{"type": "text", "text": text}],
                      "isError": True}
    else:
        return {"jsonrpc": "2.0", "id": request["id"], "error": {
            "code": -32602, "message": f"Unknown tool: {params['name']}"}}
    return {"jsonrpc": "2.0", "id": request["id"], "result": result}


def send(method, params=None):
    """Client side: the message text a real transport would carry."""
    wire = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method,
                       "params": params or {}})
    return handle(json.loads(wire))


def to_langchain(listed):
    """Roughly what an MCP adapter does: schema in, LangChain tool out."""
    def call(**arguments):
        result = send("tools/call", {"name": listed["name"],
                                     "arguments": arguments})["result"]
        if result["isError"]:
            raise ToolException(result["content"][0]["text"])
        return result["content"][0]["text"]

    return StructuredTool.from_function(
        call, name=listed["name"], description=listed["description"],
        args_schema=listed["inputSchema"], handle_tool_error=True)


def run():
    tools = {t["name"]: to_langchain(t)
             for t in send("tools/list")["result"]["tools"]}
    lines = [f"TOOL: {name} | args: {sorted(tool.args)}"
             for name, tool in tools.items()]
    # The host turns the listed tools into the model's tool descriptions.
    model = chat().bind_tools(list(tools.values()))
    for task in ["What is 27611 times 2033?", "Delete invoice 7."]:
        lines.append("TASK: " + task)
        reply = model.invoke([("system", "Answer in at most two sentences."),
                              ("human", task)])
        if not reply.tool_calls:
            lines += textwrap.wrap(" ".join(reply.content.split()), 76,
                                   initial_indent="  MODEL ANSWERED: ",
                                   subsequent_indent="    ")
            continue
        call = reply.tool_calls[0]
        lines.append(f"  CALL: {call['name']} {json.dumps(call['args'])}")
        lines.append("    result: " + tools[call["name"]].invoke(
            call["args"]))
    lines.append("HAND-WRITTEN PROPOSALS")
    lines.append("  tool error: " + tools["calculator"].invoke(
        {"expression": "delete all invoices"}))
    error = send("tools/call", {"name": "delete_invoice",
                                "arguments": {"id": 7}})["error"]
    lines.append("  protocol error: " + error["message"])
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
