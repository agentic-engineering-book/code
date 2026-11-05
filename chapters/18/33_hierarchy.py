"""Experiment 33 (Chapter 18): Hierarchy."""
from agentic.live import OpenAIModel

REPORTS = {
    "R1": {"finding": "Option A is cheaper",
           "caveat": "source confidence is low"},
    "R2": {"finding": "Option B ships faster", "caveat": None},
    "B1": {"finding": "Option A needs a new API client", "caveat": None},
    "B2": {"finding": "Option B reuses the current stack", "caveat": None},
}
TEAMS = {"research_lead": ["R1", "R2"], "build_lead": ["B1", "B2"]}
HEDGES = ("confidence", "uncertain", "unverified", "unreliable")


def text(report):
    caveat = f" Caveat: {report['caveat']}." if report["caveat"] else ""
    return report["finding"] + "." + caveat


def model_lead(words):
    """A real model summarizes its workers' reports for the root."""
    def lead(reports):
        reply = OpenAIModel(system="You are a team lead. Summarize your "
                            "workers' reports for the director in at most "
                            f"{words} words.").generate(
            [{"role": "user", "content": "\n".join(map(text, reports))}])
        return {"summary": reply["answer"].strip()}
    return lead


def structured_lead(reports):
    """The summary may be lossy; code carries caveats in their own field."""
    summary = model_lead(6)(reports)
    summary["caveats"] = [r["caveat"] for r in reports if r["caveat"]]
    return summary


def reaches_root(summaries):
    seen = " ".join(s["summary"] + " ".join(s.get("caveats", []))
                    for s in summaries).lower()
    return any(hedge in seen for hedge in HEDGES)


def flat():
    messages = 2 * len(REPORTS)  # root -> worker -> root
    summaries = [{"summary": text(r)} for r in REPORTS.values()]
    return len(REPORTS), messages, summaries


def hierarchy(lead):
    messages, summaries = 0, []
    for workers in TEAMS.values():
        messages += 2 + 2 * len(workers)  # root <-> lead, lead <-> workers
        summaries.append(lead([REPORTS[w] for w in workers]))
    return len(TEAMS), messages, summaries


for label, lead in [("flat", None),
                    ("hierarchy, 10-word leads", model_lead(10)),
                    ("hierarchy, 6-word leads", model_lead(6)),
                    ("hierarchy, 6-word leads", model_lead(6)),
                    ("hierarchy, 6-word leads", model_lead(6)),
                    ("hierarchy, structured leads", structured_lead)]:
    span, messages, summaries = flat() if lead is None else hierarchy(lead)
    print(f"{label}: root span={span}, messages={messages}, "
          f"caveat reaches root={reaches_root(summaries)}")
    if lead is not None:
        print("  research lead:", summaries[0]["summary"])
    if lead is structured_lead:
        print("  caveats field:", summaries[0]["caveats"])
