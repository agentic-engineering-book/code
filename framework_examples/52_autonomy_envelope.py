"""Experiment 52: LangGraph autonomy envelope with a cumulative risk."""
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

RISK = {"search": 0, "draft": 1, "send_email": 3, "delete_record": 8}
PERMITTED = {"search", "draft", "send_email", "delete_record"}
PLAN = ["search", "draft", "send_email", "send_email", "send_email",
        "delete_record"]


class State(TypedDict):
    position: int
    risk_remaining: int
    executed: list
    outcome: str


def gate(state):
    if state["position"] == len(PLAN):
        return {"outcome": "completed"}
    action = PLAN[state["position"]]
    if action not in PERMITTED:
        return {"outcome": f"denied:{action}"}
    if RISK[action] > state["risk_remaining"]:
        return {"outcome": f"escalate:{action}"}
    return {"outcome": "execute"}


def act(state):
    action = PLAN[state["position"]]
    return {"position": state["position"] + 1,
            "risk_remaining": state["risk_remaining"] - RISK[action],
            "executed": state["executed"] + [action]}


def run():
    builder = StateGraph(State)
    builder.add_node("gate", gate)
    builder.add_node("act", act)
    builder.add_edge(START, "gate")
    builder.add_conditional_edges(
        "gate", lambda s: "act" if s["outcome"] == "execute" else END)
    builder.add_edge("act", "gate")
    final = builder.compile().invoke({"position": 0, "risk_remaining": 10,
                                      "executed": [], "outcome": ""})
    independent = all(RISK[a] <= 8 for a in PLAN)
    return {"independent_checks_allow_all": independent,
            "executed": final["executed"],
            "risk_remaining": final["risk_remaining"],
            "outcome": final["outcome"]}


if __name__ == "__main__":
    print(run())
