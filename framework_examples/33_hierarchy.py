"""Experiment 33: LangGraph nested worker hierarchy. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    def research_lead(state):
        child = sequence([('retriever', lambda s: {'value': 'evidence'})], {})
        return {'value': child['value']}
    return sequence([('research_lead', research_lead),
                     ('supervisor', lambda s: {'value': 'approved ' + s['value']})], {})['value']


if __name__ == "__main__":
    print(run())
