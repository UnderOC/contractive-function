from __future__ import annotations

from decimal import Decimal

from contractive_tool.frontend.ast import (
    Annotation,
    Assert,
    Assign,
    Assume,
    Binary,
    BooleanConstant,
    BoolBinary,
    BoolUnary,
    Compare,
    DistributionExpr,
    Expr,
    If,
    Number,
    ProbChoice,
    Program,
    RandomDeclaration,
    Refute,
    Sequence,
    Skip,
    Unary,
    Variable,
    While,
)


def _number(value: Decimal, template: Expr) -> Number:
    if value == value.to_integral():
        text = str(value.to_integral())
    else:
        text = format(value.normalize(), "f")
    return Number(text, template.span)


def normalize_expr(expr: Expr) -> Expr:
    if isinstance(expr, (Number, Variable, BooleanConstant)):
        return expr
    if isinstance(expr, Unary):
        operand = normalize_expr(expr.operand)
        if isinstance(operand, Number):
            value = operand.decimal
            return _number(-value if expr.operator == "-" else value, expr)
        return Unary(expr.operator, operand, expr.span)
    if isinstance(expr, Binary):
        left, right = normalize_expr(expr.left), normalize_expr(expr.right)
        if isinstance(left, Number) and isinstance(right, Number):
            operations = {
                "+": lambda a, b: a + b,
                "-": lambda a, b: a - b,
                "*": lambda a, b: a * b,
            }
            return _number(operations[expr.operator](left.decimal, right.decimal), expr)
        return Binary(expr.operator, left, right, expr.span)
    if isinstance(expr, Compare):
        left, right = normalize_expr(expr.left), normalize_expr(expr.right)
        operator = {"==": "=", "≤": "<=", "≥": ">=", "≠": "!="}.get(
            expr.operator, expr.operator
        )
        if isinstance(left, Number) and isinstance(right, Number):
            a, b = left.decimal, right.decimal
            comparisons = {
                "<": a < b,
                "<=": a <= b,
                ">": a > b,
                ">=": a >= b,
                "=": a == b,
                "==": a == b,
                "!=": a != b,
            }
            return BooleanConstant(comparisons[operator], expr.span)
        return Compare(operator, left, right, expr.span)
    if isinstance(expr, BoolUnary):
        operand = normalize_expr(expr.operand)
        if isinstance(operand, BooleanConstant):
            return BooleanConstant(not operand.value, expr.span)
        if isinstance(operand, BoolUnary):
            return normalize_expr(operand.operand)
        return BoolUnary("not", operand, expr.span)
    if isinstance(expr, BoolBinary):
        left, right = normalize_expr(expr.left), normalize_expr(expr.right)
        if isinstance(left, BooleanConstant):
            if expr.operator == "and":
                return right if left.value else left
            return left if left.value else right
        if isinstance(right, BooleanConstant):
            if expr.operator == "and":
                return left if right.value else right
            return right if right.value else left
        return BoolBinary(expr.operator, left, right, expr.span)
    if isinstance(expr, ProbChoice):
        return ProbChoice(normalize_expr(expr.probability), expr.span)
    if isinstance(expr, DistributionExpr):
        name = "Uniform" if expr.name == "Unif" else expr.name
        return DistributionExpr(name, tuple(normalize_expr(a) for a in expr.arguments), expr.span)
    raise TypeError(type(expr).__name__)


def _normalize_sequence(sequence: Sequence) -> Sequence:
    statements = []
    for stmt in sequence.statements:
        if isinstance(stmt, Skip):
            statements.append(stmt)
        elif isinstance(stmt, Assign):
            statements.append(Assign(stmt.target, normalize_expr(stmt.value), stmt.span))
        elif isinstance(stmt, Annotation):
            statements.append(Annotation(normalize_expr(stmt.predicate), stmt.span))
        elif isinstance(stmt, Assert):
            statements.append(Assert(normalize_expr(stmt.condition), stmt.span))
        elif isinstance(stmt, Refute):
            statements.append(Refute(normalize_expr(stmt.condition), stmt.span))
        elif isinstance(stmt, Assume):
            statements.append(Assume(normalize_expr(stmt.condition), stmt.span))
        elif isinstance(stmt, If):
            statements.append(
                If(
                    normalize_expr(stmt.condition),
                    _normalize_sequence(stmt.then_branch),
                    _normalize_sequence(stmt.else_branch),
                    stmt.span,
                )
            )
        elif isinstance(stmt, While):
            statements.append(
                While(
                    normalize_expr(stmt.guard),
                    normalize_expr(stmt.invariant) if stmt.invariant else None,
                    _normalize_sequence(stmt.body),
                    stmt.span,
                )
            )
        else:
            raise TypeError(type(stmt).__name__)
    return Sequence(tuple(statements), sequence.span)


def normalize_program(program: Program) -> Program:
    declarations = tuple(
        RandomDeclaration(
            item.name,
            normalize_expr(item.distribution),
            item.span,
        )
        for item in program.declarations
    )
    return Program(declarations, _normalize_sequence(program.body), program.source_file)
