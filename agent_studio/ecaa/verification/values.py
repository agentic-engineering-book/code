"""Value normalisation and a safe arithmetic evaluator shared by the verifiers."""

from __future__ import annotations

import ast
import math
import operator
import re
from typing import Any

_TRUE = {"true", "yes", "y", "approved", "1"}
_FALSE = {"false", "no", "n", "not approved", "0"}
_NONE = {"none", "null", "unknown", "missing", "not on file", "n/a", ""}


def normalise(value: Any) -> Any:
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        text = value.strip().lower()
        if text in _NONE:
            return None
        if text in _TRUE:
            return True
        if text in _FALSE:
            return False
        number = re.fullmatch(r"[r$]?\s*(-?[\d,]*\.?\d+)\s*%?", text)
        if number:
            try:
                return float(number.group(1).replace(",", ""))
            except ValueError:
                pass
        return text
    return value


def values_equal(a: Any, b: Any, rel_tol: float = 1e-3, abs_tol: float = 1e-6) -> bool:
    a, b = normalise(a), normalise(b)
    if isinstance(a, float) and isinstance(b, float):
        return math.isclose(a, b, rel_tol=rel_tol, abs_tol=abs_tol)
    return a == b


_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow}
_CMP = {ast.Lt: operator.lt, ast.LtE: operator.le, ast.Gt: operator.gt,
        ast.GtE: operator.ge, ast.Eq: operator.eq, ast.NotEq: operator.ne}
_FUNCS = {"min": min, "max": max, "abs": abs, "round": round}

PLACEHOLDER = re.compile(r"\{([A-Za-z0-9_.\-]+)\}")


class ExpressionError(ValueError):
    pass


def evaluate(expression: str, bindings: dict[str, float]) -> float:
    """Evaluate arithmetic with ``{fact}`` placeholders. No names, calls or
    attributes beyond min/max/abs/round are allowed."""
    names: dict[str, float] = {}

    def bind(match: re.Match) -> str:
        key = match.group(1)
        if key not in bindings:
            raise ExpressionError(f"unbound fact {key}")
        name = f"_v{len(names)}"
        names[name] = bindings[key]
        return name

    source = PLACEHOLDER.sub(bind, expression).replace("×", "*").replace("−", "-")
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as error:
        raise ExpressionError(f"cannot parse expression: {expression}") from error

    def walk(node: ast.AST) -> Any:
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in names:
            value = names[node.id]
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise ExpressionError(f"fact value is not numeric: {value!r}")
            return float(value)
        if isinstance(node, ast.BinOp) and type(node.op) in _BIN:
            return _BIN[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -walk(node.operand)
        if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in _CMP:
            return float(_CMP[type(node.ops[0])](walk(node.left), walk(node.comparators[0])))
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in _FUNCS and not node.keywords):
            return float(_FUNCS[node.func.id](*[walk(a) for a in node.args]))
        raise ExpressionError(f"unsupported expression element: {ast.dump(node)[:60]}")

    try:
        return float(walk(tree))
    except ZeroDivisionError as error:
        raise ExpressionError("division by zero") from error
