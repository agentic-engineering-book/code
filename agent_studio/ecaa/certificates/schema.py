"""Versioned explanation certificate.

Claim kinds keep different epistemic statuses apart:

* ``evidence``      - a factual statement that must be supported by a cited observation
* ``numeric``       - arithmetic over cited facts
* ``policy``        - a conclusion derived from a public rule
* ``counterfactual``- a hypothesis about what the agent would do if one fact differed
* ``assumption``    - a declared predictive assumption or uncertainty (never "verified")

A counterfactual claim becomes a *tested behavioural influence* only after the
verifier replays the decision under that intervention and observes the result.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "ecaa-certificate/1.0"


class _Claim(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = ""
    text: str = ""


class FactClaim(_Claim):
    kind: Literal["evidence"] = "evidence"
    fact: str
    value: Any = None
    evidence_ids: list[str] = Field(default_factory=list)


class NumericClaim(_Claim):
    kind: Literal["numeric"] = "numeric"
    expression: str
    value: float | None = None
    evidence_ids: list[str] = Field(default_factory=list)


class PolicyClaim(_Claim):
    kind: Literal["policy"] = "policy"
    rule_id: str
    action: str = ""
    params: dict[str, Any] = Field(default_factory=dict)
    status: Literal["satisfied", "violated", "unknown", "not_applicable"] = "satisfied"


class CounterfactualClaim(_Claim):
    kind: Literal["counterfactual"] = "counterfactual"
    fact: str
    value: Any = None
    predicted_action: str
    predicted_params: dict[str, Any] = Field(default_factory=dict)


class AssumptionClaim(_Claim):
    kind: Literal["assumption"] = "assumption"


Claim = Annotated[
    FactClaim | NumericClaim | PolicyClaim | CounterfactualClaim | AssumptionClaim,
    Field(discriminator="kind"),
]


class AlternativeConsidered(BaseModel):
    model_config = ConfigDict(extra="ignore")
    action: str
    params: dict[str, Any] = Field(default_factory=dict)
    rejected_because: list[str] = Field(default_factory=list)  # rule ids
    text: str = ""


class ExplanationDraft(BaseModel):
    """The part of a certificate the agent writes."""

    model_config = ConfigDict(extra="ignore")
    summary: str = ""
    claims: list[Claim] = Field(default_factory=list)
    decisive_factors: list[str] = Field(default_factory=list)
    alternatives: list[AlternativeConsidered] = Field(default_factory=list)
    expected_outcome: str = ""
    limitations: list[str] = Field(default_factory=list)


class ClaimCheck(BaseModel):
    claim_id: str
    kind: str
    component: str
    status: Literal["supported", "unsupported", "contradicted", "uncertain", "not_checked"]
    reasons: list[str] = Field(default_factory=list)


class CounterfactualTest(BaseModel):
    claim_id: str
    fact: str
    value: Any = None
    predicted: str
    observed: list[str] = Field(default_factory=list)
    replays: int = 0
    matches: int = 0
    status: Literal["confirmed", "refuted", "inconclusive"] = "inconclusive"


class VerificationReport(BaseModel):
    status: Literal["PASS", "FAIL", "NOT_VERIFIED"] = "NOT_VERIFIED"
    components_run: list[str] = Field(default_factory=list)
    claim_checks: list[ClaimCheck] = Field(default_factory=list)
    policy_results: list[dict[str, Any]] = Field(default_factory=list)
    counterfactual_tests: list[CounterfactualTest] = Field(default_factory=list)
    failures: list[str] = Field(default_factory=list)
    risk_tier: str | None = None

    def failed(self) -> bool:
        return self.status == "FAIL"


class Certificate(BaseModel):
    schema_version: str = SCHEMA_VERSION
    # identification
    task_id: str
    run_id: str
    decision_id: str
    agent_variant: str
    model: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    # decision context
    objective: str
    observed_evidence_ids: list[str] = Field(default_factory=list)
    proposed_action: str
    proposed_params: dict[str, Any] = Field(default_factory=dict)
    applicable_rules: list[str] = Field(default_factory=list)
    explanation_timing: Literal["before_action", "after_action"] = "before_action"
    # explanation
    explanation: ExplanationDraft = Field(default_factory=ExplanationDraft)
    # verification
    verification: VerificationReport = Field(default_factory=VerificationReport)
    # execution
    executed: bool = False
    final_action: str | None = None
    final_params: dict[str, Any] = Field(default_factory=dict)
    outcome: str = ""
    revision_count: int = 0
    abstention_reason: str | None = None
