"""Deterministic contradiction checks between an explanation, the evidence
ledger and the decision itself."""

from __future__ import annotations

from typing import Any

from ecaa.certificates.schema import ClaimCheck, ExplanationDraft, FactClaim, PolicyClaim
from ecaa.core.domain import DomainAdapter
from ecaa.core.types import Action
from ecaa.runtime.ledger import EvidenceLedger
from ecaa.verification.values import values_equal


def find_contradictions(draft: ExplanationDraft, ledger: EvidenceLedger, domain: DomainAdapter,
                        observed: dict[str, Any], proposed: Action) -> list[ClaimCheck]:
    checks: list[ClaimCheck] = []

    def add(claim_id, kind, status, reasons):
        checks.append(ClaimCheck(claim_id=claim_id, kind=kind, component="contradiction",
                                 status=status, reasons=reasons))

    for claim in draft.claims:
        # A stated fact that disagrees with any authoritative observation.
        if isinstance(claim, FactClaim):
            for evidence, authoritative in ledger.fact_sources(claim.fact):
                if authoritative and not values_equal(evidence.content[claim.fact], claim.value):
                    add(claim.id, claim.kind, "contradicted", [
                        f"{evidence.evidence_id} records {claim.fact}="
                        f"{evidence.content[claim.fact]!r}"])
                    break
        # The explanation says the chosen action breaks a rule.
        if (isinstance(claim, PolicyClaim) and claim.status == "violated"
                and (not claim.action or claim.action == proposed.name)
                and (not claim.params or claim.params == proposed.params)):
            add(claim.id, claim.kind, "contradicted", [
                f"the explanation states {claim.rule_id} is violated by the chosen action"])

    # Reasons given for rejecting alternatives must hold on the observed facts.
    rules = {r.rule_id: r for r in domain.rules()}
    for index, alternative in enumerate(draft.alternatives):
        action = Action(name=alternative.action, params=alternative.params)
        for rule_id in alternative.rejected_because:
            rule = rules.get(rule_id)
            if rule is None:
                add(f"alt{index}", "alternative", "unsupported", [f"rule {rule_id} does not exist"])
            elif not rule.applies(action):
                # e.g. "did not reject because P3 holds for the purchase": not checkable
                # under this schema, so uncertain rather than contradicted.
                add(f"alt{index}", "alternative", "uncertain",
                    [f"{rule_id} does not apply to {action.label()}; it governs "
                     f"{', '.join(rule.applies_to)}"])
            else:
                status = rule.check(observed, action).status
                if status == "satisfied":
                    add(f"alt{index}", "alternative", "contradicted",
                        [f"{action.label()} satisfies {rule_id}; it is not a reason to reject it"])
                elif status == "unknown":
                    add(f"alt{index}", "alternative", "unsupported",
                        [f"{rule_id} for {action.label()} cannot be decided from observed facts"])

    # Factors called decisive must at least have been observed.
    for fact in draft.decisive_factors:
        if not ledger.fact_sources(fact):
            add(f"decisive:{fact}", "decisive_factor", "unsupported",
                [f"{fact} was never observed"])
    return checks
