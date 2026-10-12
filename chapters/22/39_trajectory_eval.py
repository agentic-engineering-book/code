"""Experiment 39 (Chapter 22): Trajectory evaluation."""
AUTHORIZED_TOOLS = {"search", "retrieve", "calculator"}
RELEVANT_TOOLS = {"retrieve", "calculator"}
REFERENCE_PATH = ["retrieve", "calculator"]
MAX_STEPS = 6

TRAJECTORIES = {
    "wasteful": [("tool", "search", "17 * 6"),
                 ("tool", "weather", "Pretoria"),
                 ("tool", "calculator", "17 * 6"),
                 ("answer", 102)],
    "direct": [("tool", "calculator", "17 * 6"),
               ("answer", 102)],
}


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


for name, trace in TRAJECTORIES.items():
    answer = trace[-1][1]
    print(f"{name}: answer={answer} reference_match={reference_match(trace)}")
    checks = trajectory_checks(trace)
    print("   ", " ".join(f"{key}={value}" for key, value in checks.items()))
