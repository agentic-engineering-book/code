"""Live run, Chapter 5: tool selection with clear and overlapping descriptions."""
from agentic.live import OpenAIModel
from live.common import SMALL_MODEL, arguments, parallel, rate, save, usage


def schema(name, description, parameter):
    return {"name": name, "description": description, "parameters": {
        "type": "object", "required": [parameter],
        "properties": {parameter: {"type": "string"}}}}


CLEAR = [schema("calculator", "Evaluate an arithmetic expression.", "expression"),
         schema("weather", "Get the current weather or forecast for a city.",
                "city"),
         schema("search", "Search reference documents about a topic.", "query")]
OVERLAPPING = [schema("calculator", "Work things out.", "expression"),
               schema("weather", "Find current information about a place.",
                      "city"),
               schema("search", "Find information about a topic.", "query")]
# The same overlapping descriptions, with the argument-name hint removed.
NO_HINTS = [schema(t["name"], t["description"], "input") for t in OVERLAPPING]
TASKS = [
    ("What is 18 times 7?", "calculator"),
    ("What's 15% of 240?", "calculator"),
    ("Split a 1,260 bill between 7 people.", "calculator"),
    ("How many seconds are in a week?", "calculator"),
    ("Convert 72 inches to feet.", "calculator"),
    ("Is it raining in Pretoria right now?", "weather"),
    ("What will the temperature be in Oslo tomorrow?", "weather"),
    ("Do I need an umbrella in London today?", "weather"),
    ("How windy is it in Cape Town at the moment?", "weather"),
    ("Current humidity in Singapore?", "weather"),
    ("Find information about agent evaluation methods.", "search"),
    ("Who proposed the ReAct prompting method?", "search"),
    ("What is the population of Lisbon?", "search"),
    ("What does the Model Context Protocol standardize?", "search"),
    ("When was the city of Durban founded?", "search"),
    ("Summarize research on retrieval-augmented generation.", "search"),
    ("What is the average annual rainfall in Nairobi?", "search"),
    ("What is the current air quality in Delhi?", "weather"),
    ("Compute the compound growth of 1000 at 5% for 3 years.", "calculator"),
    ("What is the history of the Paris weather service?", "search"),
]


def main():
    model_name = arguments(SMALL_MODEL).model
    models = []

    def run(item, tools):
        task, expected = item
        model = OpenAIModel(model_name, tools=tools, tool_choice="required",
                            system="Choose exactly one tool for the request.")
        models.append(model)
        chosen = model.generate([{"role": "user", "content": task}]).get(
            "action", "none")
        return {"task": task, "expected": expected, "chosen": chosen,
                "correct": chosen == expected}

    clear = parallel(lambda item: run(item, CLEAR), TASKS)
    overlap = parallel(lambda item: run(item, OVERLAPPING), TASKS)
    no_hints = parallel(lambda item: run(item, NO_HINTS), TASKS)
    metrics = [rate("Correct tool, clear descriptions",
                    [r["correct"] for r in clear]),
               rate("Correct tool, overlapping descriptions",
                    [r["correct"] for r in overlap]),
               rate("Correct tool, overlapping, same argument name",
                    [r["correct"] for r in no_hints])]
    save("ch05_tool_selection", 5, (
        "Does making tool descriptions overlap reduce a small model's tool "
        "selection accuracy when the functions themselves are unchanged?"),
        [model_name], metrics, {"clear": clear, "overlapping": overlap,
                                "same_argument_name": no_hints},
        usage(models))


if __name__ == "__main__":
    main()
