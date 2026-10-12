"""Experiment 37: LangGraph remote-task lifecycle with authorization."""
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class Task(TypedDict, total=False):
    caller: str
    states: Annotated[list, operator.add]
    artifact: dict


ALLOWED_CALLERS = {"coordinator"}


def authorize(task):
    if task["caller"] in ALLOWED_CALLERS:
        return {"states": ["working"]}
    return {"states": ["rejected"]}


def research(task):
    data = {"price": 80, "currency": "USD"}
    return {"states": ["completed"],
            "artifact": {"name": "comparison",
                         "parts": [{"kind": "data", "data": data}]}}


def run():
    builder = StateGraph(Task)
    builder.add_node("authorize", authorize)
    builder.add_node("research", research)
    builder.add_edge(START, "authorize")
    builder.add_conditional_edges(
        "authorize",
        lambda task: END if task["states"][-1] == "rejected" else "research")
    builder.add_edge("research", END)
    graph = builder.compile()
    results = {}
    for caller in ["coordinator", "intruder"]:
        final = graph.invoke({"caller": caller, "states": ["submitted"]})
        results[caller] = final["states"]
    return results


if __name__ == "__main__":
    print(run())
