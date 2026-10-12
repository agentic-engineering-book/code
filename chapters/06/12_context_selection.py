"""Experiment 12 (Chapter 6): Context selection."""
from agentic.context import select_top

REQUIRED = {"purchase_age_days", "refund_window_days"}

good_scores = [
    ("purchase_age_days=12", 1.0),
    ("refund_window_days=30", 1.0),
    ("customer_tier=Gold", 0.2),
    ("newsletter=True", 0.0),
]
corrupted_scores = [
    ("purchase_age_days=12", 1.0),
    ("customer_tier=Gold", 0.9),
    ("refund_window_days=30", 0.1),
    ("newsletter=True", 0.0),
]

for label, facts in [("GOOD RANKING", good_scores),
                     ("CORRUPTED RANKING", corrupted_scores)]:
    selected = select_top(facts, budget=2)
    visible = {fact.split("=")[0] for fact, score in selected}
    print(label)
    for fact, score in selected:
        print(f"  {fact:<24} score {score}")
    print(f"  required-fact coverage: {len(REQUIRED & visible)}/2")
