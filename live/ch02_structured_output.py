"""Live run, Chapter 2: prompted JSON versus strict JSON Schema output."""
import json

from agentic.live import OpenAIModel
from agentic.tools import calculator
from live.common import SMALL_MODEL, arguments, parallel, rate, save, usage

QUESTION = ("How often does a small model's decision parse, match the schema, "
            "and compute the right value when JSON is requested in the prompt "
            "versus enforced with a strict JSON Schema?")
TASKS = [
    ("Work out 37 times 42.", 1554), ("Add 18 and 7, then multiply by 3.", 75),
    ("What is 12 squared minus 5?", 139), ("Divide 144 by 12.", 12),
    ("Take 15% of 80.", 12), ("What is 2 to the power 10?", 1024),
    ("Subtract 999 from 1234.", 235), ("Half of 86, plus 7.", 50),
    ("Three dozen eggs: how many eggs?", 36), ("What is 7 * 8 * 9?", 504),
    ("Average of 10, 20 and 60?", 30), ("1000 minus 7, times 2.", 1986),
    ("How many minutes are in 3.5 hours?", 210),
    ("Twelve and a half percent of 640?", 80),
    ("Product of 25 and 16?", 400), ("19 plus 23 plus 58?", 100),
    ("What is 81 divided by 9, squared?", 81),
    ("Five times the sum of 3 and 4?", 35), ("One third of 297?", 99),
    ("A dozen boxes of 24 items: how many items?", 288),
]
INSTRUCTION = ('Return a calculator decision as JSON: {"action": "calculator", '
               '"arguments": {"expression": "<arithmetic expression>"}}. '
               'The expression may use + - * / ** and parentheses only.')
SCHEMA = {"type": "json_schema", "json_schema": {
    "name": "calculator_decision", "strict": True, "schema": {
        "type": "object", "additionalProperties": False,
        "required": ["action", "arguments"],
        "properties": {
            "action": {"type": "string", "enum": ["calculator"]},
            "arguments": {"type": "object", "additionalProperties": False,
                          "required": ["expression"],
                          "properties": {"expression": {"type": "string"}}}}}}}


def check(text, expected):
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"parsed": False, "valid": False, "correct": False}
    valid = (isinstance(data, dict) and set(data) == {"action", "arguments"}
             and data["action"] == "calculator"
             and isinstance(data["arguments"], dict)
             and set(data["arguments"]) == {"expression"}
             and isinstance(data["arguments"]["expression"], str))
    try:
        value = calculator(data["arguments"]["expression"]) if valid else None
    except ValueError:
        value = None
    correct = value is not None and abs(value - expected) < 1e-9
    return {"parsed": True, "valid": valid, "correct": correct}


def main():
    model_name = arguments(SMALL_MODEL).model
    models = []

    def run(item, strict):
        task, expected = item
        settings = {"response_format": SCHEMA} if strict else {}
        model = OpenAIModel(model_name, system=INSTRUCTION, **settings)
        models.append(model)
        text = model.generate([{"role": "user", "content": task}])["answer"]
        return {"task": task, "output": text, **check(text, expected)}

    prompted = parallel(lambda item: run(item, False), TASKS)
    strict = parallel(lambda item: run(item, True), TASKS)
    metrics = []
    for label, rows in [("prompted", prompted), ("strict schema", strict)]:
        for key, name in [("parsed", "parses"), ("valid", "schema-valid"),
                          ("correct", "computes the right value")]:
            metrics.append(rate(f"{name.capitalize()}, {label}",
                                [row[key] for row in rows]))
    save("ch02_structured_output", 2, QUESTION, [model_name], metrics,
         {"prompted": prompted, "strict": strict}, usage(models))


if __name__ == "__main__":
    main()
