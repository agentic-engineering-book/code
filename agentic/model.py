"""Deterministic model stand-ins.

They isolate the architecture from model variance: every reader sees the same
output. Neither class measures what a real language model would do.

A decision is a plain dict, exactly as printed in the book:

    {"action": "calculator", "arguments": {"expression": "37*42"}}
    {"done": True, "answer": "37 x 42 = 1554."}
"""


class ScriptedModel:
    """Returns scripted responses in order, ignoring the messages it receives.

    After the script is exhausted the last response repeats, which is how
    Chapter 3 builds an agent that never finishes.
    """

    def __init__(self, responses):
        if not responses:
            raise ValueError("ScriptedModel needs at least one response")
        self.responses = list(responses)
        self.calls = 0

    def generate(self, messages):
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return response


class PolicyModel:
    """Chooses its response from the messages it receives.

    Use it when an experiment must show that changing the context changes the
    decision, for example by removing an observation from the history.
    """

    def __init__(self, policy):
        self.policy = policy
        self.calls = 0

    def generate(self, messages):
        self.calls += 1
        return self.policy(messages)


def last_observation(messages):
    """Content of the most recent tool message, or None if there is none."""
    for message in reversed(messages):
        if message.get("role") == "tool":
            return message["content"]
    return None
