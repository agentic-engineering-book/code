"""Experiment 35: LangGraph debaters and a tool-grounded judge."""
import operator
from typing import Annotated, TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph

from agentic import calculator

QUESTION = "17 * 6"
calculate = tool(calculator)


class DebateState(TypedDict):
    candidates: Annotated[list, operator.add]
    rhetoric_choice: str
    grounded_choice: str


def agent_a(state):
    argument = ("Clearly and without any doubt the answer is 96; every "
                "careful reader will confirm this obvious result.")
    return {"candidates": [{"agent": "A", "answer": 96,
                            "argument": argument}]}


def agent_b(state):
    return {"candidates": [{"agent": "B", "answer": 102,
                            "argument": "102."}]}


def judge(state):
    candidates = sorted(state["candidates"], key=lambda c: c["agent"])
    # Unverified stand-in: the most elaborate argument wins.
    rhetoric = max(candidates, key=lambda c: len(c["argument"]))
    # Grounded: check every claim with the calculator tool.
    truth = calculate.invoke({"expression": QUESTION})
    verified = [c["agent"] for c in candidates if c["answer"] == truth]
    return {"rhetoric_choice": rhetoric["agent"],
            "grounded_choice": verified[0] if verified else "none verified"}


def run():
    builder = StateGraph(DebateState)
    builder.add_node("agent_a", agent_a)
    builder.add_node("agent_b", agent_b)
    builder.add_node("judge", judge)
    builder.add_edge(START, "agent_a")
    builder.add_edge(START, "agent_b")
    builder.add_edge(["agent_a", "agent_b"], "judge")
    builder.add_edge("judge", END)
    state = builder.compile().invoke({"candidates": []})
    return {"rhetoric_judge": state["rhetoric_choice"],
            "grounded_judge": state["grounded_choice"]}


if __name__ == "__main__":
    print(run())
