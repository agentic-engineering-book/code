"""Experiment 19: LangChain compression stage. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda


def run():
    compress = RunnableLambda(lambda history: history[:80])
    observe = RunnableLambda(lambda summary: {'summary': summary, 'characters': len(summary)})
    return (compress | observe).invoke('observation ' * 40)['characters']


if __name__ == "__main__":
    print(run())
