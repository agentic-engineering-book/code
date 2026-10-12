"""Experiment 25: Reflection with a verification gate in LangGraph."""
from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from agentic import calculator

TASK = "17 * 6"
CRITICS = {
    "good": lambda draft: None if draft == 102 else 102,
    "bad": lambda draft: 112,            # always invents a defect
}


class State(TypedDict, total=False):
    draft: int
    critic: str
    gated: bool
    proposed: int
    final: int


def critique(state):
    return {"proposed": CRITICS[state["critic"]](state["draft"])}


def route(state):
    if state["proposed"] is None:
        return "keep"
    if state["gated"] and calculator(TASK) != state["proposed"]:
        return "keep"                    # critique not verified
    return "revise"


def build():
    builder = StateGraph(State)
    builder.add_node("critique", critique)
    builder.add_node("revise", lambda s: {"final": s["proposed"]})
    builder.add_node("keep", lambda s: {"final": s["draft"]})
    builder.add_edge(START, "critique")
    builder.add_conditional_edges("critique", route, ["revise", "keep"])
    builder.add_edge("revise", END)
    builder.add_edge("keep", END)
    return builder.compile()


def run():
    graph, results = build(), {}
    for gated in (False, True):
        for critic, draft in (("good", 96), ("bad", 102)):
            final = graph.invoke(
                {"draft": draft, "critic": critic, "gated": gated})["final"]
            label = f"{'gated' if gated else 'ungated'} {critic} {draft}"
            results[label] = final
    return results


if __name__ == "__main__":
    print(run())
