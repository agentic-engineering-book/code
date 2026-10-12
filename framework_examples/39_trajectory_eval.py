"""Experiment 39: LangGraph trajectory recorded by a reducer, checked by
invariants rather than one reference path."""
from framework_examples.support import sequence

AUTHORIZED_TOOLS = {"search", "retrieve", "calculator"}
RELEVANT_TOOLS = {"retrieve", "calculator"}
MAX_STEPS = 6


def tool_node(name):
    return name, lambda state: {"results": [name]}


def invariants(path):
    return {"required_tool": "calculator" in path,
            "irrelevant": sum(t not in RELEVANT_TOOLS for t in path),
            "unauthorized": sum(t not in AUTHORIZED_TOOLS for t in path),
            "within_limit": len(path) <= MAX_STEPS}


def run():
    paths = {"wasteful": ["search", "weather", "calculator"],
             "direct": ["calculator"]}
    report = {}
    for label, tools in paths.items():
        state = sequence([tool_node(t) for t in tools], {"results": []})
        report[label] = invariants(state["results"])
    return report


if __name__ == "__main__":
    print(run())
