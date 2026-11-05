"""Experiment 30 (Chapter 16): Fan-out/fan-in."""
import asyncio

from agentic.live import OpenAIModel

PROPOSAL = ("Open a second warehouse in Q3. The budget assumes a 40% margin; "
            "this year's margin is 22%. All stock comes from one supplier. "
            "Signing a lease takes about four months.")
REVIEWERS = {"financial": "You review proposals for financial problems.",
             "risk": "You review proposals for business risks.",
             "operations": "You review proposals for operational "
                           "feasibility."}


async def review(name, proposal, timeout):
    model = OpenAIModel(system=REVIEWERS[name])
    messages = [{"role": "user", "content": proposal + "\nName the single "
                 "most important issue in at most eight words."}]
    reply = await asyncio.wait_for(
        asyncio.to_thread(model.generate, messages), timeout)
    return reply["answer"].strip()


async def fan_out(proposal, operations_timeout=60):
    timeouts = {"financial": 60, "risk": 60, "operations": operations_timeout}
    results = await asyncio.gather(
        *(review(name, proposal, timeouts[name]) for name in REVIEWERS),
        return_exceptions=True,  # a failed branch becomes a result
    )
    return dict(zip(REVIEWERS, results))


def bad_fan_in(branches):
    """Over-summarizes: keeps only issues that two reviewers agree on."""
    issues = [r for r in branches.values() if isinstance(r, str)]
    agreed = [issue for issue in issues if issues.count(issue) > 1]
    if agreed:
        return "Proposal needs revision."
    return "Proposal looks acceptable."


def complete_fan_in(branches):
    """Keeps every finding with its reviewer and names missing branches."""
    issues = {n: r for n, r in branches.items() if isinstance(r, str)}
    missing = [n for n, r in branches.items() if isinstance(r, Exception)]
    if missing:
        verdict = "incomplete"
    else:
        verdict = "revise" if issues else "accept"
    return {"verdict": verdict, "issues": issues, "missing": missing}


def show(label, report):
    print(f"{label}: {report['verdict']}, missing={report['missing']}")
    for reviewer, issue in report["issues"].items():
        print(f"  {reviewer}: {issue}")


async def main():
    branches = await fan_out(PROPOSAL)
    print(f"bad fan-in: {bad_fan_in(branches)}")
    show("complete fan-in", complete_fan_in(branches))
    degraded = await fan_out(PROPOSAL, operations_timeout=0.01)
    show("partial failure", complete_fan_in(degraded))


asyncio.run(main())
