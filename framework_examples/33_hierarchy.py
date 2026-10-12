"""Experiment 33: a LangGraph root over team-lead subgraphs."""
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

REPORTS = {
    "research": [{"finding": "Option A is cheaper",
                  "caveat": "source confidence is low"},
                 {"finding": "Option B ships faster", "caveat": None}],
    "build": [{"finding": "Option A needs a new API client", "caveat": None},
              {"finding": "Option B reuses the current stack",
               "caveat": None}],
}


class LeadState(TypedDict):
    reports: Annotated[list, operator.add]
    summary: dict


class RootState(TypedDict):
    summaries: Annotated[list, operator.add]
    decision: str


def build_lead(team, keep_caveats):
    builder = StateGraph(LeadState)
    workers = [f"{team}_worker_{i}" for i in range(len(REPORTS[team]))]
    for name, report in zip(workers, REPORTS[team]):
        builder.add_node(name, lambda s, r=report: {"reports": [r]})
        builder.add_edge(START, name)

    def summarize(state):
        reports = sorted(state["reports"], key=lambda r: r["finding"])
        summary = {"team": team, "findings": [r["finding"] for r in reports]}
        if keep_caveats:
            summary["caveats"] = [r["caveat"] for r in reports if r["caveat"]]
        return {"summary": summary}

    builder.add_node("summarize", summarize)
    builder.add_edge(workers, "summarize")
    builder.add_edge("summarize", END)
    return builder.compile()


def decide(state):
    caveats = [c for s in state["summaries"] for c in s.get("caveats", [])]
    if caveats:
        return {"decision": "verify before choosing: " + "; ".join(caveats)}
    return {"decision": "choose Option A"}


def build_root(keep_caveats):
    builder = StateGraph(RootState)
    leads = []
    for team in REPORTS:
        lead = build_lead(team, keep_caveats)
        name = f"{team}_lead"
        # The lead is a compiled subgraph with its own private state schema.
        builder.add_node(name, lambda s, g=lead: {
            "summaries": [g.invoke({"reports": []})["summary"]]})
        builder.add_edge(START, name)
        leads.append(name)
    builder.add_node("root", decide)
    builder.add_edge(leads, "root")
    builder.add_edge("root", END)
    return builder.compile()


def run():
    return {"lossy_leads": build_root(False).invoke({})["decision"],
            "structured_leads": build_root(True).invoke({})["decision"]}


if __name__ == "__main__":
    print(run())
