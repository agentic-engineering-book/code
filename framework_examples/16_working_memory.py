"""Experiment 16: Working memory as LangGraph state. See README."""
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from agentic import calculator as safe_calculator
from framework_examples.support import chat

GOAL = "Multiply 27611 by 2033, then add 6."
MAX_STEPS = 4


@tool
def calculator(expression: str) -> float:
    """Evaluate an arithmetic expression exactly."""
    return safe_calculator(expression)


def build(remember):
    model = chat().bind_tools([calculator])

    def think(state):
        # Working memory: the model sees the calls and results so far,
        # or, when dropped, only the goal.
        seen = state["messages"] if remember else state["messages"][:1]
        return {"messages": [model.invoke(seen)]}

    def after_tools(state):
        calls = sum(isinstance(m, ToolMessage) for m in state["messages"])
        return END if calls >= MAX_STEPS else "model"

    builder = StateGraph(MessagesState)
    builder.add_node("model", think)
    builder.add_node("tools", ToolNode([calculator]))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition,
                                  {"tools": "tools", END: END})
    builder.add_conditional_edges("tools", after_tools, ["model", END])
    return builder.compile()


def run():
    lines = []
    for label, remember in [("WORKING MEMORY KEPT", True),
                            ("WORKING MEMORY DROPPED", False)]:
        result = build(remember).invoke(
            {"messages": [HumanMessage(content=GOAL)]})
        lines.append(label)
        last = result["messages"][-1]
        calls = [m.tool_calls[0]["args"]["expression"]
                 for m in result["messages"] if getattr(m, "tool_calls", 0)]
        results = [m.content for m in result["messages"]
                   if isinstance(m, ToolMessage)]
        for step, (expression, value) in enumerate(zip(calls, results), 1):
            lines.append(f"  step {step}: calculator({expression}) = {value}")
        step = len(results)
        if isinstance(last, ToolMessage):
            lines.append(f"  STOPPED by the step limit after {step} calls")
        else:
            answer = " ".join(last.content.split())[:50]
            lines.append(f"  answered at step {step + 1}: {answer}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
