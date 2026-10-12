"""Experiment 19 (Chapter 9): Compress working context."""
import json

from agentic.context import compress

context = {
    "task": "write technical report",
    "word_limit": 500,
    "audience": "technical",
    "successful_source": "S3",
    "failed_searches": ["S1", "S2"],
    "send_requires_approval": True,
    "small_talk": "thanks"
}
keep = {
    "task",
    "word_limit",
    "audience",
    "successful_source",
    "send_requires_approval"
}


def may_send_now(state):
    """Harness rule; a missing constraint reads as 'no approval needed'."""
    return not state.get("send_requires_approval", False)


for label, fields in [("GOOD", keep),
                      ("BROKEN", keep - {"send_requires_approval"})]:
    compressed = compress(context, fields)
    ratio = len(json.dumps(compressed)) / len(json.dumps(context))
    print(f"{label} compressor: {len(json.dumps(compressed))} of "
          f"{len(json.dumps(context))} characters ({ratio:.0%})")
    print(json.dumps(compressed, indent=2))
    print("may send without approval:", may_send_now(compressed))
