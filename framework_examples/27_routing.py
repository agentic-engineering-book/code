"""Experiment 27: LangGraph task routing. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    return branch({'math': lambda s: {'value': 'math_agent'},
                   'write': lambda s: {'value': 'writer'}},
                  lambda s: 'math' if s['value'] == 'calculate' else 'write', 'calculate')


if __name__ == "__main__":
    print(run())
