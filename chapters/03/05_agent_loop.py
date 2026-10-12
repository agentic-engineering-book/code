"""Experiment 5 (Chapter 3): The smallest agent loop."""
from agentic.model import PolicyModel
from agentic.tools import execute


def policy(messages):
    """Stand-in for a model: multiply, add 6 to what it observed, finish.
    It decides from the observations in its context, nothing else."""
    observations = [m["content"] for m in messages if m["role"] == "tool"]
    if not observations:
        expression = "12*7"
    elif len(observations) == 1:
        expression = observations[-1] + "+6"
    else:
        return {"done": True,
                "answer": f"The answer is {observations[-1]}."}
    return {"done": False,
            "action": "calculator",
            "arguments": {"expression": expression}}


model = PolicyModel(policy)

messages = [
    {"role": "user",
     "content": "Multiply 12 by 7, then add 6."}
]

for step in range(1, 11):
    decision = model.generate(messages)
    print("STEP", step)

    if decision["done"]:
        print("DONE:", decision["answer"])
        break

    expression = decision["arguments"]["expression"]
    print(f'ACTION: calculator("{expression}")')
    observation = execute(decision)
    print("OBSERVATION:", observation)
    print()

    messages.append({
        "role": "tool",
        "content": str(observation)
    })
