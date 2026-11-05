"""Experiment 32: Supervisor in LangGraph. See framework_examples/README."""
import textwrap
from typing import Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from framework_examples.support import chat

GOAL = "Produce a short evidence-based comparison of products A and B."
EVIDENCE = {"A": "price 80, rating 4.1", "B": "price 95, rating 4.6"}
NEEDS = {"researcher": "", "analyst": "evidence", "writer": "findings"}


class TeamState(TypedDict):
    pending: list
    respect: bool  # does the supervisor check each worker's inputs?
    order: list
    evidence: str
    findings: str
    draft: str


def ask(system, content):
    return chat().invoke([("system", system), ("user", content)]
                         ).content.strip()


def supervisor(state) -> Command[Literal["researcher", "analyst", "writer",
                                         "__end__"]]:
    pending = state["pending"]
    if state["respect"]:
        pending = [w for w in pending if not NEEDS[w] or state[NEEDS[w]]]
        if state["pending"] and not pending:
            return Command(goto=END, update={
                "draft": "blocked: no worker has its inputs"})
    if not pending:
        return Command(goto=END)
    worker = pending[0]
    return Command(goto=worker, update={
        "pending": [w for w in state["pending"] if w != worker],
        "order": state["order"] + [worker]})


def researcher(state):
    return {"evidence": "; ".join(f"{k}: {v}" for k, v in EVIDENCE.items())}


def analyst(state):
    return {"findings": ask(
        "You are the analyst on a team. List the key differences in at most "
        "15 words, using only the evidence.",
        "Evidence: " + (state["evidence"] or "(none yet)"))}


def writer(state):
    return {"draft": ask(
        "You are the writer on a team. Write the final comparison of "
        "products A and B in one sentence, using only the analyst's findings.",
        "Analyst's findings: " + (state["findings"] or "(none yet)"))}


def build():
    builder = StateGraph(TeamState)
    builder.add_node("supervisor", supervisor)
    for name, worker in [("researcher", researcher), ("analyst", analyst),
                         ("writer", writer)]:
        builder.add_node(name, worker)
        builder.add_edge(name, "supervisor")  # workers report back
    builder.add_edge(START, "supervisor")
    return builder.compile()


def run():
    reply = ask("You are a supervisor with three workers: researcher "
                "(gathers facts), analyst (compares facts), writer (writes "
                "the final text). Reply with the order in which to run "
                "them, as names separated by ' -> '.", "Goal: " + GOAL)
    model_plan = [name.strip().lower() for name in reply.split("->")]
    bad_plan = ["writer", "researcher", "analyst"]  # written by hand
    graph, lines = build(), []
    for label, plan, respect in [
            ("model supervisor's plan", model_plan, False),
            ("bad plan", bad_plan, False),
            ("bad plan, dependency-aware supervisor", bad_plan, True)]:
        state = graph.invoke({"pending": plan, "respect": respect,
                              "order": [], "evidence": "", "findings": "",
                              "draft": ""}, {"recursion_limit": 10})
        draft = state["draft"].replace("’", "'")
        lines += [f"{label}:", "  order: " + " -> ".join(state["order"])]
        lines += textwrap.wrap(draft, 76, initial_indent="  draft: ",
                               subsequent_indent="         ")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
