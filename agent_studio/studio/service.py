"""Studio back end: catalog, graph compilation and live runs.

The canvas is compiled into one of the existing agent architectures (A, B, B+,
C, D1, D2) with a verifier configuration. The studio only observes the agents and
the verifier; it does not change how they decide.
The oracle answer is computed for display after (or beside) a run and is never
passed to an agent.
"""

from __future__ import annotations

import copy
import json
import os
import queue
import threading
import time
import uuid
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from ecaa.agents import prompts
from ecaa.agents.base import AgentConfig
from ecaa.agents.variants import VARIANTS, make_agent
from ecaa.providers import make_provider
from ecaa.runtime.environment import Environment
from ecaa.verification.engine import ALL_COMPONENTS, VerifierConfig
from ecaa.domains import DOMAINS, get_domain
from ecaa.metrics import evaluate_run
from ecaa.oracle import oracle
from studio.examples import EXAMPLES

ROOT = Path(__file__).resolve().parents[1]
MAX_AGENTS_PER_RUN = 6

# Standard per-million prices used for the cost display (checked 2026-11-17).
PRICES = {"gpt-5.4-mini-2026-03-17": (0.75, 4.50)}
DEFAULT_MODEL = "gpt-5.4-mini-2026-03-17"

ARCHITECTURES = {
    "A": ("Standard", "Decides, acts, then explains afterwards. Nothing checks it."),
    "B": ("Explain first", "Writes a certificate before acting. Nothing checks it."),
    "B+": ("Self-check", "Explains first, then reviews its own decision. Only the model "
           "checks the model."),
    "C": ("Policy-verified", "Committing actions must pass the deterministic policy gate; "
          "explains afterwards."),
    "D1": ("ECAA strict", "Acts only when an independent verifier passes its certificate: "
           "evidence, arithmetic, policy, contradictions, completeness and counterfactual "
           "replay."),
    "D2": ("ECAA adaptive", "ECAA with verification depth chosen by risk, evidence "
           "conflicts and reversibility."),
}

COMPONENTS = {
    "provenance": "Every fact claim cites an observation that states that value.",
    "numeric": "Arithmetic is recomputed from the cited facts.",
    "policy": "Rule statuses are recomputed; committing actions must pass every rule.",
    "contradiction": "No claim conflicts with the evidence or another claim.",
    "completeness": "The rules that apply are addressed; refusals name the blocking rule.",
    "counterfactual": "One 'if X were different' claim is tested by re-running the decision "
                      "with that observation changed.",
}

EVENT_LOG = ROOT / "runs"  # one JSONL event log per run (git-ignored)


# --- catalog ---------------------------------------------------------------------
def _domain_info(name: str) -> dict:
    d = get_domain(name)
    return {
        "name": name, "role": d.role,
        "tools": [t.model_dump() for t in d.tools()],
        "actions": [a.model_dump() for a in d.actions()],
        "rules": [{"id": r.rule_id, "text": r.text, "governs": list(r.applies_to)}
                  for r in d.rules()],
        "procedure": d.procedure_text.strip(),
    }


def _scenarios() -> list[dict]:
    return [{**e, "source": "example"} for e in EXAMPLES]


_CATALOG: dict | None = None


def catalog() -> dict:
    global _CATALOG
    if _CATALOG is None:
        _CATALOG = {
            "domains": {n: _domain_info(n) for n in DOMAINS},
            "scenarios": _scenarios(),
            "architectures": {k: {"name": v[0], "description": v[1]}
                              for k, v in ARCHITECTURES.items()},
            "components": COMPONENTS,
            "prices": {k: {"input": v[0], "output": v[1]} for k, v in PRICES.items()},
        }
    live = {
        "openai": bool(os.environ.get("OPENAI_API_KEY")),
    }
    return {**_CATALOG, "providers": {"mock": True, **live}, "default_model": DEFAULT_MODEL}


# --- compilation --------------------------------------------------------------------
def compile_agent(spec: dict) -> tuple[str, VerifierConfig, AgentConfig]:
    """Map an agent pipeline from the canvas onto an architecture code."""
    gate = spec.get("gate", "none")
    if gate == "verifier":
        v = spec.get("verifier") or {}
        code = "D2" if v.get("adaptive") else "D1"
        components = tuple(c for c in v.get("components", ALL_COMPONENTS) if c in ALL_COMPONENTS)
        verifier = replace(VerifierConfig(), components=components or ALL_COMPONENTS,
                           counterfactual_replays=max(1, min(3, int(v.get("replays", 1)))))
    elif gate == "policy":
        code, verifier = "C", VerifierConfig()
    elif int(spec.get("self_review", 0)) > 0:
        code, verifier = "B+", VerifierConfig()
    else:
        code = "B" if spec.get("explain") == "before" else "A"
        verifier = VerifierConfig()
    config = AgentConfig(max_steps=max(3, min(30, int(spec.get("max_steps", 14)))),
                         max_revisions=max(0, min(5, int(spec.get("max_revisions", 2)))),
                         review_rounds=max(1, min(3, int(spec.get("self_review", 1) or 1))))
    return code, verifier, config


def system_prompt_for(spec: dict, domain_name: str) -> dict:
    code, _, _ = compile_agent(spec)
    cls = VARIANTS[code]
    return {"architecture": code,
            "prompt": prompts.system_prompt(get_domain(domain_name), cls.with_certificate,
                                            cls.verified)}


def _validate_state(state: dict) -> tuple[Any, dict]:
    if not isinstance(state, dict) or state.get("domain") not in DOMAINS:
        raise ValueError("environment state must name one of: " + ", ".join(DOMAINS))
    domain = get_domain(state["domain"])
    state = copy.deepcopy(state)
    state.setdefault("notes", [])
    state.setdefault("entities", [])
    for key in ("facts",):
        if not isinstance(state.get(key), dict):
            raise ValueError("environment state needs a 'facts' object")
    domain.objective(state)  # raises on a malformed state
    return domain, state


def oracle_for(state: dict) -> dict:
    domain, state = _validate_state(state)
    result = oracle(domain, state)
    return {**result.model_dump(), "label": result.label(),
            "objective": domain.objective(state)}


def _provider(spec: dict):
    kind = spec.get("provider", "mock")
    model = spec.get("model") or DEFAULT_MODEL
    price = PRICES.get(model, (None, None))
    config = {"provider": kind, "model": model,
              "temperature": float(spec.get("temperature", 0.0)), "seed": 1234,
              "input_usd_per_million": price[0], "output_usd_per_million": price[1]}
    if kind == "openai" and not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("OPENAI_API_KEY is not set; use the mock provider or add the key to .env")
    if kind == "mock":
        config["model"] = "mock"
    return make_provider(config)


# --- runs -------------------------------------------------------------------------
def run_graph(payload: dict, emit) -> None:
    """Run every agent in ``payload`` concurrently; ``emit(dict)`` streams messages."""
    domain, state = _validate_state((payload.get("environment") or {}).get("state") or {})
    agents = payload.get("agents") or []
    if not agents:
        raise ValueError("connect at least one agent from the environment to an executor")
    if len(agents) > MAX_AGENTS_PER_RUN:
        raise ValueError(f"at most {MAX_AGENTS_PER_RUN} agents per run")
    truth = oracle(domain, state)
    batch = uuid.uuid4().hex[:8]
    task_id = f"studio-{batch}"
    emit({"type": "batch_start", "batch": batch, "objective": domain.objective(state),
          "oracle": {**truth.model_dump(), "label": truth.label()}})
    lock = threading.Lock()
    log_path = EVENT_LOG / f"{time.strftime('%Y%m%d-%H%M%S')}-{batch}.jsonl"
    EVENT_LOG.mkdir(parents=True, exist_ok=True)

    def send(message: dict) -> None:
        with lock:
            emit(message)
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(message, default=str) + "\n")

    def work(spec: dict) -> None:
        agent_id = str(spec.get("id", uuid.uuid4().hex[:6]))
        try:
            code, verifier, config = compile_agent(spec)
            provider = _provider(spec)
            agent = make_agent(code, config, verifier, name=f"{code}:{spec.get('name', '')}")
            env = Environment(domain, state, f"{task_id}-{agent_id}", task_id)
            cls = VARIANTS[code]
            send({"type": "run_start", "agent_id": agent_id, "architecture": code,
                  "architecture_name": ARCHITECTURES[code][0], "model": provider.model,
                  "provider": spec.get("provider", "mock"),
                  "components": list(verifier.components) if code in ("D1", "D2") else [],
                  "system_prompt": prompts.system_prompt(domain, cls.with_certificate,
                                                         cls.verified)})

            def listener(event: dict) -> None:
                send({"type": "event", "agent_id": agent_id, "event": event})

            result = agent.run(env, provider, 0, listener=listener)
            metrics = evaluate_run(state, truth, result, domain, provider.pricing)
            send({"type": "run_end", "agent_id": agent_id, "metrics": metrics,
                  "final_action": result.final_action.label(), "executed": result.executed,
                  "abstained": result.abstained, "ledger": result.ledger,
                  "certificate": result.certificate.model_dump(),
                  "attempts": result.attempts, "usage": asdict(result.usage),
                  "wall_time_s": result.wall_time_s})
        except Exception as error:  # report, never crash the server
            send({"type": "run_error", "agent_id": agent_id,
                  "message": f"{type(error).__name__}: {error}"})

    threads = [threading.Thread(target=work, args=(spec,), daemon=True) for spec in agents]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    shown = log_path.relative_to(ROOT) if log_path.is_relative_to(ROOT) else log_path
    send({"type": "batch_end", "batch": batch, "log": str(shown)})


def stream_run(payload: dict):
    """Generator of NDJSON lines for a run (used by the HTTP handler)."""
    messages: queue.Queue = queue.Queue()
    done = object()

    def target():
        try:
            run_graph(payload, messages.put)
        except Exception as error:
            messages.put({"type": "batch_error", "message": f"{error}"})
        finally:
            messages.put(done)

    threading.Thread(target=target, daemon=True).start()
    while True:
        item = messages.get()
        if item is done:
            return
        yield json.dumps(item, default=str) + "\n"
