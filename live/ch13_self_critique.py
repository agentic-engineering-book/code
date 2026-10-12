"""Live run, Chapter 13: intrinsic self-critique without external feedback."""
from agentic.live import OpenAIModel
from live.common import (SMALL_MODEL, arguments, numbers_in, parallel, rate,
                         save, usage)
from live.problems import problems

QUESTION = ("When a small model reviews its own answer without any external "
            "check, how often does it fix a wrong answer, and how often does "
            "it break a right one?")
TASKS = problems(30, seed=13)
FORMAT = " End with a line 'FINAL: <integer>'."


def final(text):
    tail = text.rsplit("FINAL:", 1)[-1] if "FINAL:" in text else text
    values = numbers_in(tail)
    return values[-1] if values else None


def main():
    model_name = arguments(SMALL_MODEL).model
    models = []

    def run(item):
        problem, answer = item
        model = OpenAIModel(model_name)
        models.append(model)
        messages = [{"role": "user", "content": problem + FORMAT}]
        first = model.generate(messages)["answer"]
        messages += [{"role": "assistant", "content": {"answer": first}},
                     {"role": "user", "content": (
                         "Review your answer carefully for mistakes. If it is "
                         "wrong, correct it; if it is right, keep it." + FORMAT)}]
        second = model.generate(messages)["answer"]
        before, after = final(first) == answer, final(second) == answer
        return {"problem": problem, "expected": answer, "first": final(first),
                "revised": final(second), "before": before, "after": after}

    rows = parallel(run, TASKS)
    metrics = [rate("Correct before review", [r["before"] for r in rows]),
               rate("Correct after review", [r["after"] for r in rows]),
               rate("Wrong to right (repaired)",
                    [not r["before"] and r["after"] for r in rows]),
               rate("Right to wrong (regressed)",
                    [r["before"] and not r["after"] for r in rows])]
    save("ch13_self_critique", 13, QUESTION, [model_name], metrics, rows,
         usage(models))


if __name__ == "__main__":
    main()
