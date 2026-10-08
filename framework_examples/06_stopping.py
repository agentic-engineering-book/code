"""Experiment 6: LangGraph recursion ceiling. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop
from langgraph.errors import GraphRecursionError


def run():
    try:
        bounded_loop(lambda s: {'step': s['step'] + 1},
                     lambda s: False, {'step': 0}, limit=3)
    except GraphRecursionError:
        return 'stopped by framework recursion ceiling'


if __name__ == "__main__":
    print(run())
