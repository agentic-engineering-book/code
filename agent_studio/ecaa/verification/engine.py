"""The independent explanation-verification engine.

It never asks the agent (or any model) whether its explanation is correct.
Every check is computed from the evidence ledger and the public policy, except
counterfactual tests, which observe the agent's own behaviour under replay.
"""

from __future__ import annotations

from dataclasses import dataclass

from ecaa.certificates.schema import (
    CounterfactualClaim,
    ExplanationDraft,
    FactClaim,
    NumericClaim,
    PolicyClaim,
    VerificationReport,
)
from ecaa.core.domain import DomainAdapter
from ecaa.core.types import Action
from ecaa.runtime.ledger import EvidenceLedger
from ecaa.verification.completeness import completeness_failures
from ecaa.verification.constraints import policy_gate, verify_policy_claim
from ecaa.verification.contradiction import find_contradictions
from ecaa.verification.counterfactual import ReplayFn, run_counterfactual_test
from ecaa.verification.numeric import verify_numeric_claim
from ecaa.verification.provenance import verify_fact_claim

ALL_COMPONENTS = ("provenance", "numeric", "policy", "contradiction", "completeness",
                  "counterfactual")


@dataclass
class VerifierConfig:
    components: tuple[str, ...] = ALL_COMPONENTS
    counterfactual_claims: int = 1     # how many claims to test per decision
    counterfactual_replays: int = 1    # replays per tested claim
    counterfactual_blocking: bool = True
    fail_on_unsupported: bool = True   # unsupported claims block execution

    def has(self, component: str) -> bool:
        return component in self.components


class VerificationEngine:
    def __init__(self, domain: DomainAdapter, config: VerifierConfig | None = None):
        self.domain = domain
        self.config = config or VerifierConfig()

    def verify(self, draft: ExplanationDraft, proposed: Action, ledger: EvidenceLedger,
               decision_step: int, replay: ReplayFn | None = None,
               config: VerifierConfig | None = None) -> VerificationReport:
        config = config or self.config
        observed = ledger.observed_facts()
        report = VerificationReport(components_run=[c for c in ALL_COMPONENTS if config.has(c)])

        for claim in draft.claims:
            if isinstance(claim, FactClaim) and config.has("provenance"):
                report.claim_checks.append(
                    verify_fact_claim(claim, ledger, self.domain, decision_step))
            elif isinstance(claim, NumericClaim) and config.has("numeric"):
                report.claim_checks.append(
                    verify_numeric_claim(claim, ledger, self.domain, decision_step))
            elif isinstance(claim, PolicyClaim) and config.has("policy"):
                report.claim_checks.append(
                    verify_policy_claim(claim, self.domain, observed, proposed))

        if config.has("contradiction"):
            report.claim_checks += find_contradictions(draft, ledger, self.domain, observed,
                                                       proposed)

        if config.has("policy"):
            passes, rows, failures = policy_gate(self.domain, observed, proposed)
            report.policy_results = rows
            report.failures += [f"policy: {f}" for f in failures]

        if config.has("completeness"):
            report.failures += [f"completeness: {f}" for f in completeness_failures(
                draft, self.domain, proposed,
                require_counterfactual=config.has("counterfactual"))]

        for check in report.claim_checks:
            if check.status == "contradicted" or (
                    check.status == "unsupported" and config.fail_on_unsupported):
                report.failures.append(
                    f"{check.component}: claim {check.claim_id} {check.status}: "
                    + "; ".join(check.reasons))

        # Behavioural tests are expensive: run them only if everything else passed.
        if config.has("counterfactual") and replay is not None and not report.failures:
            claims = [c for c in draft.claims if isinstance(c, CounterfactualClaim)]
            claims.sort(key=lambda c: c.fact not in draft.decisive_factors)
            for claim in claims[:config.counterfactual_claims]:
                spec = self.domain.action_spec(claim.predicted_action)
                if spec is not None:  # compare only parameters the action defines
                    claim = claim.model_copy(update={"predicted_params": {
                        k: v for k, v in claim.predicted_params.items() if k in spec.parameters}})
                test = run_counterfactual_test(claim, ledger, replay,
                                               config.counterfactual_replays)
                report.counterfactual_tests.append(test)
                if test.status == "refuted" and config.counterfactual_blocking:
                    report.failures.append(
                        f"counterfactual: claim {claim.id} refuted - with {claim.fact}="
                        f"{claim.value!r} the replayed decision was {', '.join(test.observed)}, "
                        f"not {test.predicted}")

        report.status = "FAIL" if report.failures else "PASS"
        return report
