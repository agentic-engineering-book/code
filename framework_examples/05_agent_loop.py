"""Experiment 5: LangGraph observe-decide-act loop."""
from agentic.tools import calculator
from framework_examples.support import bounded_loop


def policy(observations):
    """Stand-in model: decides only from the observations it has seen."""
    if not observations:
        return {"action": "calculator", "expression": "12*7"}
    if len(observations) == 1:
        return {"action": "calculator",
                "expression": f"{observations[-1]}+6"}
    return {"done": True, "answer": f"The answer is {observations[-1]}."}


def step(state):
    decision = policy(state["results"])
    if decision.get("done"):
        return {"value": decision["answer"], "step": state["step"] + 1}
    observation = calculator(decision["expression"])
    return {"results": [observation], "step": state["step"] + 1}


def run():
    state = bounded_loop(step, lambda s: s.get("value") is not None,
                         {"step": 0, "results": []}, limit=10)
    return {"observations": state["results"], "answer": state["value"],
            "decisions": state["step"]}


if __name__ == "__main__":
    print(run())
