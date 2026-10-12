"""Small objective evaluators used in Chapter 22."""


def exact_match(actual, expected):
    """True only when the raw output equals the reference exactly."""
    return actual == expected


def numeric_match(actual, expected, tolerance=1e-9):
    """Parse the output as a number and compare it with the reference."""
    try:
        return abs(float(actual) - float(expected)) <= tolerance
    except (TypeError, ValueError):
        return False


def success_rate(results):
    """Fraction of truthy results; 0.0 for an empty evaluation set."""
    results = list(results)
    if not results:
        return 0.0
    return sum(bool(result) for result in results) / len(results)
