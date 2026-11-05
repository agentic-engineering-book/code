"""Experiment 40 (Chapter 22): LLM-as-judge."""
from agentic.live import OpenAIModel

QUESTION = "What was the company's revenue last year?"
RUBRIC = """Score 0-2:
2 = correct, complete, grounded
1 = partially correct
0 = incorrect or unsupported"""

# Trusted labels for a small calibration subset.
LABELED = [
    ("Revenue was $120m (source: 2025 annual report).", 2),
    ("Revenue grew strongly to roughly $190m last year, driven by "
     "expansion into several new regional markets.", 0),
    ("Revenue was $120m.", 1),
    ("I don't know.", 0),
]
TRIALS = 3


def ask(system, content):
    reply = OpenAIModel(system=system).generate(
        [{"role": "user", "content": content}])
    return reply["answer"].strip()


def judge(answer):
    """A real model judge scoring with the rubric."""
    reply = ask("You grade answers with this rubric:\n" + RUBRIC +
                "\nReply with the score only.",
                f"Question: {QUESTION}\nAnswer: {answer}")
    return int(reply[0])


def pairwise_judge(first, second):
    """A real model judge comparing two answers; returns the one chosen."""
    reply = ask("You compare two answers to a question. Reply with A or B "
                "only: which answer is better?",
                f"Question: {QUESTION}\nAnswer A: {first}\nAnswer B: {second}")
    return first if reply.startswith("A") else second


print("calibration against trusted labels:")
agreement = over_scored = 0
for answer, label in LABELED:
    scores = [judge(answer) for trial in range(TRIALS)]
    agreement += sum(score == label for score in scores)
    over_scored += sum(score > label for score in scores)
    print(f"  label={label} judge={scores}  {answer[:36]}")
total = TRIALS * len(LABELED)
print(f"agreement {agreement}/{total}, over-scored {over_scored}/{total}")

short, polished = LABELED[0][0], LABELED[1][0]
first_order = [pairwise_judge(short, polished) == short
               for trial in range(TRIALS)]
second_order = [pairwise_judge(polished, short) == short
                for trial in range(TRIALS)]
print("swap test, prefers the sourced answer")
print("  when it is shown first: ", first_order)
print("  when it is shown second:", second_order)
