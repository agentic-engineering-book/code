"""Experiment 6: Step limit in LangGraph. See framework_examples/README."""
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from framework_examples.support import bounded_loop, chat

MAX_STEPS = 4
GOAL = "Keep checking order 1042 until it has shipped, then tell me."


@tool
def order_status(order_id: str) -> str:
    """Look up the shipping status of an order."""
    return "pending"  # this order never ships


model = chat().bind_tools([order_status],
                         parallel_tool_calls=False)


def step(state):
    decision = model.invoke(state["results"])
    if not decision.tool_calls:
        return {"results": [decision], "value": "answered",
                "step": state["step"] + 1}
    observation = order_status.invoke(decision.tool_calls[0])
    return {"results": [decision, observation], "step": state["step"] + 1}


def stop(state):
    """The application's stopping rule, checked after every step."""
    return state.get("value") is not None or state["step"] >= MAX_STEPS


def trial():
    messages = [
        SystemMessage("Do not reply to the user until the task is complete."),
        HumanMessage(GOAL)]
    state = bounded_loop(step, stop, {"step": 0, "results": messages},
                         limit=2 * MAX_STEPS)
    if state.get("value"):
        return f"model answered after {state['step'] - 1} checks"
    return f"STOPPED by the step limit after {MAX_STEPS} checks"


def run():
    return [f"RUN {n}: {trial()}" for n in range(1, 4)]


if __name__ == "__main__":
    for line in run():
        print(line)
