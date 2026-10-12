"""Experiment 26: Beam search as a bounded LangGraph loop."""
from framework_examples.support import bounded_loop

START, TARGET, DEPTH = 2, 13, 2
OPERATIONS = {"+3": lambda x: x + 3, "*2": lambda x: x * 2,
              "+9": lambda x: x + 9}


def closeness(candidate):
    return -abs(TARGET - candidate[0])


def beam_step(width):
    def update(state):
        candidates = [(op(value), path + [name])
                      for value, path in state["value"]
                      for name, op in OPERATIONS.items()]
        best = sorted(candidates, key=closeness, reverse=True)[:width]
        return {"value": best, "step": state["step"] + 1}
    return update


def run():
    found = {}
    for width in (1, 2, 3):
        final = bounded_loop(beam_step(width),
                             lambda s: s["step"] == DEPTH,
                             {"value": [(START, [])], "step": 0})
        hits = [" ".join(path) for value, path in final["value"]
                if value == TARGET]
        found[f"width {width}"] = hits[0] if hits else None
    return found


if __name__ == "__main__":
    print(run())
