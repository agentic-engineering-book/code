"""Experiment 57: LangChain candidate-policy evaluation. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables import RunnableParallel


def run():
    candidates = RunnableParallel(quick=RunnableLambda(lambda _: .6),
                                  verify=RunnableLambda(lambda _: .9))
    scores = candidates.invoke(None)
    return max(scores, key=scores.get)


if __name__ == "__main__":
    print(run())
