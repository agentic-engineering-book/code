"""Experiment 39: Trajectory eval, LangGraph. See framework_examples/README."""
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from agentic import calculator as safe_calculator
from framework_examples.support import chat, MODEL, SMALL_MODEL

GOAL = "What does item A17 cost including 15% VAT, according to our catalog?"
AUTHORIZED_TOOLS = {"search", "retrieve", "calculator"}
RELEVANT_TOOLS = {"retrieve", "calculator"}
REFERENCE_PATH = ["retrieve", "calculator"]
MAX_STEPS = 6


@tool
def search(query: str) -> str:
    """Search the web."""
    return "Web result: item A17 listed at around 75-85 dollars by resellers."


@tool
def retrieve(key: str) -> str:
    """Retrieve a record from the company catalog by item code."""
    return "Catalog: item A17 costs 80 dollars." if "A17" in key else "none"


@tool
def weather(city: str) -> str:
    """Current weather for a city."""
    return "Sunny, 24 C."


@tool
def calculator(expression: str) -> float:
    """Evaluate an arithmetic expression such as '80 * 1.15'."""
    return safe_calculator(expression)


TOOLS = [search, retrieve, weather, calculator]


def run_agent(model_name):
    """A real LangGraph agent; returns (tools used, final answer)."""
    model = chat(model_name).bind_tools(TOOLS)
    builder = StateGraph(MessagesState)
    builder.add_node(
        "model", lambda s: {"messages": [model.invoke(s["messages"])]})
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition,
                                  {"tools": "tools", END: END})
    builder.add_edge("tools", "model")
    result = builder.compile().invoke(
        {"messages": [HumanMessage(content=GOAL)]},
        {"recursion_limit": 2 * MAX_STEPS + 1})
    used = [call["name"] for m in result["messages"]
            if isinstance(m, AIMessage) for call in m.tool_calls]
    return used, result["messages"][-1].content


def checks(used):
    return {"required_tool": "calculator" in used,
            "irrelevant": sum(t not in RELEVANT_TOOLS for t in used),
            "unauthorized": sum(t not in AUTHORIZED_TOOLS for t in used),
            "within_limit": len(used) <= MAX_STEPS}


def run():
    lines = []
    for name in [MODEL, SMALL_MODEL]:
        used, answer = run_agent(name)
        lines += [f"{name}: tools={used}",
                  f"    answer_correct={'92' in answer} "
                  f"reference_match={used == REFERENCE_PATH}",
                  "    " + " ".join(f"{k}={v}"
                                    for k, v in checks(used).items())]
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
