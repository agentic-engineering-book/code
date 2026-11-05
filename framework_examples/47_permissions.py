"""Experiment 47: Permissions in LangGraph. See framework_examples/README."""
from langchain_core.tools import tool

from framework_examples.support import branch, chat

REQUEST = ("Email our proposal summary to customer@example.com: the new "
           "plan costs 40 dollars a month.")
PERMISSIONS = {"search": {"read"}, "email": {"draft"}, "payments": set()}
TOOL_ACTIONS = {"send_email": ("email", "send"),
                "draft_email": ("email", "draft")}


def authorized(permissions, action):
    resource, verb = action
    return verb in permissions.get(resource, set())


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email."""
    # The capability checks permission itself, before the side effect.
    if not authorized(PERMISSIONS, ("email", "send")):
        raise PermissionError("email:send not granted")
    return "sent"


@tool
def draft_email(to: str, subject: str, body: str) -> str:
    """Save an email draft."""
    return "draft saved"


def delegate(parent, requested):
    """A child receives at most what the parent holds."""
    return {resource: verbs & parent.get(resource, set())
            for resource, verbs in requested.items()}


def run():
    lines = []
    for action in [("search", "read"), ("email", "draft"), ("email", "send")]:
        allowed = authorized(PERMISSIONS, action)
        lines.append(f"{':'.join(action)} -> "
                     f"{'allowed' if allowed else 'denied'}")
    # A real agent, told nothing about permissions, chooses a tool.
    model = chat().bind_tools([draft_email, send_email],
                              tool_choice="required")
    call = model.invoke(REQUEST).tool_calls[0]
    lines.append(f"agent chooses: {call['name']}")
    tools = {"send_email": send_email, "draft_email": draft_email}
    gated = branch(  # a LangGraph conditional edge is the policy gate
        {"allow": lambda s: {"value": tools[s["value"]["name"]].invoke(
            s["value"]["args"])},
         "deny": lambda s: {"value": "denied by gate"}},
        lambda s: "allow" if authorized(
            PERMISSIONS, TOOL_ACTIONS[s["value"]["name"]]) else "deny",
        call)
    lines.append(f"graph gate: {gated}")
    try:  # a path that skips the gate still meets the tool's own check
        result = send_email.invoke(call["args"])
        lines.append(f"tool called directly: {result}")
    except PermissionError as error:
        lines.append(f"tool boundary: {error}")
    requested = {"search": {"read"}, "email": {"draft", "send"}}
    child = delegate(PERMISSIONS, requested)
    lines.append(f"child asked for email: {sorted(requested['email'])} "
                 f"| received: {sorted(child['email'])}")
    PERMISSIONS["search"] = set()  # revoked while the task runs
    lines.append("after revocation, search:read -> "
                 f"{authorized(PERMISSIONS, ('search', 'read'))}")
    PERMISSIONS["search"] = {"read"}  # restore for repeat runs
    return lines


if __name__ == "__main__":
    for line in run():
        print(line)
