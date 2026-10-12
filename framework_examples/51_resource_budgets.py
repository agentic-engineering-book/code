"""Experiment 51: LangGraph budget check as an edge BEFORE each action."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

SEARCH_COST = 0.03
MAX_STEPS, MAX_COST = 5, 0.10


class State(TypedDict):
    steps: int
    cost: float
    evidence: list
    status: str


def admit(state):
    """Admission control: decide whether the next search may run."""
    if state["steps"] >= MAX_STEPS:
        return {"status": "BUDGET_EXHAUSTED:step_budget"}
    if state["cost"] + SEARCH_COST > MAX_COST + 1e-9:
        return {"status": "BUDGET_EXHAUSTED:cost_budget"}
    return {"status": "admitted"}


def search(state):
    found = f"secondary source {state['steps'] + 1}"
    return {"steps": state["steps"] + 1,
            "cost": round(state["cost"] + SEARCH_COST, 2),
            "evidence": state["evidence"] + [found]}


def run():
    builder = StateGraph(State)
    builder.add_node("admit", admit)
    builder.add_node("search", search)
    builder.add_edge(START, "admit")
    builder.add_conditional_edges(
        "admit", lambda s: "search" if s["status"] == "admitted" else END)
    builder.add_edge("search", "admit")
    graph = builder.compile()
    final = graph.invoke({"steps": 0, "cost": 0.0, "evidence": [],
                          "status": ""}, {"recursion_limit": 50})
    return {"status": final["status"], "steps": final["steps"],
            "cost": final["cost"], "kept": final["evidence"][-1:]}


if __name__ == "__main__":
    print(run())
