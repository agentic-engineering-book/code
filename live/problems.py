"""Seeded multi-step word problems with exact integer answers."""
import random

TEMPLATES = [
    ("A warehouse has {a} boxes with {b} items each. {c} items are damaged. "
     "{d}% of the undamaged items are shipped. How many items are shipped?",
     lambda a, b, c, d: (a * b - c) * d // 100),
    ("A train covers {a} km per hour for {b} hours, then {c} km per hour for "
     "{d} hours. How many kilometres does it travel in total?",
     lambda a, b, c, d: a * b + c * d),
    ("A shop buys {a} items at {b} dollars each and sells them at {c} dollars "
     "each, but {d} items are unsold. What is the profit in dollars?",
     lambda a, b, c, d: (a - d) * c - a * b),
    ("A tank holds {a} litres. It loses {b} litres per day for {c} days and "
     "is then refilled with {d} litres. How many litres are in it?",
     lambda a, b, c, d: a - b * c + d),
]


def problems(count, seed):
    rng = random.Random(seed)
    items = []
    while len(items) < count:
        text, solve = rng.choice(TEMPLATES)
        values = dict(a=rng.randint(120, 980), b=rng.randint(12, 89),
                      c=rng.randint(11, 97), d=rng.choice([20, 25, 40, 60, 75]))
        if "profit" in text:
            values["c"] = values["b"] + rng.randint(3, 40)
            values["d"] = rng.randint(5, values["a"] // 3)
        if "undamaged" in text:
            values["c"] = rng.randint(10, values["a"])
        answer = solve(**values)
        if "undamaged" in text and (values["a"] * values["b"] - values["c"]) \
                * values["d"] % 100:
            continue  # keep answers whole numbers
        if answer > 0:
            items.append((text.format(**values), answer))
    return items
