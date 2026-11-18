"""The experimental agent architectures.

A  standard            decide -> execute -> explain afterwards
B  explain_first       decide with certificate -> execute (no verification)
B+ self_check          B plus self-review rounds (cost-matched control, no external check)
C  policy_verified     decide -> policy gate on committing actions -> execute/revise/abstain
                       -> explain afterwards
D1 ecaa_strict         decide with certificate -> independent verification (+ counterfactual
                       replay) -> execute only on PASS, else revise / abstain
D2 ecaa_adaptive       D with verification depth set by risk, evidence conflicts and reversibility
"""

from __future__ import annotations

import time
import uuid
from dataclasses import replace

from ecaa.agents import prompts
from ecaa.agents.base import AgentConfig, Decision, RunResult, Session
from ecaa.certificates.schema import ExplanationDraft, VerificationReport
from ecaa.core.types import ABSTAIN, Action
from ecaa.providers.base import Provider
from ecaa.runtime.environment import Environment
from ecaa.verification.constraints import policy_gate
from ecaa.verification.engine import VerificationEngine, VerifierConfig


class Agent:
    variant = "base"
    with_certificate = False
    verified = False

    def __init__(self, config: AgentConfig | None = None,
                 verifier: VerifierConfig | None = None, name: str | None = None):
        self.config = config or AgentConfig()
        self.verifier = verifier or VerifierConfig()
        if name:
            self.variant = name

    def run(self, env: Environment, provider: Provider, repetition: int = 0,
            listener=None) -> RunResult:
        session = Session(env, provider, self.variant, repetition,
                          prompts.system_prompt(env.domain, self.with_certificate, self.verified),
                          self.with_certificate, listener=listener)
        final, executed, certificate, attempts = self.decide(session)
        session.log("run_end", final_action=final.label(), executed=executed)
        return RunResult(
            run_id=env.run_id, task_id=env.task_id, variant=self.variant, repetition=repetition,
            model=provider.model, final_action=final, executed=executed,
            abstained=final.name == ABSTAIN, certificate=certificate, attempts=attempts,
            usage=session.usage, tool_calls=env.tool_calls, tool_errors=env.tool_errors,
            revisions=session.revision, wall_time_s=round(time.perf_counter() - session.started, 3),
            ledger=env.ledger.snapshot(), events=session.events)

    def decide(self, session: Session):
        raise NotImplementedError

    # helpers
    def _execute(self, session: Session, action: Action) -> dict:
        outcome = session.env.execute(action)
        session.log("executed_action", action=action.label(), outcome=outcome)
        return outcome

    @staticmethod
    def _abstain(reason: str) -> Action:
        return Action(name=ABSTAIN, params={"reason": reason})

    def _finish(self, session, action, draft, timing, report=None, executed=True, outcome=None):
        certificate = session.certificate(action, draft, timing, report)
        certificate.executed = executed
        certificate.final_action, certificate.final_params = action.name, action.params
        certificate.outcome = (outcome or {}).get("message", "")
        if action.name == ABSTAIN:
            certificate.abstention_reason = action.params.get("reason", "")
        session.log("certificate", certificate=certificate.model_dump())
        return certificate


class StandardAgent(Agent):
    """Agent A: act, then explain."""

    variant = "A_standard"

    def decide(self, session):
        decision = session.deliberate(max_steps=self.config.max_steps)
        action = decision.action if decision else self._abstain("step limit reached")
        session.log("proposed_action", action=action.label())
        outcome = self._execute(session, action)
        draft = session.explain_after(action, outcome["message"])
        return action, True, self._finish(session, action, draft, "after_action",
                                          outcome=outcome), []


class ExplainFirstAgent(Agent):
    """Agent B: certificate before acting, never verified."""

    variant = "B_explain_first"
    with_certificate = True

    def decide(self, session):
        decision = session.deliberate(max_steps=self.config.max_steps)
        if decision is None:
            action, draft = self._abstain("step limit reached"), None
        else:
            action, draft = self.review(session, decision)
        session.log("proposed_action", action=action.label())
        outcome = self._execute(session, action)
        return action, True, self._finish(session, action, draft, "before_action",
                                          outcome=outcome), []

    def review(self, session, decision: Decision):
        return decision.action, decision.draft


class SelfCheckAgent(ExplainFirstAgent):
    """B+: the same certificate plus self-review rounds. A cost-matched control:
    it spends extra model calls on checking, but nothing outside the model checks."""

    variant = "B_self_check"

    def review(self, session, decision: Decision):
        for _ in range(self.config.review_rounds):
            session.revision += 1
            session.transcript.append({"kind": "note", "text": prompts.SELF_REVIEW})
            previous = {"type": "decision", "action": decision.action.name,
                        "params": decision.action.params,
                        "certificate": decision.draft.model_dump() if decision.draft else {}}
            revised = _deliberate_with(session, self.config.max_steps, purpose="review",
                                       previous=previous)
            if revised is not None:
                decision = revised
        return decision.action, decision.draft


def _deliberate_with(session: Session, max_steps: int, purpose: str, previous: dict):
    """Deliberate with an extra view key (only the mock model reads it)."""
    original = session.view

    def view(env=None, **extra):
        return original(env, previous=previous, **extra)

    session.view = view
    try:
        return session.deliberate(purpose=purpose, max_steps=max_steps)
    finally:
        session.view = original


class PolicyVerifiedAgent(Agent):
    """Agent C: committing actions must pass the policy gate; explanation afterwards."""

    variant = "C_policy_verified"

    def decide(self, session):
        attempts = []
        while True:
            decision = session.deliberate(max_steps=self.config.max_steps)
            if decision is None:
                action = self._abstain("step limit reached")
                break
            observed = session.env.ledger.observed_facts()
            passes, rows, failures = policy_gate(session.env.domain, observed, decision.action)
            session.usage.verifications += 1
            attempts.append({"action": decision.action.label(), "policy_pass": passes,
                             "failures": failures})
            session.log("policy_check", action=decision.action.label(), passed=passes,
                        failures=failures, results=rows)
            if passes:
                action = decision.action
                break
            if session.revision >= self.config.max_revisions:
                action = self._abstain("policy check failed after revisions: "
                                       + "; ".join(failures)[:250])
                break
            session.revision += 1
            session.log("revision", reason="policy", failures=failures)
            session.transcript.append({"kind": "note", "text": prompts.policy_feedback(
                decision.action.label(), failures)})
        session.log("proposed_action", action=action.label())
        outcome = self._execute(session, action)
        draft = session.explain_after(action, outcome["message"])
        report = VerificationReport(status="PASS" if action.name != ABSTAIN else "FAIL",
                                    components_run=["policy_gate"],
                                    failures=[f for a in attempts for f in a["failures"]])
        return action, True, self._finish(session, action, draft, "after_action", report,
                                          outcome=outcome), attempts


class ECAAAgent(Agent):
    """Agent D: explanation-constrained action selection."""

    variant = "D1_ecaa_strict"
    with_certificate = True
    verified = True
    adaptive = False

    def verifier_for(self, session: Session, action: Action) -> tuple[VerifierConfig, str]:
        return self.verifier, "strict"

    def decide(self, session):
        engine = VerificationEngine(session.env.domain, self.verifier)
        attempts = []
        while True:
            decision = session.deliberate(max_steps=self.config.max_steps)
            if decision is None:
                action, draft, report = self._abstain("step limit reached"), None, None
                break
            if decision.action.name == ABSTAIN:
                action, draft, report = decision.action, decision.draft, None
                break
            config, tier = self.verifier_for(session, decision.action)
            session.log("verification_start", action=decision.action.label(), tier=tier,
                        components=list(config.components))

            def replay(fact, value, index, decision=decision):
                return session.replay(decision, fact, value, index, self.config.max_steps)

            report = engine.verify(decision.draft or ExplanationDraft(), decision.action,
                                   session.env.ledger, decision.decision_step, replay, config)
            report.risk_tier = tier
            session.usage.verifications += 1
            attempts.append({"action": decision.action.label(), "status": report.status,
                             "tier": tier, "failures": report.failures,
                             "report": report.model_dump()})
            session.log("verification", action=decision.action.label(), status=report.status,
                        tier=tier, failures=report.failures, report=report.model_dump())
            if report.status == "PASS":
                action, draft = decision.action, decision.draft
                break
            if session.revision >= self.config.max_revisions:
                action, draft = self._abstain(
                    "verification failed after revisions: " + "; ".join(report.failures)[:250]
                ), decision.draft
                break
            session.revision += 1
            session.log("revision", reason="verification", failures=report.failures)
            session.transcript.append({"kind": "note", "text": prompts.verification_feedback(
                decision.action.label(), report.failures)})
        session.log("proposed_action", action=action.label())
        outcome = self._execute(session, action)
        return action, True, self._finish(session, action, draft, "before_action", report,
                                          outcome=outcome), attempts


class AdaptiveECAAAgent(ECAAAgent):
    """D2: verification depth follows risk, evidence conflicts and reversibility."""

    variant = "D2_ecaa_adaptive"
    adaptive = True
    TIERS = {
        "low": ("provenance", "numeric", "policy"),
        "medium": ("provenance", "numeric", "policy", "contradiction", "completeness"),
        "high": ("provenance", "numeric", "policy", "contradiction", "completeness",
                 "counterfactual"),
    }

    def verifier_for(self, session, action):
        tier = risk_tier(session, action)
        return replace(self.verifier, components=self.TIERS[tier]), tier


def risk_tier(session: Session, action: Action) -> str:
    domain = session.env.domain
    observed = session.env.ledger.observed_facts()
    profile = domain.risk_profile(action, observed)
    conflicts = _conflicting_sources(session)
    missing = any(v is None for v in observed.values())
    if profile.commits and (not profile.reversible or profile.magnitude >= 0.5 or conflicts):
        return "high"
    if profile.commits or conflicts or missing:
        return "medium"
    return "low"


def _conflicting_sources(session: Session) -> bool:
    """True when a non-authoritative source states a different value for a fact
    that an authoritative source established."""
    from ecaa.verification.values import values_equal
    ledger = session.env.ledger
    observed = ledger.observed_facts()
    for evidence in ledger:
        for key, value in evidence.content.items():
            claimed = key.removeprefix("claimed.")
            if claimed != key and claimed in observed and not values_equal(value,
                                                                           observed[claimed]):
                return True
    return False


VARIANTS = {
    "A": StandardAgent, "B": ExplainFirstAgent, "B+": SelfCheckAgent, "C": PolicyVerifiedAgent,
    "D1": ECAAAgent, "D2": AdaptiveECAAAgent,
}


def make_agent(code: str, config: AgentConfig | None = None,
               verifier: VerifierConfig | None = None, name: str | None = None) -> Agent:
    return VARIANTS[code](config=config, verifier=verifier, name=name)


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]
