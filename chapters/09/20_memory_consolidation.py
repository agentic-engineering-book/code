"""Experiment 20 (Chapter 9): Memory consolidation."""
MIN_EPISODES = 2


def preference(episode):
    text = episode.lower()
    if "concise" in text or "shorten" in text:
        return "concise"
    if "detailed" in text:
        return "detailed"
    return None


def blind_consolidate(episodes):
    return "User prefers concise responses."


def consolidate(episodes):
    """Write a fact only with enough agreeing, non-conflicting evidence."""
    votes = [preference(e) for e in episodes if preference(e)]
    if len(set(votes)) > 1:
        counts = {v: votes.count(v) for v in sorted(set(votes))}
        return f"No fact: conflicting episodes {counts}"
    if len(votes) < MIN_EPISODES:
        return "No fact: not enough evidence"
    return f"User prefers {votes[0]} responses."


consistent = [
    "User requested a concise answer.",
    "User asked to shorten the explanation.",
    "User selected the concise version.",
]
conflicting = [
    "User requested a concise answer.",
    "User requested a detailed technical explanation.",
]

for label, episodes in [("CONSISTENT", consistent),
                        ("CONFLICTING", conflicting)]:
    print(label)
    print("  blind:  ", blind_consolidate(episodes))
    print("  guarded:", consolidate(episodes))
