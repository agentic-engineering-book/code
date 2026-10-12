"""Experiment 32: a LangGraph supervisor that routes workers with Command."""
import operator
from typing import Annotated, Literal, Optional, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

EVIDENCE = ["A: price 80, rating 4.1", "B: price 95, rating 4.6"]


class TeamState(TypedDict):
    evidence: list
    findings: list
    draft: Optional[str]
    log: Annotated[list, operator.add]


Next = Literal["researcher", "analyst", "writer", "__end__"]


def supervisor(state) -> Command[Next]:
    # Dependencies live in the routing rule: each worker needs its inputs.
    if not state["evidence"]:
        goto = "researcher"
    elif not state["findings"]:
        goto = "analyst"
    elif state["draft"] is None:
        goto = "writer"
    else:
        goto = END
    label = "done" if goto == END else goto
    return Command(goto=goto, update={"log": [f"supervisor -> {label}"]})


def researcher(state):
    return {"evidence": EVIDENCE, "log": ["researcher"]}


def analyst(state):
    return {"findings": ["A is cheaper", "B is rated higher"],
            "log": ["analyst"]}


def writer(state):
    draft = "Comparison: " + "; ".join(state["findings"]) + "."
    return {"draft": draft, "log": ["writer"]}


def run():
    builder = StateGraph(TeamState)
    builder.add_node("supervisor", supervisor)
    for name, worker in [("researcher", researcher), ("analyst", analyst),
                         ("writer", writer)]:
        builder.add_node(name, worker)
        builder.add_edge(name, "supervisor")  # workers report back
    builder.add_edge(START, "supervisor")
    graph = builder.compile()
    start = {"evidence": [], "findings": [], "draft": None, "log": []}
    state = graph.invoke(start, {"recursion_limit": 10})
    return {"draft": state["draft"], "log": state["log"]}


if __name__ == "__main__":
    print(run())
