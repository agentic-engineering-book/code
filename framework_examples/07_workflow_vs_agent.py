"""Experiment 7: Fixed LangChain composition versus LangGraph conditional routing. See framework_examples/README.md."""
from langchain_core.runnables import RunnableLambda
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    workflow = RunnableLambda(lambda x: x * 2)
    choice = branch({'double': lambda s: {'value': s['value'] * 2},
                     'square': lambda s: {'value': s['value'] ** 2}},
                    lambda s: 'double' if s['value'] < 10 else 'square', 12)
    return [workflow.invoke(4), choice]


if __name__ == "__main__":
    print(run())
