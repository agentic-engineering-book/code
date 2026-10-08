"""Experiment 12: LangChain context-selection pipeline. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda


def run():
    select = RunnableLambda(lambda items: sorted(items, key=lambda x: x[1], reverse=True)[:1])
    render = RunnableLambda(lambda chosen: chosen[0][0])
    return (select | render).invoke([('relevant', .9), ('noise', .1), ('old', .2)])


if __name__ == "__main__":
    print(run())
