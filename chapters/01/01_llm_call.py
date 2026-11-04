"""Experiment 1 (Chapter 1): A model call."""
from agentic.live import OpenAIModel

model = OpenAIModel()

question = "What is 27611 * 2033? Reply with the number only."
messages = [{"role": "user", "content": question}]

answer = model.generate(messages)["answer"]

print("MODEL:", answer)
print("GROUND TRUTH:", 27611 * 2033)
print("CORRECT:", str(27611 * 2033) in answer.replace(",", ""))
