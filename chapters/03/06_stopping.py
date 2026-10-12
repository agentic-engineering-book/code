"""Experiment 6 (Chapter 3): The agent that never finishes."""
from agentic.model import ScriptedModel
from agentic.tools import execute

MAX_STEPS = 3

# One scripted response, repeated forever: every decision is valid,
# every tool call succeeds, and no decision ever finishes the task.
model = ScriptedModel([{
    "done": False,
    "action": "calculator",
    "arguments": {"expression": "1+1"}
}])


def run(messages):
    for step in range(1, MAX_STEPS + 1):
        decision = model.generate(messages)

        if decision["done"]:
            return decision["answer"]

        observation = execute(decision)
        expression = decision["arguments"]["expression"]
        print(f'STEP {step}: calculator("{expression}") -> {observation}')
        messages.append({"role": "tool", "content": str(observation)})

    raise RuntimeError("Step limit reached")


try:
    run([{"role": "user", "content": "Add 1 and 1."}])
except RuntimeError as error:
    print("STOP:", error)
