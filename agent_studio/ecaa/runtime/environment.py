"""Sandboxed environment: tools read the hidden state, actions are only recorded."""

from __future__ import annotations

import copy
from typing import Any

from ecaa.core.domain import DomainAdapter, ToolError
from ecaa.core.types import ABSTAIN, Action, Evidence
from ecaa.runtime.ledger import EvidenceLedger


class Environment:
    def __init__(self, domain: DomainAdapter, state: dict, run_id: str, task_id: str):
        self.domain = domain
        self._state = copy.deepcopy(state)
        self.run_id, self.task_id = run_id, task_id
        self.ledger = EvidenceLedger(run_id, task_id)
        self.executed: list[Action] = []
        self.tool_calls = 0
        self.tool_errors = 0

    @property
    def objective(self) -> str:
        return self.domain.objective(self._state)

    def public_view(self) -> dict:
        """What any agent may know without calling a tool (entity ids only)."""
        return {"entities": list(self._state.get("entities", []))}

    def call_tool(self, name: str, args: dict[str, Any]) -> Evidence | str:
        """Return new evidence, or an error message for an invalid request."""
        self.tool_calls += 1
        spec = next((t for t in self.domain.tools() if t.name == name), None)
        if spec is None or not spec.read_only:
            self.tool_errors += 1
            return f"Tool '{name}' is not available."
        try:
            content, keys = self.domain.call_tool(self._state, name, dict(args or {}))
        except ToolError as error:
            self.tool_errors += 1
            return f"Tool '{name}' refused the request: {error}"
        return self.ledger.add(name, dict(args or {}), content, keys)

    def execute(self, action: Action) -> dict[str, Any]:
        """Record a terminal decision. Nothing outside the sandbox is touched."""
        spec = self.domain.action_spec(action.name)
        if action.name != ABSTAIN and spec is None:
            return {"executed": False, "message": f"Unknown action '{action.name}'."}
        self.executed.append(action)
        return {"executed": True, "sandboxed": True,
                "message": f"SANDBOX: {action.label()} recorded; no external effect."}

    def with_intervention(self, key: str, value: Any, run_id: str) -> Environment:
        """A fresh environment that differs from this one only in fact ``key``."""
        state = self.domain.apply_intervention(self._state, key, value)
        return Environment(self.domain, state, run_id, self.task_id)

    def fresh(self, run_id: str) -> Environment:
        return Environment(self.domain, self._state, run_id, self.task_id)
