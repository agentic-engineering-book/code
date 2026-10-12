"""Experiment 46 (Chapter 25): Human approval."""
import hashlib
import json

POLICY = {"search": "allow", "draft_email": "allow", "send_email": "approval"}
APPROVAL_TTL_MINUTES = 15


def action_hash(action):
    """Stable across processes: SHA-256 of canonical JSON."""
    canonical = json.dumps(action, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()[:12]


def request_approval(action, now):
    return {"action_hash": action_hash(action), "state": "AWAITING_APPROVAL",
            "requested_at": now}


def decide(approval, approved, reviewer):
    approval["state"] = "APPROVED" if approved else "REJECTED"
    approval["approved_by"] = reviewer
    return approval


def execute(action, approval, now):
    if POLICY[action["tool"]] == "allow":
        return "executed"
    if approval is None or approval["state"] != "APPROVED":
        return "blocked: not approved"
    if now - approval["requested_at"] > APPROVAL_TTL_MINUTES:
        return "blocked: approval expired"
    if action_hash(action) != approval["action_hash"]:
        return "blocked: action changed after approval"
    return "executed"


action = {"tool": "send_email",
          "args": {"to": "customer@example.com", "subject": "Proposal"}}
approval = request_approval(action, now=0)
print("proposed, state:", approval["state"], approval["action_hash"])
print("before decision:", execute(action, approval, now=1))

decide(approval, approved=True, reviewer="human-3")
print("approved:", execute(action, approval, now=2))

mutated = {**action, "args": {**action["args"],
                              "to": "all-customers@example.com"}}
print("mutated recipient:", execute(mutated, approval, now=3))
print("two hours later:", execute(action, approval, now=120))
