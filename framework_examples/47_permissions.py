"""Experiment 47: LangGraph authorization gate plus a check in the tool."""
from framework_examples.support import branch

PERMISSIONS = {"search": {"read"}, "email": {"draft"}}


def authorized(action):
    resource, verb = action.split(":")
    return verb in PERMISSIONS.get(resource, set())


def protected_tool(action):
    """The capability re-checks: a graph edge alone is not enforcement."""
    if not authorized(action):
        raise PermissionError(action)
    return f"executed {action}"


def run():
    results = {}
    for action in ["search:read", "email:draft", "email:send"]:
        results[action] = branch(
            {"allow": lambda s: {"value": protected_tool(s["value"])},
             "deny": lambda s: {"value": "denied"}},
            lambda s: "allow" if authorized(s["value"]) else "deny",
            action)
    return results


if __name__ == "__main__":
    print(run())
