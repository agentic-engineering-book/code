"""Experiment 10: LangGraph structured tool-error observations."""
import json

from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode


@tool
def weather(city: str) -> dict:
    """Get the current weather in a city."""
    raise TimeoutError("weather service unavailable")


def structured_error(error: Exception) -> str:
    """Keep the failure type, not just a message, for the next decision."""
    retryable = isinstance(error, TimeoutError)
    return json.dumps({"ok": False,
                       "error": "timeout" if retryable else "tool_failure",
                       "retryable": retryable, "message": str(error)})


def run():
    builder = StateGraph(MessagesState)
    builder.add_node("tools", ToolNode(
        [weather], handle_tool_errors=structured_error))
    builder.add_edge(START, "tools")
    builder.add_edge("tools", END)
    proposal = AIMessage(content="", tool_calls=[
        {"name": "weather", "args": {"city": "Pretoria"}, "id": "call-1"}])
    state = builder.compile().invoke({"messages": [proposal]})
    message = state["messages"][-1]
    return {"status": message.status,
            "observation": json.loads(message.content)}


if __name__ == "__main__":
    print(run())
