"""Experiment 2 (Chapter 1): From model to agent."""
from agentic.model import PolicyModel, last_observation
from agentic.tools import calculator


def policy(messages):
    """Stand-in for a model: request the calculator, then answer
    from the observation. Without an observation it asks again."""
    observation = last_observation(messages)
    if observation is None:
        return {
            "action": "calculator",
            "arguments": {"expression": "37*42"}
        }
    return {"done": True, "answer": f"37 x 42 = {observation}."}


model = PolicyModel(policy)

messages = [
    {"role": "user", "content": "What is 37 * 42?"}
]

decision = model.generate(messages)
result = calculator(**decision["arguments"])

messages.append({
    "role": "tool",
    "content": str(result)
})

final = model.generate(messages)

print("ACTION:", decision["action"])
print("OBSERVATION:", result)
print("ANSWER:", final["answer"])
