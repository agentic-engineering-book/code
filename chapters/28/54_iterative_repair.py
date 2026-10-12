"""Experiment 54 (Chapter 28): Iterative repair."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from agentic import PolicyModel, last_observation

TESTS = '''import sys
from calc import divide

CASES = {"zero": ((1, 0), None), "exact": ((6, 3), 2.0),
         "fraction": ((7, 2), 3.5)}
for name in sys.argv[1:] or CASES:
    args, expected = CASES[name]
    actual = divide(*args)
    if actual != expected or (actual is None) != (expected is None):
        print(f"FAILED divide{args}: expected {expected}, got {actual}")
'''
BODY = ("def divide(a, b):\n    if b == 0:\n        return {zero}\n"
        "    return a {op} b\n")
PATCHES = {  # what a model might propose after each kind of feedback
    None: BODY.format(zero=0, op="/"),
    "expected None": BODY.format(zero=None, op="//"),
    "expected 3.5": BODY.format(zero=None, op="/"),
}


def propose(messages):
    feedback = last_observation(messages) or ""
    for clue, patch in PATCHES.items():
        if clue and clue in feedback:
            return patch
    return PATCHES[None]


def run_tests(workspace, *names):
    """Temp dir, empty environment, timeout. This is NOT a sandbox."""
    env = {"SYSTEMROOT": os.environ["SYSTEMROOT"]} if os.name == "nt" else {}
    done = subprocess.run([sys.executable, "-B", "test_divide.py", *names],
                          cwd=workspace, env=env, capture_output=True,
                          text=True, timeout=10)
    return done.stdout.strip() or "all passed"


model = PolicyModel(propose)
messages = [{"role": "user", "content": "divide(a, 0) must return None"}]
with tempfile.TemporaryDirectory() as folder:
    workspace = Path(folder)
    (workspace / "test_divide.py").write_text(TESTS)
    for attempt in range(1, 5):  # bounded repair loop
        (workspace / "calc.py").write_text(model.generate(messages))
        targeted = run_tests(workspace, "zero")
        full = run_tests(workspace)
        print(f"attempt {attempt}: targeted test -> {targeted}")
        print(f"           full suite    -> {full}")
        if full == "all passed":
            break
        messages.append({"role": "tool", "content": full})
