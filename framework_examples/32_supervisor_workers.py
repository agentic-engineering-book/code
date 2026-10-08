"""Experiment 32: LangGraph supervisor dispatch to worker graphs. See framework_examples/README.md."""
from framework_examples.support import sequence, branch, parallel, bounded_loop


def run():
    def worker(job):
        return sequence([('work', lambda s: {'value': 'completed ' + s['value']})], {'value': job})['value']
    return parallel({job: lambda job=job: worker(job) for job in ['research', 'calculate', 'write']})


if __name__ == "__main__":
    print(run())
