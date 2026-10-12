"""Experiment 25 (Chapter 13): Reflection."""
from agentic import calculator

TASK = "17 * 6"

# Scripted critics: draft -> critique (None means "no defect found").
GOOD_CRITIC = {
    96: {"text": "The multiplication is incorrect. 17 * 6 = 102.",
         "proposed": 102},
    102: None,
}
BAD_CRITIC = {
    96: {"text": "The answer should be 112.", "proposed": 112},
    102: {"text": "The answer should be 112.", "proposed": 112},
}


def revise(draft, critique):
    return draft if critique is None else critique["proposed"]


def verified_revise(draft, critique):
    """Change the draft only if a tool confirms the proposed value."""
    if critique is None or calculator(TASK) != critique["proposed"]:
        return draft
    return critique["proposed"]


def outcome(draft, revision):
    correct = calculator(TASK)
    if draft != correct:
        return "improvement" if revision == correct else "no useful repair"
    return "preserved" if revision == correct else "REGRESSION"


print(f"{'draft':>5}  {'critic':6}  {'policy':8}  {'revision':>8}  outcome")
for policy_name, policy in [("always", revise),
                            ("verified", verified_revise)]:
    counts = {}
    for critic_name, critic in [("good", GOOD_CRITIC), ("bad", BAD_CRITIC)]:
        for draft in (96, 102):
            revision = policy(draft, critic[draft])
            result = outcome(draft, revision)
            counts[result] = counts.get(result, 0) + 1
            print(f"{draft:>5}  {critic_name:6}  {policy_name:8}  "
                  f"{revision:>8}  {result}")
    print(f"  {policy_name}: improvements={counts.get('improvement', 0)} "
          f"regressions={counts.get('REGRESSION', 0)}")
