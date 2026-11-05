"""Experiment 54: Repair loop in LangGraph. See framework_examples/README."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, MessagesState, StateGraph

from framework_examples.support import chat

# The tests belong to the harness. The agent sees only their failures.
TESTS = '''from prices import parse_price

CASES = {"dollars": ("$1,234.50", 123450), "plain": ("12", 1200),
         "euro comma": ("3,50 EUR", 350), "empty": ("", None)}
for name, (text, expected) in CASES.items():
    try:
        actual = parse_price(text)
    except Exception as error:
        actual = type(error).__name__
    if actual != expected:
        print(f"FAILED {name}: parse_price({text!r}) "
              f"expected {expected}, got {actual!r}")
'''
TASK = ("Implement parse_price(text) in prices.py: it returns the price in "
        "the text as an integer number of cents.")
CASE_NAMES = {"dollars", "plain", "euro comma", "empty"}


class State(MessagesState):
    failed: set
    passed_before: set
    attempt: int


def build(workspace, lines):
    model = chat()

    def propose(state):
        reply = model.invoke(state["messages"])
        code = reply.text.strip().strip("`").removeprefix("python\n")
        (workspace / "prices.py").write_text(code, encoding="utf-8")
        return {"messages": [AIMessage(code)]}

    def test(state):
        # Temp dir, empty environment, timeout. This is NOT a sandbox.
        env = ({"SYSTEMROOT": os.environ["SYSTEMROOT"]}
               if os.name == "nt" else {})
        output = subprocess.run(
            [sys.executable, "-B", "test_prices.py"], cwd=workspace,
            env=env, capture_output=True, text=True, timeout=10
        ).stdout.strip()
        failed = {line.split(":")[0].removeprefix("FAILED ")
                  for line in output.splitlines()}
        regressed = state["passed_before"] & failed  # passed, now fails
        attempt = state["attempt"] + 1
        lines.append(f"attempt {attempt}: failing {sorted(failed) or 'none'}"
                     + (f", REGRESSED {sorted(regressed)}"
                        if regressed else ""))
        return {"messages": [HumanMessage("Test output:\n" + output)],
                "failed": failed, "attempt": attempt,
                "passed_before": state["passed_before"]
                | (CASE_NAMES - failed)}

    builder = StateGraph(State)
    builder.add_node("propose", propose)
    builder.add_node("test", test)
    builder.add_edge(START, "propose")
    builder.add_edge("propose", "test")
    builder.add_conditional_edges(  # bounded repair loop
        "test", lambda s: END if not s["failed"] or s["attempt"] >= 4
        else "propose")
    return builder.compile()


def run():
    lines = []
    with tempfile.TemporaryDirectory() as folder:
        workspace = Path(folder)
        (workspace / "test_prices.py").write_text(TESTS)
        build(workspace, lines).invoke(
            {"messages": [("system", "You are a coding agent. Reply with "
                           "the complete new contents of prices.py only, "
                           "no code fences."), ("user", TASK)],
             "passed_before": set(), "attempt": 0})
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
