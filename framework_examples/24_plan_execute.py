"""Experiment 24: Plan, execute, and replan as a LangGraph cycle."""
import operator
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END

ROUTE_LENGTH = {"A": 3, "B": 5}
BLOCKED = {"A"}                  # true in the world, unknown to the planner


class State(TypedDict, total=False):
    plan: list
    position: str
    known_blocked: list
    replans: int
    log: Annotated[list, operator.add]


def plan(state):
    known = state.get("known_blocked", [])
    route = min((r for r in ROUTE_LENGTH if r not in known),
                key=ROUTE_LENGTH.get)
    return {"plan": [f"take {route}", "continue to D"],
            "replans": state.get("replans", -1) + 1}


def execute(state):
    step, rest = state["plan"][0], state["plan"][1:]
    if step.startswith("take"):
        route = step.split()[1]
        if route in BLOCKED:
            return {"known_blocked": state.get("known_blocked", []) + [route],
                    "log": [f"{step}: Route {route} blocked"]}
        return {"plan": rest, "position": route, "log": [f"{step}: ok"]}
    return {"plan": rest, "position": "D", "log": [f"{step}: arrived"]}


def after_execute(state):
    if state.get("position") == "D":
        return END
    blocked = state.get("known_blocked", [])
    if blocked and state["plan"][0] == f"take {blocked[-1]}":
        return "plan"                  # trigger: an assumption failed
    return "execute"


def run():
    builder = StateGraph(State)
    builder.add_node("plan", plan)
    builder.add_node("execute", execute)
    builder.add_edge(START, "plan")
    builder.add_edge("plan", "execute")
    builder.add_conditional_edges("execute", after_execute,
                                  ["plan", "execute", END])
    final = builder.compile().invoke({"position": "start"},
                                     {"recursion_limit": 12})
    return {"log": final["log"], "replans": final["replans"],
            "position": final["position"]}


if __name__ == "__main__":
    print(run())
