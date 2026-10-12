"""Experiment 53: LangGraph inspect -> patch -> test loop on a temp repo."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

REPOSITORY = {
    "calculator.py": "def add(a, b):\n    return a - b\n",
    "test_calculator.py": ("from calculator import add\n\n\n"
                           "def test_add():\n"
                           "    assert add(2, 3) == 5\n"),
}


class State(TypedDict):
    source: str
    tests: str
    attempts: int


def make_graph(workspace):
    def inspect(state):
        return {"source": (workspace / "calculator.py").read_text()}

    def patch(state):  # the scripted "model" proposes a one-line edit
        fixed = state["source"].replace("a - b", "a + b")
        (workspace / "calculator.py").write_text(fixed)
        return {"source": fixed, "attempts": state["attempts"] + 1}

    def test(state):
        # Temp dir, empty environment, timeout. This is NOT a sandbox.
        env = ({"SYSTEMROOT": os.environ["SYSTEMROOT"]}
               if os.name == "nt" else {})
        done = subprocess.run(
            [sys.executable, "-B", "-c",
             "from test_calculator import test_add; test_add()"],
            cwd=workspace, env=env, capture_output=True, timeout=10)
        return {"tests": "passed" if done.returncode == 0 else "failed"}

    builder = StateGraph(State)
    for name, node in [("inspect", inspect), ("test", test),
                       ("patch", patch)]:
        builder.add_node(name, node)
    builder.add_edge(START, "inspect")
    builder.add_edge("inspect", "test")
    builder.add_conditional_edges(
        "test", lambda s: END if s["tests"] == "passed"
        or s["attempts"] >= 3 else "patch")
    builder.add_edge("patch", "test")
    return builder.compile()


def run():
    with tempfile.TemporaryDirectory() as folder:
        workspace = Path(folder)
        for name, text in REPOSITORY.items():
            (workspace / name).write_text(text)
        final = make_graph(workspace).invoke(
            {"source": "", "tests": "", "attempts": 0})
    return {"tests": final["tests"], "patches": final["attempts"],
            "source": final["source"]}


if __name__ == "__main__":
    print(run())
