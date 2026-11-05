"""Experiment 30: Fan-out in LangGraph. See framework_examples/README."""
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from framework_examples.support import chat

PROPOSAL = ("Open a second warehouse in Q3. The budget assumes a 40% margin; "
            "this year's margin is 22%. All stock comes from one supplier. "
            "Signing a lease takes about four months.")
REVIEWERS = {"financial": "You review proposals for financial problems.",
             "risk": "You review proposals for business risks.",
             "operations": "You review proposals for operational "
                           "feasibility."}


class State(TypedDict, total=False):
    timeouts: dict
    results: Annotated[list, operator.add]  # reducer: branches append
    bad: str
    report: dict


def fan_out(state):
    # One Send per reviewer: the number of branches is decided at run time.
    return [Send("review", {"reviewer": name,
                            "timeout": state["timeouts"].get(name, 60)})
            for name in REVIEWERS]


def review(branch):
    name = branch["reviewer"]
    messages = [("system", REVIEWERS[name]),
                ("user", PROPOSAL + "\nName the single most important issue "
                 "in at most eight words.")]
    try:
        reply = chat().invoke(messages, timeout=branch["timeout"])
    except Exception as error:  # a failed branch becomes a result
        return {"results": [(name, "error", type(error).__name__)]}
    return {"results": [(name, "issue", reply.content.strip())]}


def fan_in(state):
    results = sorted(state["results"])
    issues = {name: text for name, kind, text in results if kind == "issue"}
    missing = [name for name, kind, _ in results if kind == "error"]
    verdict = "incomplete" if missing else ("revise" if issues else "accept")
    # Over-summarized fan-in: keeps only issues two reviewers agree on.
    agreed = [i for i in issues.values() if list(issues.values()).count(i) > 1]
    bad = "Proposal needs revision." if agreed else \
        "Proposal looks acceptable."
    return {"bad": bad, "report": {"verdict": verdict, "issues": issues,
                                   "missing": missing}}


def build():
    builder = StateGraph(State)
    builder.add_node("review", review)
    builder.add_node("fan_in", fan_in)
    builder.add_conditional_edges(START, fan_out, ["review"])
    builder.add_edge("review", "fan_in")  # barrier: waits for every Send
    builder.add_edge("fan_in", END)
    return builder.compile()


def show(label, report):
    lines = [f"{label}: {report['verdict']}, missing={report['missing']}"]
    for reviewer, issue in report["issues"].items():
        lines.append(f"  {reviewer}: {issue[:60]}".replace("\u2019", "'"))
    return lines


def run():
    graph = build()
    state = graph.invoke({"timeouts": {}, "results": []})
    lines = [f"bad fan-in: {state['bad']}"]
    lines += show("complete fan-in", state["report"])
    state = graph.invoke({"timeouts": {"operations": 0.01}, "results": []})
    return lines + show("partial failure", state["report"])


if __name__ == "__main__":
    for line in run():
        print(line)
