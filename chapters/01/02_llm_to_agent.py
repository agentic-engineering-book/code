"""Experiment 2 (Chapter 1): From model to agent."""
from agentic.live import CALCULATOR_SCHEMA, OpenAIModel
from agentic.tools import calculator

model = OpenAIModel(tools=[CALCULATOR_SCHEMA])

messages = [{"role": "user", "content": "What is 27611 * 2033?"}]

decision = model.generate(messages)
result = calculator(**decision["arguments"])

messages.append({"role": "assistant", "content": decision})
messages.append({"role": "tool", "content": str(result)})

final = model.generate(messages)

print("ACTION:", decision["action"], decision["arguments"])
print("OBSERVATION:", result)
print("ANSWER:", final["answer"])
