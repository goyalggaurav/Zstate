"""Restricted AST evaluator for Python_Interpreter / calculator tools."""

from __future__ import annotations

import ast
import operator

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
}


def safe_calc(expression: str) -> float:
    node = ast.parse(expression.strip(), mode="eval").body

    def _eval(n: ast.AST) -> float:
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.BinOp):
            return OPS[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.USub):
            return OPS[ast.USub](_eval(n.operand))
        raise ValueError(f"Unsupported expression: {expression}")

    return _eval(node)
