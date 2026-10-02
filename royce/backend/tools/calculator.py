"""Safe calculator — no eval()."""

from __future__ import annotations

import ast
import operator
from typing import Any, Dict

from tools.registry import ToolDefinition, registry

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.Num):  # py<3.8 compat
        return float(node.n)
    if isinstance(node, ast.BinOp):
        op = OPS.get(type(node.op))
        if not op:
            raise ValueError("Unsupported operator")
        return op(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op = OPS.get(type(node.op))
        if not op:
            raise ValueError("Unsupported unary operator")
        return op(_eval_node(node.operand))
    raise ValueError("Unsupported expression")


def safe_calculate(expression: str) -> float:
    tree = ast.parse(expression.strip(), mode="eval")
    return _eval_node(tree)


async def calculator_handler(args: Dict[str, Any], *, user_id: str) -> Dict[str, Any]:
    expr = str(args.get("expression", "")).strip()
    if not expr or len(expr) > 200:
        return {"error": "Invalid expression"}
    try:
        result = safe_calculate(expr)
        return {"expression": expr, "result": result}
    except Exception as e:
        return {"error": f"Could not evaluate: {e}"}


registry.register(
    ToolDefinition(
        name="calculator",
        description="Evaluate a mathematical expression safely. Supports +, -, *, /, //, %, ** and parentheses.",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression, e.g. '(84729 * 392) + 10'",
                }
            },
            "required": ["expression"],
        },
    ),
    calculator_handler,
)
