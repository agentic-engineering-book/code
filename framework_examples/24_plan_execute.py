"""Experiment 24: LangGraph plan and execution stages. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    state = sequence([
        ('plan', lambda s: {'value': ['search', 'summarize']}),
        ('search', lambda s: {'value': {'plan': s['value'], 'evidence': 'new evidence'}}),
        ('summarize', lambda s: {'value': 'summary based on ' + s['value']['evidence']})], {})
    return state['value']


if __name__ == "__main__":
    print(run())
