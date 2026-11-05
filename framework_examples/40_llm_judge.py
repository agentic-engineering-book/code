"""Experiment 40: LLM-as-judge in LangChain. See framework_examples/README."""
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from framework_examples.support import chat

QUESTION = "What was the company's revenue last year?"
RUBRIC = """Score 0-2:
2 = correct, complete, grounded
1 = partially correct
0 = incorrect or unsupported"""
LABELED = [  # trusted labels for a small calibration subset
    ("Revenue was $120m (source: 2025 annual report).", 2),
    ("Revenue grew strongly to roughly $190m last year, driven by "
     "expansion into several new regional markets.", 0),
    ("Revenue was $120m.", 1),
    ("I don't know.", 0),
]
TRIALS = 3
SCORE = ChatPromptTemplate.from_messages([
    ("system", "You grade answers with this rubric:\n{rubric}\n"
               "Reply with the score only."),
    ("human", "Question: {question}\nAnswer: {answer}")])
PAIR = ChatPromptTemplate.from_messages([
    ("system", "You compare two answers to a question. Reply with A or B "
               "only: which answer is better?"),
    ("human", "Question: {question}\nAnswer A: {a}\nAnswer B: {b}")])


def run():
    judge = SCORE | chat() | StrOutputParser()
    pairwise = PAIR | chat() | StrOutputParser()
    lines = ["calibration against trusted labels:"]
    agreement = over_scored = 0
    for answer, label in LABELED:
        replies = judge.batch([{"rubric": RUBRIC, "question": QUESTION,
                                "answer": answer}] * TRIALS)
        scores = [int(reply.strip()[0]) for reply in replies]
        agreement += sum(score == label for score in scores)
        over_scored += sum(score > label for score in scores)
        lines.append(f"  label={label} judge={scores}  {answer[:36]}")
    total = TRIALS * len(LABELED)
    lines.append(f"agreement {agreement}/{total}, "
                 f"over-scored {over_scored}/{total}")
    short, polished = LABELED[0][0], LABELED[1][0]
    first = pairwise.batch(
        [{"question": QUESTION, "a": short, "b": polished}] * TRIALS)
    second = pairwise.batch(
        [{"question": QUESTION, "a": polished, "b": short}] * TRIALS)
    lines += ["swap test, prefers the sourced answer",
              "  when it is shown first: "
              f" {[r.strip().startswith('A') for r in first]}",
              "  when it is shown second: "
              f"{[r.strip().startswith('B') for r in second]}"]
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
