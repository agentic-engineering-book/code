"""Experiment 23: LangChain runnable planning component. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda


def run():
    planner = RunnableLambda(lambda goal: {'goal': goal, 'steps': ['draft', 'review', 'revise', 'publish']})
    return planner.invoke('publish')['steps']


if __name__ == "__main__":
    print(run())
