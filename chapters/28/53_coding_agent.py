"""Experiment 53 (Chapter 28): The smallest coding agent."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from agentic import ScriptedModel, execute

REPOSITORY = {
    "calculator.py": "def add(a, b):\n    return a - b\n",
    "test_calculator.py": ("from calculator import add\n\n\n"
                           "def test_add():\n"
                           "    assert add(2, 3) == 5\n"),
}


def scrubbed_env():
    """No inherited secrets; Windows needs SYSTEMROOT to start Python."""
    return {"SYSTEMROOT": os.environ["SYSTEMROOT"]} if os.name == "nt" else {}


def make_tools(workspace):
    def inside(path):
        target = (workspace / path).resolve()
        if workspace.resolve() not in target.parents:
            raise ValueError(f"path outside workspace: {path}")
        return target

    def list_files():
        return sorted(p.name for p in workspace.glob("*.py"))

    def read_file(path):
        return inside(path).read_text()

    def patch_file(path, old, new):
        source = inside(path).read_text()
        if source.count(old) != 1:
            raise ValueError("patch must match exactly one location")
        inside(path).write_text(source.replace(old, new))
        return f"patched {path}: {old!r} -> {new!r}"

    def run_tests():
        # Temp dir, empty environment, timeout. This is NOT a sandbox.
        done = subprocess.run(
            [sys.executable, "-B", "-c",
             "from test_calculator import test_add; test_add()"],
            cwd=workspace, env=scrubbed_env(), capture_output=True,
            timeout=10)
        return "1 passed" if done.returncode == 0 else "1 failed"

    return {"list_files": list_files, "read_file": read_file,
            "patch_file": patch_file, "run_tests": run_tests}


model = ScriptedModel([
    {"action": "list_files", "arguments": {}},
    {"action": "run_tests", "arguments": {}},
    {"action": "read_file", "arguments": {"path": "calculator.py"}},
    {"action": "patch_file",
     "arguments": {"path": "calculator.py", "old": "a - b", "new": "a + b"}},
    {"action": "run_tests", "arguments": {}},
])

with tempfile.TemporaryDirectory() as folder:
    workspace = Path(folder)
    for name, text in REPOSITORY.items():
        (workspace / name).write_text(text)
    tools = make_tools(workspace)
    for step in range(1, 9):
        decision = model.generate([])
        result = execute(decision, tools=tools)
        print(f"step {step}: {decision['action']} -> {result!r}")
        if decision["action"] == "run_tests" and result == "1 passed":
            print("completed: the tests, not the model, ended the loop")
            break
    try:
        tools["read_file"]("../secrets.txt")
    except ValueError as error:
        print("denied:", error)
