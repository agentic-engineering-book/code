"""Experiment 10: LangChain controlled tool-error observations. See framework_examples/README.md."""
from langchain_core.tools import tool
from langchain_core.tools import ToolException


def run():
    @tool
    def divide(denominator: int) -> float:
        """Divide one by a nonzero denominator."""
        if denominator == 0:
            raise ToolException('zero denominator')
        return 1 / denominator
    divide.handle_tool_error = True
    return divide.invoke({'denominator': 0})


if __name__ == "__main__":
    print(run())
