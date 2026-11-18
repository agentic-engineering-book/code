"""Structural completeness against the *public* policy (never the oracle).

A committing action must address every rule that applies to it. Any other
decision (refuse, escalate, request information) must rest on at least one
policy claim showing why committing is not permitted.
"""

from __future__ import annotations

from ecaa.certificates.schema import CounterfactualClaim, ExplanationDraft, PolicyClaim
from ecaa.core.domain import DomainAdapter
from ecaa.core.types import ABSTAIN, Action


def completeness_failures(draft: ExplanationDraft, domain: DomainAdapter, proposed: Action,
                          require_counterfactual: bool) -> list[str]:
    if proposed.name == ABSTAIN:
        return []
    failures = []
    policy_claims = [c for c in draft.claims if isinstance(c, PolicyClaim)]
    spec = domain.action_spec(proposed.name)
    if spec is not None and spec.commits:
        for rule in domain.rules():
            if not rule.applies(proposed):
                continue
            covered = any(c.rule_id == rule.rule_id
                          and (not c.action or c.action == proposed.name)
                          and (not c.params or c.params == proposed.params)
                          for c in policy_claims)
            if not covered:
                failures.append(f"rule {rule.rule_id} applies to {proposed.label()} "
                                "but the explanation does not address it")
    else:
        committing = {a.name for a in domain.actions() if a.commits}
        if not any(c.status in ("violated", "unknown") and c.action in committing
                   for c in policy_claims):
            failures.append("the decision not to commit needs a policy claim showing a rule "
                            "that is violated or unknown for a committing action ("
                            + ", ".join(sorted(committing)) + ")")
    if require_counterfactual and not any(isinstance(c, CounterfactualClaim)
                                          for c in draft.claims):
        failures.append("no counterfactual claim about a decisive factor")
    return failures
