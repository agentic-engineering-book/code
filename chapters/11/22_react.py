"""Experiment 22 (Chapter 11): ReAct as feedback control."""
import textwrap

from agentic import calculator, execute
from agentic.live import CALCULATOR_SCHEMA, OpenAIModel, schema

GOAL = "Find the current price of item A17, then add 15% VAT."
PRICES = {"A17": 80}  # the environment: only a lookup can reveal it


def lookup_price(item):
    return PRICES[item]


TOOLS = {"lookup_price": lookup_price, "calculator": calculator}
SCHEMAS = [schema("lookup_price", "Look up the current price of an item.",
                  item="the item code"), CALCULATOR_SCHEMA]


def show(label, text):
    print(textwrap.fill(" ".join(text.split()), 76,
                        initial_indent=f"STEP {label} ",
                        subsequent_indent="    "))


def run(model, feed_back=True, max_steps=4):
    messages = [{"role": "user", "content": GOAL}]
    for step in range(1, max_steps + 1):
        decision = model.generate(messages)
        if decision.get("done"):
            return show(f"{step} DONE:", decision["answer"])
        observation = execute(decision, tools=TOOLS)
        print(f"STEP {step} ACTION: {decision['action']}"
              f"({decision['arguments']}) OBSERVATION: {observation}")
        if feed_back:
            messages += [{"role": "assistant", "content": decision},
                         {"role": "tool", "content": str(observation)}]
    print(f"STOPPED: step limit after {len(model.calls)} model calls")


print("== One-shot: no tools, so the price is not observable ==")
run(OpenAIModel(system="Answer in at most two sentences."))

print("== ReAct: each observation is appended to the messages ==")
run(OpenAIModel(tools=SCHEMAS))

print("== BREAK: the lookup runs but its result is never fed back ==")
run(OpenAIModel(tools=SCHEMAS), feed_back=False)
