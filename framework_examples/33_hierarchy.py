"""Experiment 33: Hierarchy in LangGraph. See framework_examples/README."""
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from framework_examples.support import chat

REPORTS = {
    "research": [{"finding": "Option A is cheaper",
                  "caveat": "source confidence is low"},
                 {"finding": "Option B ships faster", "caveat": None}],
    "build": [{"finding": "Option A needs a new API client", "caveat": None},
              {"finding": "Option B reuses the current stack",
               "caveat": None}],
}
HEDGES = ("confidence", "uncertain", "unverified", "unreliable")


class LeadState(TypedDict, total=False):
    reports: Annotated[list, operator.add]
    summary: dict


class RootState(TypedDict, total=False):
    summaries: Annotated[list, operator.add]
    caveat_reached: bool


def text(report):
    caveat = f" Caveat: {report['caveat']}." if report["caveat"] else ""
    return report["finding"] + "." + caveat


def build_lead(team, words, structured):
    """A team-lead subgraph: workers report, a model lead summarizes."""
    builder = StateGraph(LeadState)
    workers = [f"worker_{i}" for i in range(len(REPORTS[team]))]
    for name, report in zip(workers, REPORTS[team]):
        builder.add_node(name, lambda s, r=report: {"reports": [r]})
        builder.add_edge(START, name)

    def summarize(state):
        reports = sorted(state["reports"], key=lambda r: r["finding"])
        reply = chat().invoke([
            ("system", "You are a team lead. Summarize your workers' "
             f"reports for the director in at most {words} words."),
            ("user", "\n".join(map(text, reports)))])
        summary = {"team": team, "summary": reply.content.strip()}
        if structured:  # code carries caveats in their own field
            summary["caveats"] = [r["caveat"] for r in reports if r["caveat"]]
        return {"summary": summary}

    builder.add_node("summarize", summarize)
    builder.add_edge(workers, "summarize")
    builder.add_edge("summarize", END)
    return builder.compile()


def root(state):
    seen = " ".join(s["summary"] + " ".join(s.get("caveats", []))
                    for s in state["summaries"]).lower()
    return {"caveat_reached": any(hedge in seen for hedge in HEDGES)}


def build_root(words, structured=False):
    builder = StateGraph(RootState)
    for team in REPORTS:
        lead = build_lead(team, words, structured)
        # The lead is a compiled subgraph with its own private state.
        builder.add_node(f"{team}_lead", lambda s, g=lead: {
            "summaries": [g.invoke({"reports": []})["summary"]]})
        builder.add_edge(START, f"{team}_lead")
    builder.add_node("root", root)
    builder.add_edge([f"{team}_lead" for team in REPORTS], "root")
    builder.add_edge("root", END)
    return builder.compile()


def run():
    flat = " ".join(text(r) for team in REPORTS.values() for r in team)
    lines = [f"flat: root span=4, caveat reaches root="
             f"{any(hedge in flat.lower() for hedge in HEDGES)}"]
    for label, words, structured in [("10-word leads", 10, False),
                                     ("6-word leads", 6, False),
                                     ("6-word leads", 6, False),
                                     ("6-word leads", 6, False),
                                     ("structured leads", 6, True)]:
        state = build_root(words, structured).invoke({"summaries": []})
        research = next(s for s in state["summaries"]
                        if s["team"] == "research")
        lines.append(f"hierarchy, {label}: root span=2, caveat reaches "
                     f"root={state['caveat_reached']}")
        lines.append("  research lead: " + research["summary"][:58])
        if structured:
            lines.append(f"  caveats field: {research['caveats']}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
