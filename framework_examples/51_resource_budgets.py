"""Experiment 51: LangGraph application budgets and stopping edges. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    def work(state):
        return {'step': state['step'] + 1, 'value': round(state['value'] + .03, 2)}
    state = bounded_loop(work, lambda s: s['step'] >= 3 or s['value'] >= .10,
                         {'step': 0, 'value': 0.0})
    return {'steps': state['step'], 'cost': state['value']}


if __name__ == "__main__":
    print(run())
