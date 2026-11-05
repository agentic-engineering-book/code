"""Experiment 39 (Chapter 22): Trajectory evaluation."""
from agentic import calculator, execute
from agentic.live import CALCULATOR_SCHEMA, OpenAIModel, schema

GOAL = "What does item A17 cost including 15% VAT, according to our catalog?"
TOOLS = {
    "search": lambda query: "Web result: item A17 listed at around 75-85 "
                            "dollars by resellers.",
    "retrieve": lambda key: "Catalog: item A17 costs 80 dollars."
                            if "A17" in key else "not found",
    "weather": lambda city: "Sunny, 24 C.",
    "calculator": calculator,
}
SCHEMAS = [schema("search", "Search the web.", query="search terms"),
           schema("retrieve", "Retrieve a record from the company catalog.",
                  key="the item code"),
           schema("weather", "Current weather for a city.", city="the city"),
           CALCULATOR_SCHEMA]
AUTHORIZED_TOOLS = {"search", "retrieve", "calculator"}
RELEVANT_TOOLS = {"retrieve", "calculator"}
REFERENCE_PATH = ["retrieve", "calculator"]
MAX_STEPS = 6


def run_agent(model_name):
    """Run a real agent and record its trajectory."""
    model = OpenAIModel(model_name, tools=SCHEMAS)
    messages, trace = [{"role": "user", "content": GOAL}], []
    for step in range(MAX_STEPS):
        decision = model.generate(messages)
        if decision.get("done"):
            return trace + [("answer", decision["answer"])]
        trace.append(("tool", decision["action"], decision["arguments"]))
        observation = execute(decision, tools=TOOLS)
        messages += [{"role": "assistant", "content": decision},
                     {"role": "tool", "content": str(observation)}]
    return trace + [("answer", None)]


def tools(trace):
    return [step[1] for step in trace if step[0] == "tool"]


def reference_match(trace):
    return tools(trace) == REFERENCE_PATH


def trajectory_checks(trace):
    used = tools(trace)
    return {
        "required_tool": "calculator" in used,
        "irrelevant": sum(t not in RELEVANT_TOOLS for t in used),
        "unauthorized": sum(t not in AUTHORIZED_TOOLS for t in used),
        "within_limit": len(trace) <= MAX_STEPS,
    }


for name in ["gpt-5.4-mini-2026-03-17", "gpt-5.4-nano-2026-03-17"]:
    trace = run_agent(name)
    correct = "92" in (trace[-1][1] or "")
    print(f"{name}: tools={tools(trace)}")
    print(f"    answer_correct={correct} "
          f"reference_match={reference_match(trace)}")
    print("   ", " ".join(f"{key}={value}"
                         for key, value in trajectory_checks(trace).items()))
