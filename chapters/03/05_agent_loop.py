"""Experiment 5 (Chapter 3): The smallest agent loop."""
from agentic.live import CALCULATOR_SCHEMA, OpenAIModel
from agentic.tools import execute

model = OpenAIModel(tools=[CALCULATOR_SCHEMA])

goal = ("Multiply 27611 by 2033. If the result is even, add 6; "
        "otherwise subtract 6.")
messages = [{"role": "user", "content": goal}]

for step in range(1, 11):
    decision = model.generate(messages)
    messages.append({"role": "assistant", "content": decision})
    print("STEP", step)

    if decision.get("done"):
        print("DONE:", decision["answer"])
        break

    print("ACTION:", decision["action"], decision["arguments"])
    observation = execute(decision)
    print("OBSERVATION:", observation)
    print()

    messages.append({"role": "tool", "content": str(observation)})
