"""Experiment 55: LangGraph observe/validate computer-action workflow. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    screen = {'button': (100, 200)}
    def observe(state):
        return {'value': screen['button']}
    def validate(state):
        screen['button'] = (140, 220)
        return {'value': 'reobserve' if state['value'] != screen['button'] else 'click'}
    return sequence([('observe', observe), ('validate_before_act', validate)], {})['value']


if __name__ == "__main__":
    print(run())
