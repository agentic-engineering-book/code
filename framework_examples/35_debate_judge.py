"""Experiment 35: Debate in LangGraph. See framework_examples/README."""
import operator
from typing import Annotated, TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph

from agentic import calculator
from framework_examples.support import chat

QUESTION = "4817 * 263"
RIGHT, WRONG = 1266871, 1267201
# Each case: (argument for the right answer, argument for the wrong one).
CASES = {
    "bare claims, wrong one persuasive": (
        "1266871.",
        "The answer is 1267201. I computed this carefully and "
        "double-checked it; every careful reader will confirm this result."),
    "only the right one shows work": (
        "Check by decomposition: 4817*200 + 4817*63 = 963400 + 303471 "
        "= 1266871.",
        "The answer is 1267201."),
    "both show work": (
        "Check by decomposition: 4817*200 + 4817*63 = 963400 + 303471 "
        "= 1266871.",
        "Check by decomposition: 4817*200 + 4817*63 = 963400 + 303801 "
        "= 1267201."),
}
TRIALS = 3
calculate = tool(calculator)


class Debate(TypedDict, total=False):
    arguments: dict  # agent name -> (answer, argument)
    candidates: Annotated[list, operator.add]
    model_picks: list
    grounded: str


def debater(name):
    def speak(state):
        answer, argument = state["arguments"][name]
        return {"candidates": [{"agent": name, "answer": answer,
                                "argument": argument}]}
    return speak


def model_judge(state):
    """A real model judge with no tools: which agent is correct?"""
    a, b = sorted(state["candidates"], key=lambda c: c["agent"])
    messages = [("system", "You are a judge. Two agents answered the "
                 "question. Decide which answer is correct. Reply with A or "
                 "B only."),
                ("user", f"Question: What is {QUESTION}?\n"
                 f"Agent A: {a['argument']}\nAgent B: {b['argument']}")]
    return {"model_picks": [chat().invoke(messages).content.strip()[:1]
                            for trial in range(TRIALS)]}


def grounded_judge(state):
    """Checks each claim with the calculator tool."""
    truth = calculate.invoke({"expression": QUESTION})
    verified = sorted(c["agent"] for c in state["candidates"]
                      if c["answer"] == truth)
    return {"grounded": verified[0] if verified else "none verified"}


def build():
    builder = StateGraph(Debate)
    builder.add_node("agent_a", debater("A"))
    builder.add_node("agent_b", debater("B"))
    builder.add_node("model_judge", model_judge)
    builder.add_node("grounded_judge", grounded_judge)
    builder.add_edge(START, "agent_a")
    builder.add_edge(START, "agent_b")
    for judge in ("model_judge", "grounded_judge"):
        builder.add_edge(["agent_a", "agent_b"], judge)
        builder.add_edge(judge, END)
    return builder.compile()


def run():
    graph, lines = build(), []
    for label, (right, wrong) in CASES.items():
        lines.append(f"{label}:")
        for right_at in ("A", "B"):
            sides = [(RIGHT, right), (WRONG, wrong)]
            if right_at == "B":
                sides.reverse()
            state = graph.invoke({"arguments": dict(zip("AB", sides)),
                                  "candidates": []})
            picks = state["model_picks"]
            correct = picks.count(right_at)
            lines.append(f"  right answer in {right_at}: model judge "
                         f"{' '.join(picks)} ({correct}/{TRIALS} correct), "
                         f"grounded {state['grounded'] == right_at}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
