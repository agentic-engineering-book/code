"""Experiment 51 (Chapter 27): Resource budgets."""
from agentic.control import Budget

SEARCH_COST = 0.03  # abstract cost units per search, not real prices


def search(step):
    """Every search returns another secondary source; none is decisive."""
    return f"secondary source {step + 1}"


def enough(evidence):
    return any("primary" in item for item in evidence)


def unbounded(max_iterations=100):
    evidence, cost = [], 0.0
    for step in range(max_iterations):
        evidence.append(search(step))
        cost += SEARCH_COST
        if enough(evidence):
            return "answer", len(evidence), cost
    return "no answer", len(evidence), cost


def bounded(budget):
    evidence = []
    while True:
        reason = budget.refusal(SEARCH_COST)  # check BEFORE spending
        if reason:
            return {"status": "BUDGET_EXHAUSTED", "reason": reason,
                    "steps": budget.steps_used, "cost": budget.cost_used,
                    "best_evidence": evidence[-1:]}
        budget.charge(SEARCH_COST)
        evidence.append(search(budget.steps_used - 1))
        if enough(evidence):
            return {"status": "COMPLETED", "steps": budget.steps_used}


def show(label, budget):
    result = bounded(budget)
    print(f"{label}: {result['status']} ({result['reason']})")
    print(f"  steps {result['steps']}, cost {result['cost']:.2f}, "
          f"kept {result['best_evidence']}")


status, steps, cost = unbounded()
print(f"unbounded: {status} after {steps} searches, cost {cost:.2f}")
show("max 5 steps, max cost 0.10", Budget(max_steps=5, max_cost=0.10))
show("max 2 steps, max cost 1.00", Budget(max_steps=2, max_cost=1.00))
