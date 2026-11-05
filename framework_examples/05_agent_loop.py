"""Experiment 5: Agent loop in LangGraph. See framework_examples/README."""
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool

from agentic.tools import calculator as evaluate
from framework_examples.support import bounded_loop, chat

GOAL = ("Multiply 27611 by 2033. If the result is even, add 6; "
        "otherwise subtract 6.")


@tool
def calculator(expression: str) -> float:
    """Evaluate an arithmetic expression exactly. Supports + - * / **."""
    return evaluate(expression)


model = chat().bind_tools([calculator], parallel_tool_calls=False)


def step(state):
    """One turn: the model decides; software runs the tool it names."""
    decision = model.invoke(state["results"])
    if not decision.tool_calls:
        return {"results": [decision], "value": decision.content,
                "step": state["step"] + 1}
    observation = calculator.invoke(decision.tool_calls[0])
    return {"results": [decision, observation], "step": state["step"] + 1}


def run():
    state = bounded_loop(
        step, lambda s: s.get("value") is not None or s["step"] >= 10,
        {"step": 0, "results": [HumanMessage(content=GOAL)]}, limit=25)
    lines = []
    for message in state["results"][1:]:
        if message.type == "ai" and message.tool_calls:
            call = message.tool_calls[0]
            lines.append(f"ACTION: {call['name']} {call['args']}")
        elif message.type == "tool":
            lines.append(f"OBSERVATION: {message.content}")
        else:
            lines.append("DONE: " + " ".join(message.content.split())[:70])
    return lines + [f"MODEL CALLS: {state['step']}"]


if __name__ == "__main__":
    for line in run():
        print(line)
