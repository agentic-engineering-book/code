"""Experiment 50: a LangChain tool that runs code in a limited child."""
import os
import subprocess
import sys
import tempfile

from langchain_core.tools import tool


@tool
def run_python(code: str) -> str:
    """Run Python in a temp dir with no inherited environment and a timeout.

    This is NOT a sandbox: the child still has the user's filesystem and
    network access. Real isolation needs a container or VM boundary.
    """
    env = {}
    if os.name == "nt":  # Python on Windows needs SYSTEMROOT to start
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    with tempfile.TemporaryDirectory() as workspace:
        try:
            done = subprocess.run([sys.executable, "-I", "-c", code],
                                  cwd=workspace, env=env, timeout=1,
                                  capture_output=True, text=True)
        except subprocess.TimeoutExpired:
            return "timeout"
    return done.stdout.strip()


def run():
    os.environ["API_KEY"] = "demo-secret"
    probes = {
        "secret": "import os; print(os.environ.get('API_KEY'))",
        "runaway": "while True: pass",
        "host_file": f"print(len(open({__file__!r}).read()) > 0)",
    }
    results = {name: run_python.invoke({"code": code})
               for name, code in probes.items()}
    del os.environ["API_KEY"]
    return {"registered_tools": [run_python.name], "results": results,
            "contained": ["secret", "runaway"],
            "not_contained": ["host_file"]}


if __name__ == "__main__":
    print(run())
