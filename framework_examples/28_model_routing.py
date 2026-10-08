"""Experiment 28: LangChain model-selection branch. See framework_examples/README.md."""
from langchain_core.runnables import RunnableBranch, RunnableLambda


def run():
    router = RunnableBranch((lambda difficulty: difficulty > .6,
                             RunnableLambda(lambda x: 'strong')),
                            RunnableLambda(lambda x: 'cheap'))
    return router.invoke(.8)


if __name__ == "__main__":
    print(run())
