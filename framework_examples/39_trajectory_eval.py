"""Experiment 39: LangGraph reducer-backed trajectory evaluation. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    result = sequence([
        ('search', lambda s: {'results': ['search']}),
        ('calculator', lambda s: {'results': ['calculator']}),
        ('answer', lambda s: {'results': ['answer']})], {'results': []})
    return result['results'] == ['search', 'calculator', 'answer']


if __name__ == "__main__":
    print(run())
