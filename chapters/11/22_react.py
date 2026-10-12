"""Experiment 22 (Chapter 11): ReAct as feedback control."""
from agentic import PolicyModel, ScriptedModel, calculator, execute

GOAL = "Find the current value of X, then calculate X * 1.15."
ENVIRONMENT = {"X": 80}


def lookup(key):
    return ENVIRONMENT[key]


TOOLS = {"lookup": lookup, "calculator": calculator}


def react_policy(messages):
    """Stand-in model: its next decision depends on what it has observed."""
    seen = [m["content"] for m in messages if m["role"] == "tool"]
    if not seen:
        return {"action": "lookup", "arguments": {"key": "X"}}
    if len(seen) == 1:
        expression = f"{seen[0]} * 1.15"
        return {"action": "calculator",
                "arguments": {"expression": expression}}
    return {"done": True, "answer": seen[-1]}


def run(model, feed_back=True, max_steps=4):
    messages = [{"role": "user", "content": GOAL}]
    for step in range(1, max_steps + 1):
        decision = model.generate(messages)
        messages.append({"role": "assistant", "content": decision})
        if decision.get("done"):
            print(f"STEP {step} DONE: {decision['answer']}")
            return decision["answer"]
        observation = execute(decision, tools=TOOLS)
        print(f"STEP {step} ACTION: {decision['action']}"
              f"({decision['arguments']}) OBSERVATION: {observation}")
        if feed_back:
            messages.append({"role": "tool", "content": str(observation)})
    print(f"STOPPED: step limit after {model.calls} model calls")
    return None


print("== One-shot: no tools, so X must be guessed (here X = 100) ==")
run(ScriptedModel([{"done": True, "answer": "115.0"}]))

print("== ReAct: each observation is appended to the messages ==")
run(PolicyModel(react_policy))

print("== BREAK: the lookup runs but its result is never fed back ==")
run(PolicyModel(react_policy), feed_back=False)
