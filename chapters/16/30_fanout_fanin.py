"""Experiment 30 (Chapter 16): Fan-out/fan-in."""
import asyncio

PROPOSAL = "Open a second warehouse in Q3"


async def review_financials(proposal):
    await asyncio.sleep(0)
    return "margin assumption unsupported"


async def review_risks(proposal):
    await asyncio.sleep(0)
    return "dependency on one supplier"


async def review_operations(proposal, available=True):
    await asyncio.sleep(0)
    if not available:
        raise TimeoutError("operations reviewer timed out")
    return "timeline infeasible"


async def fan_out(proposal, operations_available=True):
    names = ["financial", "risk", "operations"]
    results = await asyncio.gather(
        review_financials(proposal),
        review_risks(proposal),
        review_operations(proposal, operations_available),
        return_exceptions=True,  # a failed branch becomes a result
    )
    return dict(zip(names, results))


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
    degraded = await fan_out(PROPOSAL, operations_available=False)
    show("partial failure", complete_fan_in(degraded))


asyncio.run(main())
