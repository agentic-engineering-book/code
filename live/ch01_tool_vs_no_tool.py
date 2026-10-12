"""Live run, Chapter 1: multiplication with and without a calculator tool."""
import random

from agentic import Agent
from agentic.live import CALCULATOR_SCHEMA, OpenAIModel
from live.common import (arguments, contains_number, parallel, rate, save,
                         usage)

QUESTION = ("Does giving a real model a calculator tool change exact-answer "
            "accuracy on five-digit by four-digit multiplication?")
rng = random.Random(1)
TASKS = [(rng.randint(10000, 99999), rng.randint(1000, 9999))
         for _ in range(20)]


def main():
    model_name = arguments().model
    models = []

    def without_tool(task):
        a, b = task
        model = OpenAIModel(model_name)
        models.append(model)
        answer = model.generate([{
            "role": "user",
            "content": f"What is {a} * {b}? Reply with the exact integer only."
        }])["answer"]
        return {"task": f"{a}*{b}", "answer": answer,
                "correct": contains_number(answer, a * b)}

    def with_tool(task):
        a, b = task
        model = OpenAIModel(model_name, tools=[CALCULATOR_SCHEMA],
                            system="Use the calculator tool for arithmetic.")
        models.append(model)
        answer = Agent(model, max_steps=4).run(f"What is {a} * {b}?")
        return {"task": f"{a}*{b}", "answer": answer,
                "tool_calls": len(model.calls) - 1,
                "correct": contains_number(answer, a * b)}

    plain, tooled = parallel(without_tool, TASKS), parallel(with_tool, TASKS)
    metrics = [rate("Exact answer, model alone", [t["correct"] for t in plain]),
               rate("Exact answer, model + calculator",
                    [t["correct"] for t in tooled]),
               rate("Runs that called the calculator",
                    [t["tool_calls"] > 0 for t in tooled])]
    save("ch01_tool_vs_no_tool", 1, QUESTION, [model_name], metrics,
         {"model_alone": plain, "with_calculator": tooled}, usage(models))


if __name__ == "__main__":
    main()
