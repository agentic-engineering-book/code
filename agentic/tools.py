"""Executable capabilities and the function that dispatches model decisions."""
import ast
import operator

_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}
MAX_EXPRESSION_LENGTH = 200
MAX_EXPONENT = 100


def _evaluate(node):
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left, right = _evaluate(node.left), _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise ValueError("exponent too large")
        return _OPERATORS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_evaluate(node.operand))
    raise ValueError("unsupported expression")


def calculator(expression: str):
    """Evaluate arithmetic (+ - * / ** and parentheses) without eval().

    Only number literals and arithmetic operators are accepted. Length and
    exponent limits stop inputs such as 9**9**9 from exhausting the machine.
    """
    if not isinstance(expression, str) or len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError("expression must be a string of at most "
                         f"{MAX_EXPRESSION_LENGTH} characters")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise ValueError("not an arithmetic expression") from error
    return _evaluate(tree.body)


TOOLS = {"calculator": calculator}


def execute(decision, tools=TOOLS):
    """Run the tool a decision names. Software, not the model, executes it."""
    name = decision.get("action")
    if name not in tools:
        raise ValueError(f"unknown action: {name!r}")
    return tools[name](**decision.get("arguments", {}))
