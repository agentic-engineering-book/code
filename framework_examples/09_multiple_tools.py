"""Experiment 9: Tool selection in LangChain. See framework_examples/README."""
from langchain_core.tools import StructuredTool

from framework_examples.support import chat


def search(query: str) -> str:
    """Never run here: the experiment only measures the model's choice."""
    return ""


def search_tools(docs_name, docs_text, web_name, web_text):
    """Two search tools: the company's documents first, then the web."""
    return [StructuredTool.from_function(search, name=name, description=text)
            for name, text in [(docs_name, docs_text), (web_name, web_text)]]


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


def run():
    lines = []
    for label, tools in VARIANTS.items():
        # tool_choice="required": the model must pick one of the tools.
        model = chat().bind_tools(tools, tool_choice="required")
        lines.append(label)
        correct = 0
        for goal, expected in TASKS:
            chosen = model.invoke(goal).tool_calls[0]["name"]
            right = chosen == tools[expected].name
            correct += right
            mark = "ok" if right else "WRONG"
            lines.append(f"  {goal:<46} -> {chosen:<11} {mark}")
        lines += [f"  selection accuracy: {correct}/{len(TASKS)}", ""]
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
