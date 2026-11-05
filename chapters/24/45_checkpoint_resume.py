"""Experiment 45 (Chapter 24): Checkpoint and resume."""
import json
import tempfile
from pathlib import Path

from agentic.live import OpenAIModel

STEPS = ["retrieve", "analyze", "draft", "verify", "submit"]
source = {"price": 80, "version": 4}  # the external world
model = OpenAIModel()


def do_step(name):
    """Each step is a real model call."""
    reply = model.generate([{"role": "user", "content":
                             f"Task T42: the price is {source['price']}. "
                             f"Do the '{name}' step in at most eight words."}])
    return reply["answer"].strip()


def run(checkpoint_path, crash_at=None):
    executed, calls_before = [], len(model.calls)
    state = {"next_step": 0, "source_version": source["version"],
             "outputs": {}}
    if checkpoint_path.exists():
        state = json.loads(checkpoint_path.read_text())
        if state["source_version"] != source["version"]:
            print("  stale checkpoint: source changed, restarting")
            state = {"next_step": 0, "source_version": source["version"],
                     "outputs": {}}
    for index in range(state["next_step"], len(STEPS)):
        if STEPS[index] == crash_at:
            raise RuntimeError(f"crash during {crash_at}, after "
                               f"{len(model.calls) - calls_before} "
                               "model calls")
        state["outputs"][STEPS[index]] = do_step(STEPS[index])
        executed.append(STEPS[index])
        state["next_step"] = index + 1
        checkpoint_path.write_text(json.dumps(state))
    return (", ".join(executed) +
            f" ({len(model.calls) - calls_before} model calls)")


with tempfile.TemporaryDirectory() as folder:
    checkpoint = Path(folder) / "task-T42.json"
    try:
        run(checkpoint, crash_at="verify")
    except RuntimeError as error:
        print("first run:", error)
    print("resume:", run(checkpoint))

with tempfile.TemporaryDirectory() as folder:
    checkpoint = Path(folder) / "task-T42.json"
    try:
        run(checkpoint, crash_at="verify")
    except RuntimeError as error:
        print("first run:", error)
    source = {"price": 90, "version": 5}  # changed while we were down
    print("resume:", run(checkpoint))
