"""Experiment 42: LangChain parallel branches: total work vs critical path."""
from langchain_core.runnables import RunnableLambda, RunnableParallel

# Fixture measurements (simulated ms and $), not live timings or invoices.
BRANCHES = {"A": (200, 0.001), "B": (900, 0.004), "C": (400, 0.002)}


def branch(name):
    duration_ms, cost = BRANCHES[name]
    return RunnableLambda(
        lambda _: {"duration_ms": duration_ms, "cost": cost}, name=name)


def run():
    fan_out = RunnableParallel({name: branch(name) for name in BRANCHES})
    spans = fan_out.invoke("question")
    work = sum(span["duration_ms"] for span in spans.values())
    critical = max(spans, key=lambda name: spans[name]["duration_ms"])
    cost = sum(span["cost"] for span in spans.values())
    return {"branch_work_ms": work, "critical_branch": critical,
            "wall_clock_ms": spans[critical]["duration_ms"],
            "cost": round(cost, 3)}


if __name__ == "__main__":
    print(run())
