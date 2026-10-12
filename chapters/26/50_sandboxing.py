"""Experiment 50 (Chapter 26): Sandboxing."""
import os
import subprocess
import sys
import tempfile

os.environ["API_KEY"] = "demo-secret"  # a credential the host process holds

# "Generated" programs. Treat them as untrusted code.
PROBES = {
    "reads secret": "import os; print(os.environ.get('API_KEY'))",
    "loops forever": "while True: pass",
    "reads outside workspace": f"print(len(open({__file__!r}).read()) > 0)",
}


def run_child(code, workspace):
    """Child process, scrubbed environment, timeout, temp working dir.

    This is NOT a sandbox: the child still runs as the host user and can
    read any file the user can read and open any network connection.
    """
    env = {}
    if os.name == "nt":  # Python on Windows needs SYSTEMROOT to start
        env["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    try:
        done = subprocess.run([sys.executable, "-I", "-c", code],
                              cwd=workspace, env=env, timeout=1,
                              capture_output=True, text=True)
        return done.stdout.strip()
    except subprocess.TimeoutExpired:
        return "killed by 1 s timeout"


print("host process sees API_KEY:", os.environ.get("API_KEY"))
with tempfile.TemporaryDirectory() as workspace:
    for name, code in PROBES.items():
        print(f"child {name}: {run_child(code, workspace)}")
print("contained: secret, runaway loop")
print("not contained: filesystem (and network) -> needs an OS sandbox")
