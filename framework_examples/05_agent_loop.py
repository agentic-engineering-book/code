"""Experiment 5: LangGraph conditional loop. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    state = bounded_loop(lambda s: {'step': s['step'] + 1},
                         lambda s: s['step'] >= 3, {'step': 0})
    return state['step']


if __name__ == "__main__":
    print(run())
