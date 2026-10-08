"""Experiment 8: LangChain tool schema and invocation. See framework_examples/README.md."""
from langchain_core.tools import tool


def run():
    @tool
    def add(a: int, b: int) -> int:
        """Add two integers."""
        return a + b
    return add.invoke({'a': 2, 'b': 3})


if __name__ == "__main__":
    print(run())
