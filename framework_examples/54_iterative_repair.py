"""Experiment 54: LangGraph feedback and bounded repair loop. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    def attempt(state):
        return {'step': state['step'] + 1,
                'value': 'return a-b' if state['step'] == 0 else 'return a+b'}
    state = bounded_loop(attempt, lambda s: s['value'] == 'return a+b' or s['step'] >= 3,
                         {'step': 0, 'value': ''})
    return {'attempts': state['step'], 'repaired': state['value']}


if __name__ == "__main__":
    print(run())
