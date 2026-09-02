from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceSpan:
    file: str
    start_line: int
    start_column: int
    end_line: int
    end_column: int

    @classmethod
    def synthetic(cls, file: str = "<generated>") -> "SourceSpan":
        return cls(file, 1, 1, 1, 1)


class Expr:
    span: SourceSpan


@dataclass(frozen=True)
class Number(Expr):
    text: str
    span: SourceSpan

    @property
    def decimal(self) -> Decimal:
        return Decimal(self.text)


@dataclass(frozen=True)
class Variable(Expr):
    name: str
    span: SourceSpan


@dataclass(frozen=True)
class Unary(Expr):
    operator: str
    operand: Expr
    span: SourceSpan


@dataclass(frozen=True)
class Binary(Expr):
    operator: str
    left: Expr
    right: Expr
    span: SourceSpan


@dataclass(frozen=True)
class BooleanConstant(Expr):
    value: bool
    span: SourceSpan


@dataclass(frozen=True)
class Compare(Expr):
    operator: str
    left: Expr
    right: Expr
    span: SourceSpan


@dataclass(frozen=True)
class BoolUnary(Expr):
    operator: str
    operand: Expr
    span: SourceSpan


@dataclass(frozen=True)
class BoolBinary(Expr):
    operator: str
    left: Expr
    right: Expr
    span: SourceSpan


@dataclass(frozen=True)
class ProbChoice(Expr):
    probability: Expr
    span: SourceSpan


@dataclass(frozen=True)
class DistributionExpr(Expr):
    name: str
    arguments: tuple[Expr, ...]
    span: SourceSpan


class Stmt:
    span: SourceSpan


@dataclass(frozen=True)
class Skip(Stmt):
    span: SourceSpan


@dataclass(frozen=True)
class Assign(Stmt):
    target: str
    value: Expr
    span: SourceSpan


@dataclass(frozen=True)
class Sequence(Stmt):
    statements: tuple[Stmt, ...]
    span: SourceSpan


@dataclass(frozen=True)
class If(Stmt):
    condition: Expr
    then_branch: Sequence
    else_branch: Sequence
    span: SourceSpan


@dataclass(frozen=True)
class While(Stmt):
    guard: Expr
    invariant: Expr | None
    body: Sequence
    span: SourceSpan


@dataclass(frozen=True)
class Assert(Stmt):
    condition: Expr
    span: SourceSpan


@dataclass(frozen=True)
class Refute(Stmt):
    condition: Expr
    span: SourceSpan


@dataclass(frozen=True)
class Assume(Stmt):
    condition: Expr
    span: SourceSpan


@dataclass(frozen=True)
class Annotation(Stmt):
    predicate: Expr
    span: SourceSpan


@dataclass(frozen=True)
class RandomDeclaration:
    name: str
    distribution: DistributionExpr
    span: SourceSpan


@dataclass(frozen=True)
class Program:
    declarations: tuple[RandomDeclaration, ...]
    body: Sequence
    source_file: str


def ast_to_data(value: Any) -> Any:
    """Convert AST dataclasses into stable, JSON-compatible objects."""
    if is_dataclass(value):
        result: dict[str, Any] = {"node": type(value).__name__}
        for field in fields(value):
            result[field.name] = ast_to_data(getattr(value, field.name))
        return result
    if isinstance(value, tuple):
        return [ast_to_data(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    return value


_ARITH_PRECEDENCE = {"+": 10, "-": 10, "*": 20}
_BOOL_PRECEDENCE = {"or": 1, "and": 2}


def format_expr(expr: Expr, parent_precedence: int = 0) -> str:
    if isinstance(expr, Number):
        return expr.text
    if isinstance(expr, Variable):
        return expr.name
    if isinstance(expr, BooleanConstant):
        return "true" if expr.value else "false"
    if isinstance(expr, Unary):
        text = f"{expr.operator}{format_expr(expr.operand, 30)}"
        return f"({text})" if parent_precedence > 30 else text
    if isinstance(expr, Binary):
        precedence = _ARITH_PRECEDENCE[expr.operator]
        text = (
            f"{format_expr(expr.left, precedence)} {expr.operator} "
            f"{format_expr(expr.right, precedence + (1 if expr.operator == '-' else 0))}"
        )
        return f"({text})" if parent_precedence > precedence else text
    if isinstance(expr, Compare):
        return f"{format_expr(expr.left)} {expr.operator} {format_expr(expr.right)}"
    if isinstance(expr, BoolUnary):
        text = f"not {format_expr(expr.operand, 3)}"
        return f"({text})" if parent_precedence > 3 else text
    if isinstance(expr, BoolBinary):
        precedence = _BOOL_PRECEDENCE[expr.operator]
        text = (
            f"{format_expr(expr.left, precedence)} {expr.operator} "
            f"{format_expr(expr.right, precedence + 1)}"
        )
        return f"({text})" if parent_precedence > precedence else text
    if isinstance(expr, ProbChoice):
        return f"prob({format_expr(expr.probability)})"
    if isinstance(expr, DistributionExpr):
        args = ", ".join(format_expr(arg) for arg in expr.arguments)
        return f"{expr.name}({args})"
    raise TypeError(f"unsupported expression: {type(expr).__name__}")


def negate(expr: Expr) -> Expr:
    if isinstance(expr, BooleanConstant):
        return BooleanConstant(not expr.value, expr.span)
    if isinstance(expr, BoolUnary) and expr.operator == "not":
        return expr.operand
    return BoolUnary("not", expr, expr.span)

