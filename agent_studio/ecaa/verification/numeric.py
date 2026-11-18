"""Numerical consistency: recompute arithmetic claims from cited facts."""

from __future__ import annotations

from ecaa.certificates.schema import ClaimCheck, NumericClaim
from ecaa.core.domain import DomainAdapter
from ecaa.runtime.ledger import EvidenceLedger
from ecaa.verification.provenance import check_citations
from ecaa.verification.values import PLACEHOLDER, ExpressionError, evaluate, values_equal


def verify_numeric_claim(claim: NumericClaim, ledger: EvidenceLedger, domain: DomainAdapter,
                         decision_step: int) -> ClaimCheck:
    def result(status, reasons):
        return ClaimCheck(claim_id=claim.id, kind=claim.kind, component="numeric",
                          status=status, reasons=reasons)

    keys = PLACEHOLDER.findall(claim.expression)
    valid, reasons = check_citations(claim.evidence_ids, ledger, domain, decision_step)
    bindings = {}
    for key in keys:
        source = next((e for e in reversed(valid)
                       if key in e.content and key in e.authoritative_keys), None)
        if source is None:
            return result("unsupported", reasons + [f"{key} is not stated by cited evidence"])
        bindings[key] = source.content[key]
    try:
        computed = evaluate(claim.expression, bindings)
    except ExpressionError as error:
        return result("unsupported", reasons + [str(error)])
    if claim.value is None or not values_equal(computed, claim.value, rel_tol=1e-4):
        return result("contradicted", reasons + [
            f"{claim.expression} evaluates to {computed:g}, not {claim.value}"])
    if not keys:
        return result("uncertain", reasons + ["arithmetic is correct but cites no facts"])
    return result("supported", reasons)
