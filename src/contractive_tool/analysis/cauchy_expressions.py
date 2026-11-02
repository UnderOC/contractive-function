"""Small arithmetic-only parser for configs and proof artifact expressions."""
import ast
import sympy as sp

from contractive_tool.errors import AnalysisError


def parse_expression(text, symbols):
    symbols = {str(s): s for s in symbols}
    if not isinstance(text, str):
        raise AnalysisError('Expected an arithmetic expression string')
    try:
        tree = ast.parse(text, mode='eval')
    except SyntaxError as error:
        raise AnalysisError('Invalid arithmetic expression') from error

    def visit(node):
        if isinstance(node, ast.Name) and node.id in symbols:
            return symbols[node.id]
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return sp.Rational(ast.get_source_segment(text, node))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Add):
                return left+right
            if isinstance(node.op, ast.Sub):
                return left-right
            if isinstance(node.op, ast.Mult):
                return left*right
            if isinstance(node.op, ast.Div) and right.is_Rational and right != 0:
                return left/right
            if isinstance(node.op, ast.Pow) and right.is_Integer and 0 <= right <= 64:
                return left**right
        raise AnalysisError('Only declared symbols and polynomial arithmetic are allowed')

    return sp.expand(visit(tree.body))
