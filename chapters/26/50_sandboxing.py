"""Experiment 50 (Chapter 26): Sandboxing."""
import os
import subprocess
import sys
import tempfile
import textwrap

from agentic.live import OpenAIModel

os.environ["API_KEY"] = "demo-secret"  # a credential the host process holds

# Programs written by a real model from short descriptions, standing in
# for code an agent generates. Treat them as untrusted code.
TARGET = __file__
DESCRIPTIONS = {
    "reads secret": "print the value of the environment variable API_KEY",
    "loops forever": "loop forever doing nothing",
    "reads outside workspace": "print whether the file whose name is in "
                               "the variable path can be opened and read",
}


def generate(description):
    reply = OpenAIModel().generate([{"role": "user", "content":
        f"Write a Python one-liner to {description}. Reply with the code "
        "only, no explanation, no code fences."}])
    return reply["answer"].strip().strip("`")


PROBES = {name: generate(text) for name, text in DESCRIPTIONS.items()}


def run_child(code, workspace):
    """Child process, scrubbed environment, timeout, temp working dir.

    This is NOT a sandbox: the child still runs as the host user and can
    read any file the user can read and open any network connection.
    """
    env = {}
    if os.name == "nt":  # Python on Windows needs SYSTEMROOT to start
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    try:
        program = f"path = {TARGET!r}\n{code}"  # a file outside workspace
        done = subprocess.run([sys.executable, "-I", "-c", program],
                              cwd=workspace, env=env, timeout=1,
                              capture_output=True, text=True)
        errors = done.stderr.strip().splitlines()
        return done.stdout.strip() or (errors[-1] if errors else "")
    except subprocess.TimeoutExpired:
        return "killed by 1 s timeout"


print("host process sees API_KEY:", os.environ.get("API_KEY"))
with tempfile.TemporaryDirectory() as workspace:
    for name, code in PROBES.items():
        print(textwrap.fill(f"generated ({name}): {code}", 76,
                            subsequent_indent="    "))
        print(f"  child: {run_child(code, workspace)}")
print("contained: secret, runaway loop")
print("not contained: filesystem (and network) -> needs an OS sandbox")
