"""Live run, Chapter 15: a cheap-first cascade with an agreement check."""
import json

from agentic.live import OpenAIModel
from agentic.tools import calculator
from live.common import MODEL, SMALL_MODEL, parallel, rate, save, usage
from live.problems import problems

QUESTION = ("Can a cascade that asks a small model twice, and escalates to a "
            "larger model only when the two answers disagree, match the "
            "larger model's accuracy while sending it fewer requests?")
TASKS = problems(30, seed=15)
SCHEMA = {"type": "json_schema", "json_schema": {
    "name": "worked_answer", "strict": True, "schema": {
        "type": "object", "additionalProperties": False,
        "required": ["expression", "answer"],
        "properties": {"expression": {"type": "string"},
                       "answer": {"type": "number"}}}}}
SYSTEM = ("Solve the problem. Give one arithmetic expression (numbers, "
          "+ - * / and parentheses) that computes the answer, and the answer.")


def solve(model_name, models, problem):
    """The model writes the expression; the calculator does the arithmetic."""
    model = OpenAIModel(model_name, system=SYSTEM, response_format=SCHEMA)
    models.append(model)
    data = json.loads(model.generate(
        [{"role": "user", "content": problem}])["answer"])
    try:
        value = calculator(data["expression"])
    except ValueError:
        value = None
    stated_matches = value is not None and abs(value - data["answer"]) < 1e-6
    return {"value": value, "stated": data["answer"],
            "stated_matches_expression": stated_matches}


def near(value, truth):
    return value is not None and abs(value - truth) < 1e-6


def main():
    models = []
    small_a = parallel(lambda t: solve(SMALL_MODEL, models, t[0]), TASKS)
    small_b = parallel(lambda t: solve(SMALL_MODEL, models, t[0]), TASKS)
    large = parallel(lambda t: solve(MODEL, models, t[0]), TASKS)
    rows = []
    for (problem, truth), a, b, big in zip(TASKS, small_a, small_b, large):
        agree = a["value"] is not None and near(a["value"], b["value"])
        final = a["value"] if agree else big["value"]
        rows.append({"problem": problem, "expected": truth, "small_a": a,
                     "small_b": b, "large": big, "escalated": not agree,
                     "small_correct": near(a["value"], truth),
                     "large_correct": near(big["value"], truth),
                     "cascade_correct": near(final, truth),
                     "agreed_but_wrong": agree and not near(a["value"], truth)})
    stated = [r[k]["stated_matches_expression"] for r in rows
              for k in ("small_a", "small_b")]
    metrics = [rate("Correct, small model only",
                    [r["small_correct"] for r in rows]),
               rate("Correct, large model only",
                    [r["large_correct"] for r in rows]),
               rate("Correct, cascade", [r["cascade_correct"] for r in rows]),
               rate("Escalated to large model", [r["escalated"] for r in rows]),
               rate("Small samples agreed but were wrong",
                    [r["agreed_but_wrong"] for r in rows]),
               rate("Small model's stated number matched its own expression",
                    stated),
               rate("Large model's stated number matched its own expression",
                    [r["large"]["stated_matches_expression"] for r in rows])]
    save("ch15_cascade", 15, QUESTION, [SMALL_MODEL, MODEL], metrics, rows,
         usage(models), notes=(
             "Values are computed by the calculator from each model's "
             "expression. A first version accepted the model's stated "
             "number; both models stated wrong numbers for correct "
             "expressions, so that design escalated everything."))


if __name__ == "__main__":
    main()
