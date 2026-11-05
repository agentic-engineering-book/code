"""Experiment 22: ReAct loop in LangGraph. See framework_examples/README."""
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from agentic import calculator as safe_calculator
from framework_examples.support import chat

GOAL = "Find the current price of item A17, then add 15% VAT."


@tool
def lookup_price(item: str) -> int:
    """Look up the current price of an item."""
    return {"A17": 80}[item]


@tool
def calculator(expression: str) -> float:
    """Evaluate an arithmetic expression such as '80 * 1.15'."""
    return safe_calculator(expression)


def run():
    model = chat().bind_tools([lookup_price, calculator])
    builder = StateGraph(MessagesState)
    builder.add_node(
        "model", lambda s: {"messages": [model.invoke(s["messages"])]})
    builder.add_node("tools", ToolNode([lookup_price, calculator]))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition,
                                  {"tools": "tools", END: END})
    builder.add_edge("tools", "model")
    result = builder.compile().invoke(
        {"messages": [HumanMessage(content=GOAL)]}, {"recursion_limit": 10})
    steps = []
    for message in result["messages"][1:]:
        if isinstance(message, AIMessage) and message.tool_calls:
            call = message.tool_calls[0]
            steps.append(f"ACTION {call['name']}({call['args']})")
        elif isinstance(message, ToolMessage):
            steps.append(f"OBSERVATION {message.content}")
        else:
            steps.append("DONE " + " ".join(message.content.split())[:60])
    return steps


if __name__ == "__main__":
    for line in run():
        print(line)
