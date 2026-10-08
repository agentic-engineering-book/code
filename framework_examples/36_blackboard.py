"""Experiment 36: LangGraph shared-state blackboard. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    return sequence([
        ('research', lambda s: {'value': {'research': 'evidence'}}),
        ('writer', lambda s: {'value': {**s['value'],
            'writer': 'draft based on ' + s['value']['research']}})], {})['value']


if __name__ == "__main__":
    print(run())
