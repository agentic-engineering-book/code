"""Experiment 38: LangChain composable exact-match evaluation. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda


def run():
    answer = RunnableLambda(lambda question: '42')
    evaluate = RunnableLambda(lambda output: {'correct': output == '42'})
    return (answer | evaluate).invoke('6*7?')['correct']


if __name__ == "__main__":
    print(run())
