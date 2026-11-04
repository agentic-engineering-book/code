"""Experiment 21 (Chapter 10): A minimal MCP-shaped calculator."""
import json
import textwrap

from agentic import calculator
from agentic.live import OpenAIModel

PROTOCOL_VERSION = "2025-06-18"
TOOLS = [{
    "name": "calculator",
    "description": "Evaluate basic arithmetic such as 18*7.",
    "inputSchema": {
        "type": "object",
        "properties": {"expression": {"type": "string"}},
        "required": ["expression"],
    },
}]
IMPLEMENTATIONS = {"calculator": calculator}


def handle(request):
    """Server side: one JSON-RPC 2.0 request in, one response out."""
    method, params = request["method"], request.get("params", {})
    if "id" not in request:
        return None  # a notification, such as notifications/initialized
    if method == "initialize":
        result = {"protocolVersion": PROTOCOL_VERSION,
                  "capabilities": {"tools": {"listChanged": False}},
                  "serverInfo": {"name": "calc-server", "version": "1.0"}}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call" and params["name"] in IMPLEMENTATIONS:
        try:
            value = IMPLEMENTATIONS[params["name"]](**params["arguments"])
            result = {"content": [{"type": "text", "text": str(value)}],
                      "isError": False}
        except (ValueError, SyntaxError):
            text = "invalid arithmetic expression"
            result = {"content": [{"type": "text", "text": text}],
                      "isError": True}
    elif method == "tools/call":
        return {"jsonrpc": "2.0", "id": request["id"], "error": {
            "code": -32602, "message": f"Unknown tool: {params['name']}"}}
    else:
        return {"jsonrpc": "2.0", "id": request["id"], "error": {
            "code": -32601, "message": f"Method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": request["id"], "result": result}


next_id = 0


def send(method, params=None, notification=False):
    """Client side: build the message a real transport would carry."""
    global next_id
    request = {"jsonrpc": "2.0", "method": method}
    if not notification:
        next_id += 1
        request["id"] = next_id
    if params is not None:
        request["params"] = params
    wire = json.dumps(request)  # stdio or HTTP would carry this text
    return handle(json.loads(wire))


reply = send("initialize", {
    "protocolVersion": PROTOCOL_VERSION, "capabilities": {},
    "clientInfo": {"name": "book-client", "version": "1.0"}})["result"]
print("SERVER:", reply["serverInfo"]["name"],
      "| version:", reply["protocolVersion"],
      "| capabilities:", sorted(reply["capabilities"]))
send("notifications/initialized", notification=True)

available = send("tools/list")["result"]["tools"]
for tool in available:
    print("TOOL:", tool["name"], "| requires:",
          tool["inputSchema"]["required"])



def call(proposal):
    response = send("tools/call", proposal)
    print("  CALL:", proposal["name"], json.dumps(proposal["arguments"]))
    if "error" in response:
        print("    protocol error:", json.dumps(response["error"]))
    else:
        print("    content:", json.dumps(response["result"]["content"]))
        print("    isError:", json.dumps(response["result"]["isError"]))


# The host turns the listed tools into the model's tool descriptions.
model = OpenAIModel(tools=[{"name": tool["name"],
                            "description": tool["description"],
                            "parameters": tool["inputSchema"]}
                           for tool in available],
                    system="Answer in at most two sentences.")
for task in ["What is 27611 times 2033?", "Delete invoice 7."]:
    print("TASK:", task)
    decision = model.generate([{"role": "user", "content": task}])
    if decision.get("done"):
        print(textwrap.fill(decision["answer"], 76,
                            initial_indent="  MODEL ANSWERED: ",
                            subsequent_indent="    "))
    else:
        call({"name": decision["action"],
              "arguments": decision["arguments"]})

print("HAND-WRITTEN PROPOSALS")
call({"name": "calculator",
      "arguments": {"expression": "delete all invoices"}})
call({"name": "delete_invoice", "arguments": {"id": 7}})
