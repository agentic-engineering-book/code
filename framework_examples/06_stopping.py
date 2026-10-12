"""Experiment 6: Application step limit plus framework ceiling."""
from langgraph.errors import GraphRecursionError

from agentic.tools import calculator
from framework_examples.support import bounded_loop


def repeat_forever(state):
    # The same valid action every time: no progress toward done.
    return {"step": state["step"] + 1, "results": [calculator("1+1")]}


def run():
    # Primary control: the application's own step limit.
    state = bounded_loop(repeat_forever, lambda s: s["step"] >= 3,
                         {"step": 0, "results": []}, limit=25)
    # Backstop: with no application rule, LangGraph's recursion limit
    # still ends the run, but as an exception rather than a policy.
    try:
        bounded_loop(repeat_forever, lambda s: False,
                     {"step": 0, "results": []}, limit=5)
        backstop = "not reached"
    except GraphRecursionError:
        backstop = "GraphRecursionError"
    return {"application_limit_steps": state["step"],
            "observations": state["results"], "without_limit": backstop}


if __name__ == "__main__":
    print(run())
