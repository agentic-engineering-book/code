"""Experiment 52 (Chapter 27): Risk budget and autonomy envelope."""
from agentic.control import Budget

RISK = {"search": 0, "draft": 1, "send_email": 3, "delete_record": 8}
COST = {"search": 0.03, "draft": 0.02, "send_email": 0.01,
        "delete_record": 0.01}
PERMITTED = {"search", "draft", "send_email", "delete_record"}
SINGLE_ACTION_LIMIT = 8
PLAN = ["search", "draft", "send_email", "send_email", "send_email",
        "delete_record"]


def independent_checks(plan):
    """Deliberate failure: every action is judged on its own."""
    total = 0
    for action in plan:
        if RISK[action] <= SINGLE_ACTION_LIMIT:
            total += RISK[action]
    print(f"independent checks: all {len(plan)} allowed, "
          f"total risk {total}")


def may_execute(action, budget, risk_remaining):
    if action not in PERMITTED:
        return "deny: not permitted"
    if budget.refusal(COST[action]):
        return "stop: resource budget"
    if RISK[action] > risk_remaining:
        return "escalate: needs approval"
    return "execute"


def envelope(plan, risk_budget=10, sensitive_data_at=None):
    budget, risk_remaining = Budget(max_steps=20, max_cost=1.0), risk_budget
    for step, action in enumerate(plan):
        if step == sensitive_data_at:
            risk_remaining = min(risk_remaining, 2)  # envelope contracts
            print("  sensitive data detected: risk remaining -> 2")
        verdict = may_execute(action, budget, risk_remaining)
        print(f"  {action:<13} risk {RISK[action]}  {verdict:<25} "
              f"cost left {budget.cost_remaining:.2f}")
        if verdict != "execute":
            return
        budget.charge(COST[action])
        risk_remaining -= RISK[action]


independent_checks(PLAN)
print("risk budget 10:")
envelope(PLAN)
print("risk budget 10, sensitive data found at step 2:")
envelope(PLAN, sensitive_data_at=2)
