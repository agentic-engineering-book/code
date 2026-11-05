"""Experiment 26: Tree search in LangGraph. See framework_examples/README."""
import operator
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from framework_examples.support import chat

START_VALUE, TARGET = 2, 13
OPERATIONS = {"+3": lambda x: x + 3, "*2": lambda x: x * 2,
              "+9": lambda x: x + 9}
PUZZLE = (f"Start at {START_VALUE} and reach exactly {TARGET} using exactly "
          "two operations, each one of +3, *2, +9.")


def ask(question):
    return chat().invoke(question).content.strip()


def verify(path):
    """Exact check: does this sequence of operations reach the target?"""
    value = START_VALUE
    for name in path.split():
        if name not in OPERATIONS:
            return False
        value = OPERATIONS[name](value)
    return value == TARGET


def model_judge(name, value):
    reply = ask(PUZZLE + f" After the first operation {name} the value is "
                f"{value}. With one operation left, can this value become "
                f"exactly {TARGET}? Reply YES or NO only.")
    return reply.upper().startswith("YES")


def exact_judge(name, value):
    return any(op(value) == TARGET for op in OPERATIONS.values())


JUDGES = {"model_judge": model_judge, "exact_judge": exact_judge}


class Tree(TypedDict, total=False):
    judge: str
    kept: Annotated[list, operator.add]
    solutions: list


def expand(state):
    """Fan out: one branch per first move."""
    return [Send("judge", {"judge": state["judge"], "move": name})
            for name in OPERATIONS]


def judge(branch):
    value = OPERATIONS[branch["move"]](START_VALUE)
    keep = JUDGES[branch["judge"]](branch["move"], value)
    return {"kept": [branch["move"]] if keep else []}


def complete(state):
    """Code expands the second move and verifies every full path."""
    paths = [f"{first} {second}" for first in sorted(state["kept"])
             for second in OPERATIONS]
    return {"solutions": [path for path in paths if verify(path)]}


def build():
    builder = StateGraph(Tree)
    builder.add_node("judge", judge)
    builder.add_node("complete", complete)
    builder.add_conditional_edges(START, expand, ["judge"])
    builder.add_edge("judge", "complete")
    builder.add_edge("complete", END)
    return builder.compile()


def run():
    lines = ["ONE PATH: the model answers directly"]
    for trial in range(5):
        answer = ask(PUZZLE + " Reply with the two operations only, "
                     "like '+3 *2'.")
        lines.append(f"  {answer[:20]:8} correct={verify(answer)}")
    lines.append("TREE: Send expands each first move, a judge prunes, "
                 "code verifies")
    graph = build()
    for name in ("model_judge",) * 3 + ("exact_judge",):
        state = graph.invoke({"judge": name, "kept": []})
        lines.append(f"  {name:11} kept={sorted(state['kept'])} "
                     f"solutions={state['solutions']}")
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
