"""Experiment 26 (Chapter 14): Tree reasoning."""
from agentic.live import OpenAIModel

START, TARGET = 2, 13
OPERATIONS = {"+3": lambda x: x + 3, "*2": lambda x: x * 2,
              "+9": lambda x: x + 9}
PUZZLE = (f"Start at {START} and reach exactly {TARGET} using exactly two "
          "operations, each one of +3, *2, +9.")


def ask(question):
    reply = OpenAIModel().generate([{"role": "user", "content": question}])
    return reply["answer"].strip()


def verify(path):
    """Exact check: does this sequence of operations reach the target?"""
    value = START
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
    return any(operation(value) == TARGET for operation in OPERATIONS.values())


print("ONE PATH: the model answers directly")
for trial in range(5):
    answer = ask(PUZZLE + " Reply with the two operations only, like '+3 *2'.")
    print(f"  {answer:8} correct={verify(answer)}")

print("TREE: code expands every first move, a judge prunes, code verifies")
for judge in (model_judge, model_judge, model_judge, exact_judge):
    kept = [name for name, operation in OPERATIONS.items()
            if judge(name, operation(START))]
    solutions = [f"{first} {second}" for first in kept for second in OPERATIONS
                 if verify(f"{first} {second}")]
    print(f"  {judge.__name__:11} kept={kept} solutions={solutions}")
