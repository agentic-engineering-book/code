"""Experiment 54: LangGraph repair loop fed by full-suite test failures."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

TESTS = '''from calc import divide

CASES = [((1, 0), None), ((6, 3), 2.0), ((7, 2), 3.5)]
for args, expected in CASES:
    actual = divide(*args)
    if actual != expected or (actual is None) != (expected is None):
        print(f"divide{args}: expected {expected}, got {actual}")
'''
BODY = ("def divide(a, b):\n    if b == 0:\n        return {zero}\n"
        "    return a {op} b\n")
PATCHES = {"": BODY.format(zero=0, op="/"),
           "expected None": BODY.format(zero=None, op="//"),
           "expected 3.5": BODY.format(zero=None, op="/")}


class State(TypedDict):
    feedback: str
    history: list


def make_graph(workspace):
    def propose(state):  # scripted model: picks a patch from the feedback
        clue = next(c for c in reversed(PATCHES) if c in state["feedback"])
        (workspace / "calc.py").write_text(PATCHES[clue])
        return {}

    def test(state):
        # Temp dir, empty environment, timeout. This is NOT a sandbox.
        env = ({"SYSTEMROOT": os.environ["SYSTEMROOT"]}
               if os.name == "nt" else {})
        done = subprocess.run([sys.executable, "-B", "test_divide.py"],
                              cwd=workspace, env=env, capture_output=True,
                              text=True, timeout=10)
        feedback = done.stdout.strip() or "all passed"
        return {"feedback": feedback,
                "history": state["history"] + [feedback]}

    builder = StateGraph(State)
    builder.add_node("propose", propose)
    builder.add_node("test", test)
    builder.add_edge(START, "propose")
    builder.add_edge("propose", "test")
    builder.add_conditional_edges(
        "test", lambda s: END if s["feedback"] == "all passed"
        or len(s["history"]) >= 4 else "propose")
    return builder.compile()


def run():
    with tempfile.TemporaryDirectory() as folder:
        workspace = Path(folder)
        (workspace / "test_divide.py").write_text(TESTS)
        final = make_graph(workspace).invoke({"feedback": "",
                                              "history": []})
    return {"attempts": len(final["history"]),
            "feedback": final["history"]}


if __name__ == "__main__":
    print(run())
