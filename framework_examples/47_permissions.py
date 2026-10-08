"""Experiment 47: LangGraph authorization gate. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    return branch({'allow': lambda s: {'value': 'executed'},
                   'deny': lambda s: {'value': 'denied'}},
                  lambda s: 'allow' if s['value'] in {'read'} else 'deny', 'send')


if __name__ == "__main__":
    print(run())
