"""Run experiments that call a real model and record what they printed.

A real model's answer changes from run to run, so the book prints one
recorded run. The output of chapters/01/01_llm_call.py is saved as
chapters/01/output/01_llm_call.txt, with the model and date in a header
comment that the book leaves out.

    python tools/record_output.py chapters/01/01_llm_call.py [...]

Requires OPENAI_API_KEY and makes paid requests.
"""
from datetime import datetime, timezone
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from agentic.live import MODEL  # noqa: E402


def record(script):
    script = (ROOT / script).resolve()
    env = {**os.environ, "PYTHONPATH": str(ROOT), "PYTHONIOENCODING": "utf-8"}
    done = subprocess.run([sys.executable, str(script)], cwd=ROOT, env=env,
                          capture_output=True, text=True, encoding="utf-8")
    if done.returncode:
        sys.exit(f"{script.name} failed:\n{done.stderr}")
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    target = script.parent / "output" / f"{script.stem}.txt"
    target.parent.mkdir(exist_ok=True)
    target.write_text(f"# model {MODEL}, run {date}\n{done.stdout}",
                      encoding="utf-8")
    print(f"--- {target.relative_to(ROOT).as_posix()}\n{done.stdout}")


if __name__ == "__main__":
    for path in sys.argv[1:]:
        record(path)
