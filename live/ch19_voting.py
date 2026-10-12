"""Live run, Chapter 19: one sample versus a majority vote of five."""
from collections import Counter

from agentic.live import OpenAIModel
from live.common import SMALL_MODEL, arguments, parallel, rate, save, usage
from live.ch13_self_critique import FORMAT, final
from live.problems import problems

QUESTION = ("Does a majority vote over five independent samples from a small "
            "model answer more problems correctly than a single sample?")
TASKS = problems(20, seed=19)
SAMPLES = 5


def main():
    model_name = arguments(SMALL_MODEL).model
    models = []

    def sample(item):
        problem, _ = item[0]
        model = OpenAIModel(model_name)
        models.append(model)
        return final(model.generate(
            [{"role": "user", "content": problem + FORMAT}])["answer"])

    jobs = [(task, i) for task in TASKS for i in range(SAMPLES)]
    answers = parallel(sample, jobs)
    rows = []
    for index, (problem, truth) in enumerate(TASKS):
        votes = answers[index * SAMPLES:(index + 1) * SAMPLES]
        counts = Counter(v for v in votes if v is not None).most_common()
        tie = len(counts) > 1 and counts[0][1] == counts[1][1]
        majority = None if not counts or tie else counts[0][0]
        rows.append({"problem": problem, "expected": truth, "votes": votes,
                     "single_correct": votes[0] == truth,
                     "majority_correct": majority == truth,
                     "any_correct": truth in votes, "tie": tie})
    metrics = [rate("Correct, single sample",
                    [r["single_correct"] for r in rows]),
               rate("Correct, majority of five (ties count as wrong)",
                    [r["majority_correct"] for r in rows]),
               rate("At least one of five correct (oracle@5)",
                    [r["any_correct"] for r in rows])]
    save("ch19_voting", 19, QUESTION, [model_name], metrics, rows,
         usage(models))


if __name__ == "__main__":
    main()
