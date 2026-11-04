"""Experiment 8 (Chapter 5): One tool."""
from agentic.live import CALCULATOR_SCHEMA, OpenAIModel
from agentic.tools import calculator

# The registry: software's source of truth about what can execute.
tools = {
    "calculator": calculator
}

# The description: what the model is told about the tool.
model = OpenAIModel(tools=[CALCULATOR_SCHEMA])

question = "What is 27611 times 2033?"
decision = model.generate([{"role": "user", "content": question}])

tool = tools[decision["action"]]
result = tool(**decision["arguments"])

print("ACTION:", decision["action"], decision["arguments"])
print("RESULT:", result)
