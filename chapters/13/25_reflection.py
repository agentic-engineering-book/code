"""Experiment 25 (Chapter 13): Reflection."""
import re

from agentic import calculator
from agentic.live import OpenAIModel

TASK = ("A shop buys 417 items at 35 dollars each and sells them at 47 "
        "dollars each, but 62 items are unsold. What is the profit in dollars?")
CORRECT = calculator("355 * 47 - 417 * 35")  # what a tool can confirm
DRAFTS = {5004: "417 * (47 - 35) = 5004 dollars.",
          2090: "355 * 47 - 417 * 35 = 16685 - 14595 = 2090 dollars."}
CRITICS = {
    "careful": "Check this answer step by step, then end with the correct "
               "profit as a line 'FINAL: <integer>'.",
    "hasty": "This answer contains a mistake. Find it and reply with the "
             "corrected profit as a line 'FINAL: <integer>'.",
}
critic = OpenAIModel()


def critique(draft, instruction):
    """The critic's proposed revision: the number after FINAL."""
    reply = critic.generate([{"role": "user", "content":
                              f"Task: {TASK}\nAnswer: {draft}\n{instruction}"}])
    found = re.findall(r"FINAL:\s*\$?([\d,]+)", reply["answer"])
    return int(found[-1].replace(",", "")) if found else None


def outcome(draft, revision):
    if draft != CORRECT:
        return "improvement" if revision == CORRECT else "no useful repair"
    return "preserved" if revision == CORRECT else "REGRESSION"


print("critic   draft  proposed  always            verified")
for name, instruction in CRITICS.items():
    for draft, text in DRAFTS.items():
        for trial in range(3):
            proposed = critique(text, instruction)
            verified = proposed if proposed == CORRECT else draft
            print(f"{name:8} {draft:>5} {proposed!s:>9}  "
                  f"{outcome(draft, proposed):17} {outcome(draft, verified)}")
