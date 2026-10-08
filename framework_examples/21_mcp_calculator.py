"""Experiment 21: LangChain local tool contract corresponding to MCP discovery. See framework_examples/README.md."""
from langchain_core.tools import tool


def run():
    @tool
    def calculator(a: int, b: int) -> int:
        """Multiply two integers."""
        return a * b
    return {'discovered': calculator.name,
            'schema': sorted(calculator.args),
            'result': calculator.invoke({'a': 6, 'b': 7})}


if __name__ == "__main__":
    print(run())
