"""Evidence provenance: do cited observations exist, belong to this run, predate
the decision, come from an authorised tool, remain unmodified, and actually
state the claimed fact?"""

from __future__ import annotations

from ecaa.certificates.schema import ClaimCheck, FactClaim
from ecaa.core.domain import DomainAdapter
from ecaa.core.types import Evidence
from ecaa.runtime.ledger import EvidenceLedger
from ecaa.verification.values import values_equal


def check_citations(evidence_ids: list[str], ledger: EvidenceLedger, domain: DomainAdapter,
                    decision_step: int) -> tuple[list[Evidence], list[str]]:
    """Return (valid cited evidence, reasons for invalid citations)."""
    tool_names = {t.name for t in domain.tools()}
    valid, reasons = [], []
    for evidence_id in evidence_ids:
        evidence = ledger.get(evidence_id)
        if evidence is None:
            reasons.append(f"cited evidence {evidence_id} does not exist")
        elif evidence.run_id != ledger.run_id or evidence.task_id != ledger.task_id:
            reasons.append(f"evidence {evidence_id} belongs to another run or task")
        elif evidence.step > decision_step:
            reasons.append(f"evidence {evidence_id} was retrieved after the decision")
        elif evidence.tool not in tool_names:
            reasons.append(f"evidence {evidence_id} came from an unauthorised tool")
        elif not ledger.intact(evidence):
            reasons.append(f"evidence {evidence_id} was modified after retrieval")
        else:
            valid.append(evidence)
    return valid, reasons


def verify_fact_claim(claim: FactClaim, ledger: EvidenceLedger, domain: DomainAdapter,
                      decision_step: int) -> ClaimCheck:
    def result(status, reasons):
        return ClaimCheck(claim_id=claim.id, kind=claim.kind, component="provenance",
                          status=status, reasons=reasons)

    if not claim.evidence_ids:
        return result("unsupported", ["no evidence cited"])
    valid, reasons = check_citations(claim.evidence_ids, ledger, domain, decision_step)
    if reasons and not valid:
        return result("unsupported", reasons)
    mentioning = [e for e in valid if claim.fact in e.content]
    if not mentioning:
        return result("unsupported", reasons + [f"no cited evidence states {claim.fact}"])
    authoritative = [e for e in mentioning if claim.fact in e.authoritative_keys]
    if not authoritative:
        return result("unsupported", reasons + [
            f"{claim.fact} is cited only from a non-authoritative source"])
    if all(values_equal(e.content[claim.fact], claim.value) for e in authoritative):
        return result("supported", reasons)
    observed = authoritative[-1].content[claim.fact]
    return result("contradicted", reasons + [
        f"{claim.fact} is {observed!r} in {authoritative[-1].evidence_id}, not {claim.value!r}"])
