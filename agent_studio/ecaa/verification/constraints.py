"""Policy (constraint) verification, deterministic and separate from explanation checks.

``policy_gate`` is what Agent C uses: a committing action may run only if every
applicable rule is satisfied by *observed* facts. ``verify_policy_claim`` checks
a policy statement made in an explanation.
"""

from __future__ import annotations

from typing import Any

from ecaa.certificates.schema import ClaimCheck, PolicyClaim
from ecaa.core.domain import DomainAdapter
from ecaa.core.types import ABSTAIN, Action


def policy_gate(domain: DomainAdapter, observed: dict[str, Any], action: Action
                ) -> tuple[bool, list[dict], list[str]]:
    """Return (passes, rule results, failure reasons)."""
    if action.name == ABSTAIN:
        return True, [], []
    spec = domain.action_spec(action.name)
    if spec is None:
        return False, [], [f"'{action.name}' is not an available action"]
    results = domain.check_rules(observed, action)
    rows = [{"rule_id": r.rule_id, "status": r.status, "facts": list(r.facts_used),
             "detail": r.detail} for r in results]
    if not spec.commits:
        return True, rows, []
    failures = [f"{r.rule_id} {r.status}: {r.detail}" for r in results
                if r.status in ("violated", "unknown")]
    return not failures, rows, failures


def verify_policy_claim(claim: PolicyClaim, domain: DomainAdapter, observed: dict[str, Any],
                        proposed: Action) -> ClaimCheck:
    def result(status, reasons):
        return ClaimCheck(claim_id=claim.id, kind=claim.kind, component="policy",
                          status=status, reasons=reasons)

    rule = next((r for r in domain.rules() if r.rule_id == claim.rule_id), None)
    if rule is None:
        return result("unsupported", [f"rule {claim.rule_id} does not exist"])
    action = Action(name=claim.action or proposed.name,
                    params=claim.params if claim.action else (claim.params or proposed.params))
    if not rule.applies(action):
        if claim.status == "not_applicable":
            return result("supported", [])
        # Malformed rather than false: the claim cannot be checked, so it is not
        # counted as verified (and does not establish anything).
        return result("uncertain", [
            f"{claim.rule_id} does not apply to {action.label()}; it governs "
            f"{', '.join(rule.applies_to)}"])
    actual = rule.check(observed, action)
    if actual.status == claim.status:
        return result("supported", [])
    if actual.status == "unknown":
        return result("unsupported", [
            f"{claim.rule_id} cannot be decided from observed facts ({actual.detail})"])
    return result("contradicted", [
        f"{claim.rule_id} is {actual.status} for {action.label()}, not {claim.status} "
        f"({actual.detail})"])
