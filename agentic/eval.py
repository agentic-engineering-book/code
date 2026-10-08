def exact_match(actual, expected): return actual==expected
def success_rate(results): return sum(bool(x) for x in results)/len(results) if results else 0.0
