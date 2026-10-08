"""Experiment 35: LangGraph debate branches and judge stage. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    arguments = parallel({'agent_a': lambda: 'A', 'agent_b': lambda: 'B'})
    return sequence([('judge', lambda s: {'value': 'A' if 'A' in dict(s['value']).values() else 'B'})],
                    {'value': arguments})['value']


if __name__ == "__main__":
    print(run())
