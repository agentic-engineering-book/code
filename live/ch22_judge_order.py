"""Live run, Chapter 22: does an LLM judge's verdict depend on answer order?"""
from agentic.live import OpenAIModel
from live.common import MODEL, arguments, parallel, rate, save, usage
from live.problems import problems

QUESTION = ("When the same two answers are shown in both orders, how often "
            "does an LLM judge pick the correct one, and how often does its "
            "verdict change with the order?")
TASKS = problems(20, seed=22)
SYSTEM = ("You are grading two candidate answers to a problem. Reply with "
          "exactly one letter, A or B, for the better answer.")


def candidates(problem, truth):
    right = f"The answer is {truth}."
    wrong = f"The answer is {truth + max(1, round(truth * 0.07))}."
    return right, wrong


def main():
    model_name = arguments(MODEL).model
    models = []

    def judge(item):
        (problem, truth), right_first = item
        right, wrong = candidates(problem, truth)
        a, b = (right, wrong) if right_first else (wrong, right)
        model = OpenAIModel(model_name, system=SYSTEM)
        models.append(model)
        verdict = model.generate([{"role": "user", "content": (
            f"Problem: {problem}\n\nAnswer A: {a}\nAnswer B: {b}")}])["answer"]
        letter = verdict.strip()[:1].upper()
        picked_right = letter == ("A" if right_first else "B")
        return {"problem": problem, "right_first": right_first,
                "verdict": verdict.strip()[:20], "picked_right": picked_right,
                "picked_first": letter == "A"}

    rows = parallel(judge, [(t, order) for t in TASKS for order in (True, False)])
    pairs = [rows[i:i + 2] for i in range(0, len(rows), 2)]
    metrics = [rate("Picked the correct answer (all verdicts)",
                    [r["picked_right"] for r in rows]),
               rate("Same correct verdict in both orders",
                    [p[0]["picked_right"] and p[1]["picked_right"]
                     for p in pairs]),
               rate("Verdict flipped with the order",
                    [p[0]["picked_right"] != p[1]["picked_right"]
                     for p in pairs]),
               rate("Chose position A", [r["picked_first"] for r in rows])]
    save("ch22_judge_order", 22, QUESTION, [model_name], metrics, rows,
         usage(models), notes=("Wrong answers are the true answer plus about "
                               "7%; the judge sees no worked solution."))


if __name__ == "__main__":
    main()
