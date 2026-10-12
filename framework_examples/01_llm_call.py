"""Experiment 1: LangChain model invocation."""
from langchain_core.language_models.fake import FakeListLLM


def run():
    # A deterministic test double stands in for a hosted model.
    model = FakeListLLM(responses=["37 x 42 is approximately 1,500."])
    answer = model.invoke("What is 37 * 42?")
    return {"model": answer, "ground_truth": 37 * 42,
            "correct": str(37 * 42) in answer}


if __name__ == "__main__":
    print(run())
