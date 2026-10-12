"""Experiment 18 (Chapter 8): Procedural memory."""
from agentic import PolicyModel
from agentic.memory import Memory

GOOD = ("When a unit test fails: read the failing assertion, edit the "
        "smallest responsible unit, rerun the test.")
BAD = "When any test fails, delete the test."


def repair_policy(messages):
    """Stand-in model: follows a procedure if one is in context."""
    context = " ".join(m["content"] for m in messages).lower()
    if "delete the test" in context:
        return {"action": "delete_test", "target": "test_refund.py"}
    if "smallest responsible unit" in context:
        return {"action": "inspect_then_edit",
                "target": "refund_window()"}
    return {"action": "rewrite_module", "target": "refunds.py"}


model = PolicyModel(repair_policy)
task = {"role": "user", "content": "Repair failing unit test."}

for label, stored in [("NO PROCEDURE", []), ("GOOD PROCEDURE", [GOOD]),
                      ("BAD PROCEDURE", [BAD])]:
    memory = Memory()
    for text in stored:
        memory.write(text, "procedural", source="past runs")
    procedures = memory.retrieve(kind="procedural", query="test fails")
    context = [{"role": "system", "content": p["text"]}
               for p in procedures]
    decision = model.generate(context + [task])
    print(f"{label:<15} -> {decision['action']} {decision['target']}")
