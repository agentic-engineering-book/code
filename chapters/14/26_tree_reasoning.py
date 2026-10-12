"""Experiment 26 (Chapter 14): Tree reasoning."""
START, TARGET, DEPTH = 2, 13, 2
OPERATIONS = {
    "+3": lambda x: x + 3,
    "*2": lambda x: x * 2,
    "+9": lambda x: x + 9,
}


def expand(state):
    value, path = state
    return [(operation(value), path + [name])
            for name, operation in OPERATIONS.items()]


def closeness(state):
    """Greedy heuristic: immediate distance to the target."""
    return -abs(TARGET - state[0])


def lookahead(state):
    """Best closeness still reachable in the remaining steps."""
    frontier = [state]
    for _ in range(DEPTH - len(state[1])):
        frontier = [child for s in frontier for child in expand(s)]
    return max(closeness(s) for s in frontier)


def show(state):
    return " ".join([str(START)] + state[1]) + f" = {state[0]}"


def beam_search(width, score):
    beam, expansions = [(START, [])], 0
    for _ in range(DEPTH):
        candidates = []
        for state in beam:
            candidates += expand(state)
            expansions += 1
        beam = sorted(candidates, key=score, reverse=True)[:width]
    solutions = [show(s) for s in beam if s[0] == TARGET]
    return solutions, expansions


print("first moves scored by closeness:")
for state in expand((START, [])):
    print(f"  {show(state):10} score {closeness(state)}")
for score in (closeness, lookahead):
    for width in (1, 2, 3):
        solutions, expansions = beam_search(width, score)
        print(f"{score.__name__:9} width {width}: expansions={expansions} "
              f"solution={solutions[0] if solutions else None}")
