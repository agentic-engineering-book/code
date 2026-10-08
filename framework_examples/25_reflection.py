"""Experiment 25: LangGraph draft/critique/revision workflow. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    result = sequence([
        ('draft', lambda s: {'value': 'The answer is 41'}),
        ('critique', lambda s: {'value': {'draft': s['value'], 'critique': 'Arithmetic is wrong'}}),
        ('revise', lambda s: {'value': 'The answer is 42'})], {})
    return result['value']


if __name__ == "__main__":
    print(run())
