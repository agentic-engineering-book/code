"""Experiment 4: LangChain tool argument validation. See framework_examples/README.md."""
from langchain_core.tools import tool
from pydantic import ValidationError


def run():
    @tool
    def add(a: int, b: int) -> int:
        """Add validated integer arguments."""
        return a + b
    try:
        add.invoke({'a': 'not-an-integer', 'b': 2})
    except ValidationError:
        rejected = True
    return {'valid': add.invoke({'a': 6, 'b': 7}), 'invalid_rejected': rejected}


if __name__ == "__main__":
    print(run())
