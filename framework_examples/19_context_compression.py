"""Experiment 19: LangChain field-keeping compressor and a broken variant."""
from langchain_core.runnables import RunnableLambda

CONTEXT = {"task": "write technical report", "word_limit": 500,
           "audience": "technical", "successful_source": "S3",
           "failed_searches": ["S1", "S2"],
           "send_requires_approval": True, "small_talk": "thanks"}
KEEP = {"task", "word_limit", "audience", "successful_source",
        "send_requires_approval"}


def compressor(keep):
    return RunnableLambda(
        lambda state: {k: v for k, v in state.items() if k in keep})


def run():
    may_send = RunnableLambda(
        lambda state: not state.get("send_requires_approval", False))
    report = {}
    for label, keep in [("good", KEEP),
                        ("broken", KEEP - {"send_requires_approval"})]:
        compressed = compressor(keep).invoke(CONTEXT)
        report[label] = {"kept": list(compressed),
                         "may_send_without_approval":
                             may_send.invoke(compressed)}
    return report


if __name__ == "__main__":
    print(run())
