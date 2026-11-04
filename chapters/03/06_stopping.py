"""Experiment 6 (Chapter 3): The agent that never finishes."""
from agentic.live import OpenAIModel
from agentic.tools import execute

MAX_STEPS = 4

STATUS_SCHEMA = {
    "name": "order_status",
    "description": "Look up the shipping status of an order.",
    "parameters": {
        "type": "object",
        "properties": {"order_id": {"type": "string"}},
        "required": ["order_id"],
    },
}


def order_status(order_id):
    return "pending"  # this order never ships


model = OpenAIModel(tools=[STATUS_SCHEMA], system=(
    "Do not reply to the user until the task is complete."))
tools = {"order_status": order_status}


def run(goal):
    messages = [{"role": "user", "content": goal}]

    for step in range(1, MAX_STEPS + 1):
        decision = model.generate(messages)
        messages.append({"role": "assistant", "content": decision})

        if decision.get("done"):
            return f"model answered after {step - 1} checks"

        observation = execute(decision, tools=tools)
        messages.append({"role": "tool", "content": str(observation)})

    return f"STOPPED by the step limit after {MAX_STEPS} checks"


goal = "Keep checking order 1042 until it has shipped, then tell me."
for trial in range(1, 6):
    print(f"RUN {trial}:", run(goal))
