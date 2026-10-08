"""Experiment 29: LangChain parallel runnable execution. See framework_examples/README.md."""
from langchain_core.runnables import RunnableParallel, RunnableLambda


def run():
    workers = RunnableParallel(**{str(x): RunnableLambda(lambda _, x=x: x*x) for x in [2, 3, 4]})
    result = workers.invoke(None)
    return [result[str(x)] for x in [2, 3, 4]]


if __name__ == "__main__":
    print(run())
