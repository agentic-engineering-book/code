"""Experiment 16 (Chapter 8): Working memory."""
from agentic import calculator
from agentic.live import CALCULATOR_SCHEMA, OpenAIModel

GOAL = "Multiply 27611 by 2033, then add 6."
MAX_STEPS = 4


def run(remember):
    model = OpenAIModel(tools=[CALCULATOR_SCHEMA])
    messages = [{"role": "user", "content": GOAL}]
    for step in range(1, MAX_STEPS + 1):
        decision = model.generate(messages)
        if decision.get("done"):
            return f"answered at step {step}: {decision['answer']}"
        expression = decision["arguments"]["expression"]
        result = calculator(expression)
        print(f"  step {step}: calculator({expression}) = {result}")
        if remember:  # working memory: the call and its result stay
            messages += [{"role": "assistant", "content": decision},
                         {"role": "tool", "content": result}]
    return f"STOPPED by the step limit after {MAX_STEPS} calls"


for label, remember in [("WORKING MEMORY KEPT", True),
                        ("WORKING MEMORY DROPPED", False)]:
    print(label)
    print("  " + run(remember))
