"""Experiment 16: LangGraph state as working memory, with a checkpointer."""
import operator
from typing import Annotated, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from agentic import calculator


class TaskState(TypedDict):
    goal: str
    observations: Annotated[list, operator.add]  # reducer: accumulate


def multiply(state):
    return {"observations": [{"expression": "12*7",
                              "result": calculator("12*7")}]}


def add(state):
    product = state["observations"][-1]["result"]
    expression = f"{product}+6"
    return {"observations": [{"expression": expression,
                              "result": calculator(expression)}]}


def run():
    builder = StateGraph(TaskState)
    builder.add_node("multiply", multiply)
    builder.add_node("add", add)
    builder.add_edge(START, "multiply")
    builder.add_edge("multiply", "add")
    builder.add_edge("add", END)
    app = builder.compile(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "refund-task"}}
    app.invoke({"goal": "Multiply 12 by 7, then add 6",
                "observations": []}, config)
    saved = app.get_state(config).values["observations"]
    return [[o["expression"], o["result"]] for o in saved]


if __name__ == "__main__":
    print(run())
