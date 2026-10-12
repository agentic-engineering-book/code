"""Experiment 12: LangChain select-to-budget stage and a corrupted ranking."""
from langchain_core.runnables import RunnableLambda

REQUIRED = {"purchase_age_days", "refund_window_days"}
GOOD = [("purchase_age_days=12", 1.0), ("refund_window_days=30", 1.0),
        ("customer_tier=Gold", 0.2), ("newsletter=True", 0.0)]
CORRUPTED = [("purchase_age_days=12", 1.0), ("customer_tier=Gold", 0.9),
             ("refund_window_days=30", 0.1), ("newsletter=True", 0.0)]


def run():
    select = RunnableLambda(lambda facts: sorted(
        facts, key=lambda fact: fact[1], reverse=True)[:2])
    measure = RunnableLambda(lambda chosen: {
        "visible": [fact for fact, score in chosen],
        "coverage": len(REQUIRED & {f.split("=")[0] for f, _ in chosen})
        / len(REQUIRED)})
    pipeline = select | measure
    return {"good": pipeline.invoke(GOOD),
            "corrupted": pipeline.invoke(CORRUPTED)}


if __name__ == "__main__":
    print(run())
