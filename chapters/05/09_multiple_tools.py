"""Experiment 9 (Chapter 5): Tool selection."""
import re

from agentic.model import PolicyModel

CLEAR = {
    "calculator": "Calculate an arithmetic expression.",
    "weather": "Get the current weather in a city.",
    "search": "Find information about a topic.",
}
OVERLAPPING = {
    "calculator": "Calculate an arithmetic expression.",
    "weather": "Find current information about a city.",
    "search": "Find information about a topic.",
}
TASKS = [
    ("Calculate 18 times 7.", "calculator"),
    ("What is the weather in Pretoria?", "weather"),
    ("Find information about agent evaluation.", "search"),
]
STOP_WORDS = {"a", "an", "the", "is", "in", "what"}


def words(text):
    return set(re.findall(r"[a-z]+", text.lower())) - STOP_WORDS


def policy(messages):
    """Stand-in for a model: pick the tool whose description shares the
    most words with the goal. It sees only the descriptions in context."""
    descriptions, goal = messages[0]["content"], messages[1]["content"]
    scores = {name: len(words(text) & words(goal))
              for name, text in descriptions.items()}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return {"done": True, "answer": "no suitable tool"}
    return {"action": best, "arguments": {}}


model = PolicyModel(policy)

VARIANTS = [("CLEAR", CLEAR), ("OVERLAPPING", OVERLAPPING)]

for label, descriptions in VARIANTS:
    print(label, "DESCRIPTIONS")
    correct = 0
    for goal, expected in TASKS:
        messages = [{"role": "system", "content": descriptions},
                    {"role": "user", "content": goal}]
        chosen = model.generate(messages).get("action", "none")
        correct += chosen == expected
        mark = "ok" if chosen == expected else "WRONG"
        print(f"  {goal:<42} -> {chosen:<10} {mark}")
    print(f"  selection accuracy: {correct}/{len(TASKS)}")
    print()
