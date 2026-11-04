"""Experiment 20 (Chapter 9): Memory consolidation."""
import textwrap

from agentic.live import OpenAIModel

PLAIN = ("Write one durable fact about the user's preferences, based on "
         "these past episodes. Reply with the fact only.")
GUARDED = PLAIN + (" If fewer than two episodes support it, or the "
                   "episodes conflict, reply NONE.")
MIN_EPISODES = 2

EPISODES = {
    "CONSISTENT": ["User requested a concise answer.",
                   "User asked to shorten the explanation.",
                   "User selected the concise version."],
    "CONFLICTING": ["User requested a concise answer.",
                    "User requested a detailed technical explanation."],
    "ONE EPISODE": ["User requested a concise answer."],
}

plain, guarded = OpenAIModel(system=PLAIN), OpenAIModel(system=GUARDED)


def consolidate(model, episodes):
    reply = model.generate([{"role": "user", "content": "\n".join(episodes)}])
    return reply["answer"]


def checked(episodes):
    """The threshold is counted in code; the model judges the conflict."""
    if len(episodes) < MIN_EPISODES:
        return "NONE (not enough episodes)"
    return consolidate(guarded, episodes)


for label, episodes in EPISODES.items():
    print(label)
    for name, result in [("plain", consolidate(plain, episodes)),
                         ("guarded", consolidate(guarded, episodes)),
                         ("checked", checked(episodes))]:
        print(textwrap.fill(result, 76, initial_indent=f"  {name:<8} ",
                            subsequent_indent=" " * 11))
