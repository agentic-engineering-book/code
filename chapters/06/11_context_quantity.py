"""Experiment 11 (Chapter 6): Context quantity."""
from agentic.context import coverage

REQUIRED = {"purchase_age_days", "refund_window_days"}
NOISE = {
    "customer_tier": "Gold",
    "preferred_language": "English",
    "last_login": "Tuesday",
    "shipping_method": "Express",
    "newsletter": "subscribed",
    "warehouse": "North",
}
CONTEXTS = {
    "minimal relevant": {"purchase_age_days": 12, "refund_window_days": 30},
    "relevant + noise": {"purchase_age_days": 12, "refund_window_days": 30,
                         **NOISE},
    "large but incomplete": {"purchase_age_days": 12, **NOISE},
}


def decide(context):
    """Deterministic refund rule: it can only use facts it is given."""
    if coverage(context, REQUIRED) < 1:
        return "cannot decide"
    eligible = context["purchase_age_days"] <= context["refund_window_days"]
    return "refund" if eligible else "no refund"


for name, context in CONTEXTS.items():
    distractors = len(context.keys() - REQUIRED)
    print(f"{name:<21} coverage={coverage(context, REQUIRED):.1f} "
          f"fields={len(context)} distractors={distractors} "
          f"-> {decide(context)}")
