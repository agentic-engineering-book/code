"""Experiment 54 (Chapter 28): Iterative repair."""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from agentic.live import OpenAIModel

# The tests belong to the harness. The agent sees only their failures.
TESTS = '''from prices import parse_price

CASES = {"dollars": ("$1,234.50", 123450), "plain": ("12", 1200),
         "euro comma": ("3,50 EUR", 350), "empty": ("", None)}
for name, (text, expected) in CASES.items():
    try:
        actual = parse_price(text)
    except Exception as error:
        actual = type(error).__name__
    if actual != expected:
        print(f"FAILED {name}: parse_price({text!r}) "
              f"expected {expected}, got {actual!r}")
'''
TASK = ("Implement parse_price(text) in prices.py: it returns the price in "
        "the text as an integer number of cents.")
CASE_NAMES = {"dollars", "plain", "euro comma", "empty"}


def run_tests(workspace):
    """Temp dir, empty environment, timeout. This is NOT a sandbox."""
    env = {"SYSTEMROOT": os.environ["SYSTEMROOT"]} if os.name == "nt" else {}
    done = subprocess.run([sys.executable, "-B", "test_prices.py"],
                          cwd=workspace, env=env, capture_output=True,
                          text=True, timeout=10)
    return done.stdout.strip()


model = OpenAIModel(system="You are a coding agent. Reply with the "
                    "complete new contents of prices.py only, no code fences.")
messages = [{"role": "user", "content": TASK}]
passed_before = set()
with tempfile.TemporaryDirectory() as folder:
    workspace = Path(folder)
    (workspace / "test_prices.py").write_text(TESTS)
    for attempt in range(1, 5):  # bounded repair loop
        code = model.generate(messages)["answer"].strip().strip("`")
        code = code.removeprefix("python\n")
        (workspace / "prices.py").write_text(code, encoding="utf-8")
        output = run_tests(workspace)
        failed = {line.split(":")[0].removeprefix("FAILED ")
                  for line in output.splitlines()}
        regressed = passed_before & failed  # passed before, fails now
        print(f"attempt {attempt}: failing {sorted(failed) or 'none'}"
              + (f", REGRESSED {sorted(regressed)}" if regressed else ""))
        if not failed:
            break
        passed_before |= CASE_NAMES - failed
        messages += [{"role": "assistant", "content": {"answer": code}},
                     {"role": "user", "content": "Test output:\n" + output}]
