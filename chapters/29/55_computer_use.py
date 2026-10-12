"""Experiment 55 (Chapter 29): Computer use."""


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


def locate(observation, label):
    matches = [c for name, c in observation["buttons"].items()
               if name == label]
    if len(matches) != 1:
        raise LookupError(f"{label!r} is missing or ambiguous")
    return matches[0]


print("Stale coordinates:")
screen = ToyScreen()
target = locate(screen.observe(), "Submit")
screen.dialog_appears()
print(f"  click {target} -> pressed {screen.click(target)!r}")

print("Re-observe, ground by label, verify the postcondition:")
screen = ToyScreen()
target = locate(screen.observe(), "Submit")
screen.dialog_appears()  # e.g. while a human approves the action
target = locate(screen.observe(), "Submit")  # re-ground just before acting
print(f"  click {target} -> pressed {screen.click(target)!r}")
after = screen.observe()
verified = after["message"] == "Submitted successfully"
print(f"  postcondition verified from new observation: {verified}")
