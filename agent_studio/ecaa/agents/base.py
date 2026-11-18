"""Shared agent runtime: deliberation loop, transcript, usage accounting, replay.

All variants use this same loop. The variant classes differ only in what they
ask for (plain decision or certificate) and in what happens between the
decision and execution (nothing, a policy gate, or certificate verification).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any

from pydantic import ValidationError

from ecaa.agents import prompts
from ecaa.certificates.schema import Certificate, ExplanationDraft, VerificationReport
from ecaa.core.types import ABSTAIN, Action, Evidence
from ecaa.providers.base import ModelRequest, Provider
from ecaa.runtime.environment import Environment


@dataclass
class AgentConfig:
    max_steps: int = 14          # model turns per deliberation (tool calls + decision)
    max_revisions: int = 2       # policy/verification-driven revisions
    review_rounds: int = 1       # self-review rounds (cost-matched control only)


@dataclass
class Usage:
    model_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    model_latency_s: float = 0.0
    format_errors: int = 0
    provider_errors: int = 0
    replay_calls: int = 0
    replays: int = 0
    verifications: int = 0


@dataclass
class Decision:
    action: Action
    draft: ExplanationDraft | None
    decision_step: int            # ledger length when the decision was made
    transcript_index: int         # transcript length before the decision turn


@dataclass
class RunResult:
    run_id: str
    task_id: str
    variant: str
    repetition: int
    model: str
    final_action: Action
    executed: bool
    abstained: bool
    certificate: Certificate
    attempts: list[dict] = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    tool_calls: int = 0
    tool_errors: int = 0
    revisions: int = 0
    wall_time_s: float = 0.0
    ledger: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)


class Session:
    """One agent run: environment, model, transcript and accounting."""

    def __init__(self, env: Environment, provider: Provider, variant: str, repetition: int,
                 system: str, needs_certificate: bool, listener=None):
        self.env, self.provider, self.variant = env, provider, variant
        self.listener = listener  # optional callable(event) for live observers (the studio)
        self.repetition, self.system = repetition, system
        self.needs_certificate = needs_certificate
        self.transcript: list[dict] = [{"kind": "objective", "text": env.objective}]
        self.usage = Usage()
        self.events: list[dict] = []
        self.revision = 0
        self.started = time.perf_counter()
        self.log("task_start", objective=env.objective, variant=variant, model=provider.model)

    def log(self, event: str, **payload: Any) -> None:
        record = {"event": event, "t": round(time.perf_counter() - self.started, 4),
                  "run_id": self.env.run_id, "task_id": self.env.task_id, **payload}
        self.events.append(record)
        if self.listener is not None:
            self.listener(record)

    # --- rendering -------------------------------------------------------------
    def messages(self, transcript: list[dict] | None = None,
                 override: tuple[str, Any] | None = None) -> list[dict]:
        rendered = [{"role": "system", "content": self.system}]
        for item in (self.transcript if transcript is None else transcript):
            kind = item["kind"]
            if kind == "objective":
                rendered.append({"role": "user", "content": item["text"]})
            elif kind == "model":
                rendered.append({"role": "assistant", "content": item["text"]})
            elif kind == "observation":
                evidence: Evidence | None = item.get("evidence")
                if evidence is None:
                    rendered.append({"role": "user", "content": item["error"]})
                else:
                    content = dict(evidence.content)
                    if override and override[0] in content:
                        content[override[0]] = override[1]
                    rendered.append({"role": "user", "content": prompts.observation_text(
                        evidence.evidence_id, evidence.tool, evidence.args, content)})
            else:  # note: feedback or instruction
                rendered.append({"role": "user", "content": item["text"]})
        return rendered

    def view(self, env: Environment | None = None, **extra: Any) -> dict:
        env = env or self.env
        fact_evidence = {}
        for evidence in env.ledger:
            for key in evidence.authoritative_keys:
                if key in evidence.content:
                    fact_evidence[key] = evidence.evidence_id
        return {"domain": env.domain, "observed": env.ledger.observed_facts(),
                "fact_evidence": fact_evidence, "public": env.public_view(),
                "calls_made": [(e.tool, e.args) for e in env.ledger],
                "run_seed": [env.task_id, self.repetition],
                "revision": self.revision, "needs_certificate": self.needs_certificate, **extra}

    # --- model calls -----------------------------------------------------------
    def ask(self, purpose: str, messages: list[dict], view: dict) -> dict | None:
        response = self.provider.complete(ModelRequest(purpose, messages, view))
        self.usage.model_calls += 1
        self.usage.input_tokens += response.input_tokens
        self.usage.output_tokens += response.output_tokens
        self.usage.model_latency_s += response.latency_s
        if purpose == "replay":
            self.usage.replay_calls += 1
        self.log("model_call", purpose=purpose, input_tokens=response.input_tokens,
                 output_tokens=response.output_tokens, latency_s=response.latency_s,
                 error=response.error, text=response.text[:4000])
        if response.error:
            self.usage.provider_errors += 1
            return None
        if response.content is None:
            self.usage.format_errors += 1
        return response.content

    def deliberate(self, env: Environment | None = None, transcript: list[dict] | None = None,
                   override: tuple[str, Any] | None = None, purpose: str = "step",
                   max_steps: int = 14) -> Decision | None:
        """Call tools until the model returns a decision. ``env``/``transcript``/
        ``override`` are set only for counterfactual replays."""
        env = env or self.env
        transcript = self.transcript if transcript is None else transcript
        replay = override is not None
        for _ in range(max_steps):
            content = self.ask(purpose, self.messages(transcript, override),
                               self.view(env) if not replay else self._replay_view(env, override))
            if content is None:
                transcript.append({"kind": "note", "text":
                                   "Your reply was not a single valid JSON object. Reply again."})
                continue
            transcript.append({"kind": "model", "text": json.dumps(content, default=str)})
            kind = content.get("type")
            if kind == "tool_call":
                tool, args = str(content.get("tool", "")), content.get("args") or {}
                if not isinstance(args, dict):
                    args = {}
                result = env.call_tool(tool, args)
                if isinstance(result, Evidence):
                    if override and override[0] in result.content:
                        result = _overridden(env, result, override)
                    transcript.append({"kind": "observation", "evidence": result})
                    if not replay:
                        self.log("tool_response", tool=tool, args=args,
                                 evidence_id=result.evidence_id, content=result.content,
                                 authoritative_keys=list(result.authoritative_keys))
                else:
                    transcript.append({"kind": "observation", "error": result})
                    if not replay:
                        self.log("tool_error", tool=tool, args=args, message=result)
                continue
            if kind == "decision":
                decision = self._parse_decision(content, env, transcript, replay)
                if decision is not None:
                    return decision
                continue
            transcript.append({"kind": "note", "text":
                               'Reply with "type": "tool_call" or "type": "decision".'})
        return None

    def _parse_decision(self, content: dict, env: Environment, transcript: list[dict],
                        replay: bool) -> Decision | None:
        name = str(content.get("action", ""))
        params = content.get("params") or {}
        if not isinstance(params, dict):
            params = {}
        spec = env.domain.action_spec(name)
        if name != ABSTAIN and spec is None:
            transcript.append({"kind": "note", "text": f"'{name}' is not an available action."})
            return None
        if spec is not None:  # keep only the parameters the action defines
            params = {k: v for k, v in params.items() if k in spec.parameters}
        draft = None
        if self.needs_certificate and not replay and name != ABSTAIN:
            try:
                draft = ExplanationDraft.model_validate(content.get("certificate") or {})
            except ValidationError as error:
                self.usage.format_errors += 1
                transcript.append({"kind": "note", "text": "The certificate is not valid: "
                                   + _short_errors(error) + ". Reply again."})
                return None
        if name == ABSTAIN:
            params = {"reason": str(params.get("reason", content.get("reason", "")))[:300]}
        index = len(transcript) - 1
        if not replay:
            self.log("decision_proposed", action=Action(name=name, params=params).label(),
                     revision=self.revision,
                     certificate=draft.model_dump() if draft is not None else None)
        return Decision(Action(name=name, params=params), draft, len(env.ledger), index)

    def _replay_view(self, env: Environment, override: tuple[str, Any]) -> dict:
        view = self.view(env, purpose="replay")
        if override[0] in view["observed"]:
            view["observed"][override[0]] = override[1]
        return view

    def replay(self, decision: Decision, fact: str, value: Any, index: int,
               max_steps: int) -> Action | None:
        """Re-run the decision from the same point with one observation changed.

        The transcript is cut just before the decision turn and every rendered
        observation of ``fact`` shows ``value``; tools called during the replay
        are served by a fresh environment whose results show the same override.
        """
        self.usage.replays += 1
        self.log("counterfactual_replay_start", fact=fact, value=value, replay=index)
        cut = self.transcript[:decision.transcript_index]
        env = self.env.fresh(f"{self.env.run_id}-cf{self.usage.replays}")
        for item in cut:  # restore the same ledger so evidence ids keep their meaning
            if item["kind"] == "observation" and item.get("evidence") is not None:
                e = item["evidence"]
                env.ledger.add(e.tool, e.args, e.content, e.authoritative_keys)
        result = self.deliberate(env=env, transcript=list(cut), override=(fact, value),
                                 purpose="replay", max_steps=max_steps)
        self.log("counterfactual_replay", fact=fact, value=value, replay=index,
                 action=result.action.label() if result else None)
        return result.action if result else None

    def explain_after(self, decision: Action, outcome: str) -> ExplanationDraft:
        """Post-hoc explanation (Agents A and C)."""
        self.transcript.append({"kind": "note", "text": prompts.explain_request(
            decision.label(), outcome)})
        for _ in range(2):
            content = self.ask("explain", self.messages(), self.view(decision=decision))
            if content is not None:
                self.transcript.append({"kind": "model",
                                        "text": json.dumps(content, default=str)})
                try:
                    return ExplanationDraft.model_validate(content.get("certificate") or content)
                except ValidationError as error:
                    self.usage.format_errors += 1
                    self.transcript.append({"kind": "note", "text": "The certificate is not "
                                            "valid: " + _short_errors(error) + ". Reply again."})
        return ExplanationDraft(summary="(no valid explanation produced)")

    def certificate(self, decision: Action, draft: ExplanationDraft | None, timing: str,
                    report: VerificationReport | None = None) -> Certificate:
        applicable = [r.rule_id for r in self.env.domain.rules() if r.applies(decision)]
        return Certificate(
            task_id=self.env.task_id, run_id=self.env.run_id,
            decision_id=f"{self.env.run_id}-d{self.revision}", agent_variant=self.variant,
            model=self.provider.model, objective=self.env.objective,
            observed_evidence_ids=[e.evidence_id for e in self.env.ledger],
            proposed_action=decision.name, proposed_params=decision.params,
            applicable_rules=applicable, explanation_timing=timing,
            explanation=draft or ExplanationDraft(),
            verification=report or VerificationReport(), revision_count=self.revision)


def _overridden(env: Environment, evidence: Evidence, override: tuple[str, Any]) -> Evidence:
    """Replace the just-recorded evidence with a copy showing the override."""
    content = {**evidence.content, override[0]: override[1]}
    env.ledger._items.pop()
    env.ledger._by_id.pop(evidence.evidence_id, None)
    return env.ledger.add(evidence.tool, evidence.args, content, evidence.authoritative_keys)


def _short_errors(error: ValidationError) -> str:
    return "; ".join(f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}"
                     for e in error.errors()[:4])
