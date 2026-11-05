"""Experiment 50: Sandboxing in LangChain. See framework_examples/README."""
import os
import subprocess
import sys
import tempfile
import textwrap

from langchain_core.tools import tool

from framework_examples.support import chat

# Programs written by a real model from short descriptions, standing in
# for code an agent generates. Treat them as untrusted code.
DESCRIPTIONS = {
    "reads secret": "print the value of the environment variable API_KEY",
    "loops forever": "loop forever doing nothing",
    "reads outside workspace": "print whether the file whose name is in "
                               "the variable path can be opened and read",
}


def generate(description):
    reply = chat().invoke(f"Write a Python one-liner to {description}. "
                          "Reply with the code only, no explanation, "
                          "no code fences.")
    return reply.text.strip().strip("`")


@tool
def run_python(code: str) -> str:
    """Run Python in a temp dir with no inherited environment and a timeout.

    This is NOT a sandbox: the child still runs as the host user and can
    read any file the user can read and open any network connection.
    """
    env = {}
    if os.name == "nt":  # Python on Windows needs SYSTEMROOT to start
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    program = f"path = {__file__!r}\n{code}"  # a file outside workspace
    with tempfile.TemporaryDirectory() as workspace:
        try:
            done = subprocess.run([sys.executable, "-I", "-c", program],
                                  cwd=workspace, env=env, timeout=1,
                                  capture_output=True, text=True)
        except subprocess.TimeoutExpired:
            return "killed by 1 s timeout"
    errors = done.stderr.strip().splitlines()
    return done.stdout.strip() or (errors[-1] if errors else "")


def run():
    os.environ["API_KEY"] = "demo-secret"  # a credential the host holds
    lines = ["host process sees API_KEY: " + os.environ["API_KEY"]]
    for name, description in DESCRIPTIONS.items():
        code = generate(description)
        lines += textwrap.wrap(f"generated ({name}): {code}", 76,
                               subsequent_indent="    ")
        result = run_python.invoke({"code": code})
        lines.append("  " + textwrap.shorten(f"child: {result}", 74))
    del os.environ["API_KEY"]
    lines.append("contained: secret, runaway loop")
    lines.append("not contained: filesystem (and network) -> needs an OS "
                 "sandbox")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
