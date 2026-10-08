"""Experiment 59: LangChain composition of reward-scored policy candidates. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables import RunnableParallel


def run():
    reward = lambda correct, cost: correct - .1 * cost
    policies = RunnableParallel(long=RunnableLambda(lambda _: reward(1, 5)),
                                short=RunnableLambda(lambda _: reward(.9, 1)))
    scores = policies.invoke(None)
    return {'selected': max(scores, key=scores.get), 'scores': scores}


if __name__ == "__main__":
    print(run())
