"""Experiment 9: LangGraph named-tool dispatch."""
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from agentic.tools import calculator as evaluate


@tool
def calculator(expression: str) -> float:
    """Evaluate a basic arithmetic expression."""
    return evaluate(expression)


@tool
def weather(city: str) -> dict:
    """Get the current weather in a city."""
    return {"city": city, "temperature_c": 24}


@tool
def search(topic: str) -> str:
    """Find information about a topic."""
    return f"3 fixture documents about {topic}"


def dispatch(name, args):
    """Run one proposed call through a ToolNode with three tools."""
    builder = StateGraph(MessagesState)
    builder.add_node("tools", ToolNode([calculator, weather, search]))
    builder.add_edge(START, "tools")
    builder.add_edge("tools", END)
    proposal = AIMessage(content="", tool_calls=[
        {"name": name, "args": args, "id": "call-1"}])
    message = builder.compile().invoke({"messages": [proposal]})
    return message["messages"][-1].status


def run():
    # A correct name runs; a plausible but unregistered name is refused
    # as an error observation instead of executing anything.
    return {"weather": dispatch("weather", {"city": "Pretoria"}),
            "forecast": dispatch("forecast", {"city": "Pretoria"})}


if __name__ == "__main__":
    print(run())
