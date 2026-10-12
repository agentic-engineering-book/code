"""Experiment 47 (Chapter 25): Permissions."""
PARENT_PERMISSIONS = {
    "search": {"read"},
    "email": {"draft"},
    "payments": set(),
}


def authorized(permissions, action):
    resource, verb = action
    return verb in permissions.get(resource, set())


def send_email(permissions, draft):
    """The capability checks permission itself, before the side effect."""
    if not authorized(permissions, ("email", "send")):
        raise PermissionError("email:send not granted")
    return f"sent {draft}"


def delegate(parent, requested):
    """A child receives at most what the parent holds."""
    return {resource: verbs & parent.get(resource, set())
            for resource, verbs in requested.items()}


for action in [("search", "read"), ("email", "draft"), ("email", "send")]:
    allowed = authorized(PARENT_PERMISSIONS, action)
    print(":".join(action), "->", "allowed" if allowed else "denied")

try:
    send_email(PARENT_PERMISSIONS, "draft-7")
except PermissionError as error:
    print("tool boundary:", error)

requested = {"search": {"read"}, "email": {"draft", "send"}}
child = delegate(PARENT_PERMISSIONS, requested)
print("child asked for email:", sorted(requested["email"]),
      "| received:", sorted(child["email"]))

PARENT_PERMISSIONS["search"] = set()  # revoked while the task runs
print("after revocation, search:read ->",
      authorized(PARENT_PERMISSIONS, ("search", "read")))
