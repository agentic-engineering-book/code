"""Experiment 33 (Chapter 18): Hierarchy."""
REPORTS = {
    "R1": {"finding": "Option A is cheaper",
           "caveat": "source confidence is low"},
    "R2": {"finding": "Option B ships faster", "caveat": None},
    "B1": {"finding": "Option A needs a new API client", "caveat": None},
    "B2": {"finding": "Option B reuses the current stack", "caveat": None},
}
TEAMS = {"research_lead": ["R1", "R2"], "build_lead": ["B1", "B2"]}


def lossy_lead(reports):
    return {"findings": [r["finding"] for r in reports]}


def structured_lead(reports):
    return {"findings": [r["finding"] for r in reports],
            "caveats": [r["caveat"] for r in reports if r["caveat"]]}


def root_decides(summaries):
    caveats = [c for s in summaries for c in s.get("caveats", [])]
    if caveats:
        return "verify before choosing: " + "; ".join(caveats)
    return "choose Option A"


def flat():
    messages = 2 * len(REPORTS)  # root -> worker -> root
    summaries = [structured_lead([report]) for report in REPORTS.values()]
    return len(REPORTS), messages, root_decides(summaries)


def hierarchy(lead):
    messages, summaries = 0, []
    for workers in TEAMS.values():
        messages += 2 + 2 * len(workers)  # root <-> lead, lead <-> workers
        summaries.append(lead([REPORTS[w] for w in workers]))
    return len(TEAMS), messages, root_decides(summaries)


for label, (span, messages, decision) in [
    ("flat", flat()),
    ("hierarchy, lossy leads", hierarchy(lossy_lead)),
    ("hierarchy, structured leads", hierarchy(structured_lead)),
]:
    print(f"{label}: root span={span}, messages={messages}")
    print(f"  decision: {decision}")
