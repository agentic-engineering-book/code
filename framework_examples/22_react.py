"""Experiment 22: ReAct loop in LangGraph. See framework_examples/README."""
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode, tools_condition

from agentic import calculator as safe_calculator

GOAL = "Find the current value of X, then calculate X * 1.15."


@tool
def lookup(key: str) -> int:
    """Return the current value stored under key."""
    return {"X": 80}[key]


@tool
def calculator(expression: str) -> float:
    """Evaluate an arithmetic expression such as '80 * 1.15'."""
    return safe_calculator(expression)


def scripted_policy(messages):
    """Deterministic stand-in: the next call depends on observations."""
    seen = [m.content for m in messages if isinstance(m, ToolMessage)]
    if not seen:
        call = {"name": "lookup", "args": {"key": "X"}, "id": "call-1"}
    elif len(seen) == 1:
        call = {"name": "calculator", "id": "call-2",
                "args": {"expression": f"{seen[0]} * 1.15"}}
    else:
        return AIMessage(content=f"X * 1.15 = {seen[-1]}")
    return AIMessage(content="", tool_calls=[call])


def run(live=False):
    if live:
        import os
        from langchain_openai import ChatOpenAI
        model = ChatOpenAI(model=os.environ["BOOK_MODEL"], timeout=30,
                           max_retries=1).bind_tools([lookup, calculator])
    else:
        model = RunnableLambda(scripted_policy)
    builder = StateGraph(MessagesState)
    builder.add_node(
        "model", lambda s: {"messages": [model.invoke(s["messages"])]})
    builder.add_node("tools", ToolNode([lookup, calculator]))
    builder.add_edge(START, "model")
    builder.add_conditional_edges("model", tools_condition,
                                  {"tools": "tools", END: END})
    builder.add_edge("tools", "model")
    graph = builder.compile()
    result = graph.invoke({"messages": [HumanMessage(content=GOAL)]},
                          {"recursion_limit": 10})
    steps = []
    for message in result["messages"][1:]:
        if isinstance(message, AIMessage) and message.tool_calls:
            call = message.tool_calls[0]
            steps.append(f"ACTION {call['name']}({call['args']})")
        elif isinstance(message, ToolMessage):
            steps.append(f"OBSERVATION {message.content}")
        else:
            steps.append(f"DONE {message.content}")
    return steps


if __name__ == "__main__":
    import sys
    print(run(live="--live" in sys.argv))
