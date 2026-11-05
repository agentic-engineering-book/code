"""Experiment 53 (Chapter 28): The smallest coding agent."""
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from agentic import execute
from agentic.live import OpenAIModel, schema

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


SCHEMAS = [schema("list_files", "List the Python files."),
           schema("read_file", "Read a file.", path="file name"),
           schema("patch_file", "Replace one exact snippet in a file.",
                  path="file name", old="exact text to replace",
                  new="replacement text"),
           schema("run_tests", "Run the test suite.")]
model = OpenAIModel(tools=SCHEMAS, system="You are a coding agent. Make "
                    "the tests pass by fixing the code, not the tests.")
messages = [{"role": "user", "content": "The tests fail. Fix the bug."}]

with tempfile.TemporaryDirectory() as folder:
    workspace = Path(folder)
    for name, text in REPOSITORY.items():
        (workspace / name).write_text(text)
    tools = make_tools(workspace)
    for step in range(1, 9):
        decision = model.generate(messages)
        if decision.get("done"):
            print(f"step {step}: model stops without passing tests")
            break
        result = execute(decision, tools=tools)
        print(textwrap.shorten(f"step {step}: {decision['action']} -> "
                               f"{result!r}", 76))
        messages += [{"role": "assistant", "content": decision},
                     {"role": "tool", "content": str(result)}]
        if decision["action"] == "run_tests" and result == "1 passed":
            print("completed: the tests, not the model, ended the loop")
            break
    try:
        tools["read_file"]("../secrets.txt")
    except ValueError as error:
        print("denied:", error)
