"""Experiment 55 (Chapter 29): Computer use."""
import json

from agentic.live import OpenAIModel


class ToyScreen:
    """A recorded interface: labelled buttons at pixel centres."""

    def __init__(self):
        self.buttons = {"Submit": (420, 610), "Cancel": (300, 610)}
        self.message = ""

    def observe(self):
        return {"buttons": dict(self.buttons), "message": self.message}

    def dialog_appears(self):  # the layout shifts under the agent
        self.buttons = {"Delete": (420, 610), "Submit": (510, 610),
                        "Cancel": (300, 610)}

    def click(self, point):
        for label, centre in self.buttons.items():
            if centre == point:
                if label == "Submit":
                    self.message = "Submitted successfully"
                return label
        return None


def locate(observation, goal):
    """A real model grounds the goal in the observed screen."""
    model = OpenAIModel(system="You control a mouse. Reply with JSON: "
                        '{"x": ..., "y": ...} for the centre to click, or '
                        '{"x": null, "y": null} if no control fits.',
                        response_format={"type": "json_object"})
    reply = model.generate([{"role": "user", "content":
                             f"Screen: {json.dumps(observation)}\n"
                             f"Goal: {goal}"}])
    point = json.loads(reply["answer"])
    if point["x"] is None:
        raise LookupError(f"no control for {goal!r}")
    return (int(point["x"]), int(point["y"]))


print("Stale coordinates:")
screen = ToyScreen()
target = locate(screen.observe(), "submit the form")
screen.dialog_appears()
print(f"  click {target} -> pressed {screen.click(target)!r}")

print("Re-observe, ground by label, verify the postcondition:")
screen = ToyScreen()
target = locate(screen.observe(), "submit the form")
screen.dialog_appears()  # e.g. while a human approves the action
target = locate(screen.observe(), "submit the form")  # re-ground now
print(f"  click {target} -> pressed {screen.click(target)!r}")
after = screen.observe()
verified = after["message"] == "Submitted successfully"
print(f"  postcondition verified from new observation: {verified}")
