"""Experiment 31: LangChain specialist runnable exposed as a tool. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda
from langchain_core.tools import StructuredTool


def run():
    specialist = RunnableLambda(lambda x: x*x)
    def square(x: int) -> int:
        return specialist.invoke(x)
    delegated = StructuredTool.from_function(square, description='Delegate squaring to a specialist.')
    return delegated.invoke({'x': 9})


if __name__ == "__main__":
    print(run())
