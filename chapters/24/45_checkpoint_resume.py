"""Experiment 45 (Chapter 24): Checkpoint and resume."""
import json
import tempfile
from pathlib import Path

STEPS = ["retrieve", "analyze", "draft", "verify", "submit"]
source = {"price": 80, "version": 4}  # the external world


def run(checkpoint_path, crash_at=None):
    executed = []
    state = {"next_step": 0, "source_version": source["version"]}
    if checkpoint_path.exists():
        state = json.loads(checkpoint_path.read_text())
        if state["source_version"] != source["version"]:
            print("  stale checkpoint: source changed, restarting")
            state = {"next_step": 0, "source_version": source["version"]}
    for index in range(state["next_step"], len(STEPS)):
        if STEPS[index] == crash_at:
            raise RuntimeError(f"crash during {crash_at}")
        executed.append(STEPS[index])
        state["next_step"] = index + 1
        checkpoint_path.write_text(json.dumps(state))
    return executed


with tempfile.TemporaryDirectory() as folder:
    checkpoint = Path(folder) / "task-T42.json"
    try:
        run(checkpoint, crash_at="verify")
    except RuntimeError as error:
        print("first run:", error)
    print("resume executes:", run(checkpoint))

with tempfile.TemporaryDirectory() as folder:
    checkpoint = Path(folder) / "task-T42.json"
    try:
        run(checkpoint, crash_at="verify")
    except RuntimeError as error:
        print("first run:", error)
    source = {"price": 90, "version": 5}  # changed while we were down
    print("resume executes:", run(checkpoint))
