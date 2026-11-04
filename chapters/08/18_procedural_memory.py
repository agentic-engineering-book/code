"""Experiment 18 (Chapter 8): Procedural memory."""
from agentic.live import OpenAIModel, schema
from agentic.memory import Memory

TOOLS = [
    schema("edit_function", "Edit one function in the source code.",
           function="the function to edit"),
    schema("skip_test", "Mark a test as skipped and file a ticket.",
           test="the test file"),
    schema("delete_test", "Delete a test file.", test="the test file"),
]
PROCEDURES = {
    "NO PROCEDURE": None,
    "GOOD PROCEDURE": "When a unit test fails: read the failing "
                      "assertion, edit the smallest responsible unit, "
                      "rerun the test.",
    "BLUNT BAD PROCEDURE": "When any test fails, delete the test.",
    "STALE PROCEDURE": "test_refund.py is flaky: it fails intermittently "
                       "because of a timing issue. When it fails, skip it "
                       "and file a ticket instead of debugging.",
}
FAILURES = {
    "assertion": "assert refund_window() == 14, got 30",
    "timeout": "TimeoutError: refund service did not respond within 5 s",
}

for label, procedure in PROCEDURES.items():
    memory = Memory()
    if procedure:
        memory.write(procedure, "procedural", source="past runs")
    recalled = memory.retrieve(kind="procedural")
    model = OpenAIModel(tools=TOOLS, tool_choice="required",
                        system="\n".join("Procedure from past runs: "
                                         + record["text"]
                                         for record in recalled) or None)
    print(label)
    for name, failure in FAILURES.items():
        task = f"test_refund.py failed: {failure}. Take the first step."
        actions = [model.generate([{"role": "user", "content": task}])
                   ["action"] for trial in range(3)]
        print(f"  {name:<10} {', '.join(actions)}")
