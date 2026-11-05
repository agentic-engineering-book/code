"""Experiment 53: Coding agent in LangGraph. See framework_examples/README."""
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from framework_examples.support import chat

REPOSITORY = {
    "calculator.py": "def add(a, b):\n    return a - b\n",
    "test_calculator.py": ("from calculator import add\n\n\n"
                           "def test_add():\n"
                           "    assert add(2, 3) == 5\n"),
}


def make_tools(workspace):
    def inside(path):
        target = (workspace / path).resolve()
        if workspace.resolve() not in target.parents:
            raise ValueError(f"path outside workspace: {path}")
        return target

    @tool
    def list_files() -> list:
        """List the Python files."""
        return sorted(p.name for p in workspace.glob("*.py"))

    @tool
    def read_file(path: str) -> str:
        """Read a file."""
        return inside(path).read_text()

    @tool
    def patch_file(path: str, old: str, new: str) -> str:
        """Replace one exact snippet in a file."""
        source = inside(path).read_text()
        if source.count(old) != 1:
            raise ValueError("patch must match exactly one location")
        inside(path).write_text(source.replace(old, new))
        return f"patched {path}: {old!r} -> {new!r}"

    @tool
    def run_tests() -> str:
        """Run the test suite."""
        # Temp dir, empty environment, timeout. This is NOT a sandbox.
        env = ({"SYSTEMROOT": os.environ["SYSTEMROOT"]}
               if os.name == "nt" else {})
        done = subprocess.run(
            [sys.executable, "-B", "-c",
             "from test_calculator import test_add; test_add()"],
            cwd=workspace, env=env, capture_output=True, timeout=10)
        return "1 passed" if done.returncode == 0 else "1 failed"

    return [list_files, read_file, patch_file, run_tests]


def tests_passed(state):
    """The tests, not the model, end the loop."""
    return END if state["messages"][-1].content == "1 passed" else "model"


def run():
    with tempfile.TemporaryDirectory() as folder:
        workspace = Path(folder)
        for name, text in REPOSITORY.items():
            (workspace / name).write_text(text)
        tools = make_tools(workspace)
        model = chat().bind_tools(tools, parallel_tool_calls=False)
        builder = StateGraph(MessagesState)
        builder.add_node(
            "model", lambda s: {"messages": [model.invoke(s["messages"])]})
        builder.add_node("tools", ToolNode(tools, handle_tool_errors=True))
        builder.add_edge(START, "model")
        builder.add_conditional_edges("model", tools_condition)
        builder.add_conditional_edges("tools", tests_passed)
        result = builder.compile().invoke(
            {"messages": [("system", "You are a coding agent. Make the "
                           "tests pass by fixing the code, not the tests."),
                          ("user", "The tests fail. Fix the bug.")]},
            {"recursion_limit": 16})
        lines, step = [], 0
        for message in result["messages"]:
            if isinstance(message, AIMessage) and message.tool_calls:
                step += 1
                name = message.tool_calls[0]["name"]
            elif isinstance(message, ToolMessage):
                lines.append(textwrap.shorten(
                    f"step {step}: {name} -> {message.content!r}", 76))
        if result["messages"][-1].content == "1 passed":
            lines.append("completed: the tests, not the model, ended the "
                         "loop")
        try:
            tools[1].invoke({"path": "../secrets.txt"})
        except ValueError as error:
            lines.append(f"denied: {error}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
