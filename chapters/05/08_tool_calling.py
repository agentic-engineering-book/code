"""Experiment 8 (Chapter 5): One tool."""
from agentic.tools import calculator

# The registry: software's source of truth about what can execute.
tools = {
    "calculator": calculator
}

# The model's proposal. Here it is fixed; a live model would supply it.
decision = {
    "action": "calculator",
    "arguments": {
        "expression": "18*7"
    }
}

tool = tools[decision["action"]]
result = tool(**decision["arguments"])

print("ACTION:", decision["action"])
print("RESULT:", result)
