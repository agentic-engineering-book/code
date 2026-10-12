"""Experiment 30: LangGraph Send fan-out, reducer, and complete fan-in."""
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

FINDINGS = {
    "financial": "margin assumption unsupported",
    "risk": "dependency on one supplier",
    "operations": None,  # this branch times out
}


class State(TypedDict):
    reviewers: list
    results: Annotated[list, operator.add]  # reducer: branches append
    report: dict


def fan_out(state):
    # One Send per reviewer: the number of branches is decided at run time.
    return [Send("review", {"reviewer": r}) for r in state["reviewers"]]


def review(branch):
    finding = FINDINGS[branch["reviewer"]]
    if finding is None:
        return {"results": [(branch["reviewer"], "error", "timeout")]}
    return {"results": [(branch["reviewer"], "issue", finding)]}


def fan_in(state):
    results = sorted(state["results"])
    issues = {name: text for name, kind, text in results if kind == "issue"}
    missing = [name for name, kind, _ in results if kind == "error"]
    verdict = "incomplete" if missing else ("revise" if issues else "accept")
    return {"report": {"verdict": verdict, "issues": issues,
                       "missing": missing}}


def run():
    builder = StateGraph(State)
    builder.add_node("review", review)
    builder.add_node("fan_in", fan_in)
    builder.add_conditional_edges(START, fan_out, ["review"])
    builder.add_edge("review", "fan_in")  # barrier: waits for every Send
    builder.add_edge("fan_in", END)
    graph = builder.compile()
    state = graph.invoke({"reviewers": list(FINDINGS), "results": []})
    return state["report"]


if __name__ == "__main__":
    print(run())
