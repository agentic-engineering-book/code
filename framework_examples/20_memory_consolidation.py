"""Experiment 20: LangGraph memory-consolidation stages. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop
from collections import Counter


def run():
    result = sequence([
        ('count', lambda s: {'value': dict(Counter(s['value']))}),
        ('consolidate', lambda s: {'value': {'A': 'usually succeeds'
            if s['value']['A succeeded'] > 1 else 'succeeded once', 'B': 'failed once'}})],
        {'value': ['A succeeded', 'A succeeded', 'B failed']})
    return result['value']


if __name__ == "__main__":
    print(run())
