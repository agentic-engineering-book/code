"""Experiment 9 (Chapter 5): Tool selection."""
from agentic.live import OpenAIModel, schema


def search_tools(docs_name, docs_text, web_name, web_text):
    """Two search tools: the company's documents first, then the web."""
    return [schema(docs_name, docs_text, query="what to search for"),
            schema(web_name, web_text, query="what to search for")]


VARIANTS = {
    "CLEAR": search_tools(
        "search_docs", "Search the company's internal documents: "
                       "policies, HR rules and expense rules.",
        "search_web", "Search the public web for general knowledge."),
    "SAME DESCRIPTIONS, VAGUE NAMES": search_tools(
        "search_a", "Search for information.",
        "search_b", "Search for information."),
}
DOCS, WEB = 0, 1
TASKS = [
    ("What is our travel expense limit per night?", DOCS),
    ("How many vacation days do new employees get?", DOCS),
    ("Who approves overtime in our company?", DOCS),
    ("Who won the 2022 football World Cup?", WEB),
    ("What is the population of Brazil?", WEB),
    ("When was the telephone invented?", WEB),
]

for label, tools in VARIANTS.items():
    # tool_choice="required": the model must pick one of the tools.
    model = OpenAIModel(tools=tools, tool_choice="required")
    print(label)
    correct = 0
    for goal, expected in TASKS:
        messages = [{"role": "user", "content": goal}]
        chosen = model.generate(messages)["action"]
        right = chosen == tools[expected]["name"]
        correct += right
        print(f"  {goal:<46} -> {chosen:<11} {'ok' if right else 'WRONG'}")
    print(f"  selection accuracy: {correct}/{len(TASKS)}")
    print()
