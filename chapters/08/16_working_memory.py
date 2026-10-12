"""Experiment 16 (Chapter 8): Working memory."""
from agentic import calculator

state = {
    "goal": "Multiply 12 by 7, then add 6",
    "observations": []
}

state["observations"].append({
    "expression": "12*7",
    "result": calculator("12*7")
})

print(state["observations"][-1]["result"])


def product_from(state):
    """The second step needs the first step's result."""
    for observation in state["observations"]:
        if observation.get("expression") == "12*7":
            return observation["result"]
    return None


product = product_from(state)
state["observations"].append({
    "expression": f"{product}+6",
    "result": calculator(f"{product}+6")
})
print("FINAL:", state["observations"][-1]["result"])

# Break it: replace the state instead of accumulating it.
state["observations"] = [{"result": 90}]
print("12*7 still available?", product_from(state) is not None)
