from __future__ import annotations

from decimal import Decimal

from contractive_tool.errors import Diagnostic, SemanticError
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
    Refute,
    Sequence,
    Unary,
    Variable,
    While,
)
from contractive_tool.frontend.normalize import normalize_program
from contractive_tool.ir.program import ProgramIR, ProgramSymbols


def _walk_statements(sequence: Sequence):
    for stmt in sequence.statements:
        yield stmt
        if isinstance(stmt, If):
            yield from _walk_statements(stmt.then_branch)
            yield from _walk_statements(stmt.else_branch)
        elif isinstance(stmt, While):
            yield from _walk_statements(stmt.body)


def _walk_expr(expr: Expr):
    yield expr
    if isinstance(expr, (Unary, BoolUnary)):
        yield from _walk_expr(expr.operand)
    elif isinstance(expr, (Binary, BoolBinary, Compare)):
        yield from _walk_expr(expr.left)
        yield from _walk_expr(expr.right)
    elif isinstance(expr, ProbChoice):
        yield from _walk_expr(expr.probability)
    elif isinstance(expr, DistributionExpr):
        for argument in expr.arguments:
            yield from _walk_expr(argument)


def _is_arithmetic(expr: Expr) -> bool:
    return isinstance(expr, (Number, Variable, Unary, Binary))


def _is_boolean(expr: Expr) -> bool:
    return isinstance(expr, (BooleanConstant, Compare, BoolUnary, BoolBinary, ProbChoice))


def _diagnostic(message: str, expr_or_stmt) -> Diagnostic:
    span = expr_or_stmt.span
    return Diagnostic(message, span.file, span.start_line, span.start_column)


def _validate_distribution(distribution: DistributionExpr, diagnostics: list[Diagnostic]) -> None:
    arities = {"Uniform": 2, "Normal": 2, "Bernoulli": 1}
    expected = arities.get(distribution.name)
    if expected is None:
        diagnostics.append(_diagnostic(f"unsupported distribution '{distribution.name}'", distribution))
        return
    if len(distribution.arguments) != expected:
        diagnostics.append(
            _diagnostic(
                f"{distribution.name} expects {expected} argument(s), got {len(distribution.arguments)}",
                distribution,
            )
        )
        return
    if not all(isinstance(arg, Number) for arg in distribution.arguments):
        diagnostics.append(
            _diagnostic(f"{distribution.name} parameters must be numeric constants", distribution)
        )
        return
    values = [arg.decimal for arg in distribution.arguments]
    if distribution.name == "Uniform" and values[0] >= values[1]:
        diagnostics.append(_diagnostic("Uniform requires lower bound < upper bound", distribution))
    elif distribution.name == "Normal" and values[1] <= 0:
        diagnostics.append(_diagnostic("Normal requires a positive standard deviation", distribution))
    elif distribution.name == "Bernoulli" and not Decimal(0) <= values[0] <= Decimal(1):
        diagnostics.append(_diagnostic("Bernoulli probability must be in [0, 1]", distribution))


def check_program(program: Program) -> ProgramIR:
    """Normalize and type-check a source AST, returning bound Program IR."""
    program = normalize_program(program)
    diagnostics: list[Diagnostic] = []

    declarations: dict[str, DistributionExpr] = {}
    for declaration in program.declarations:
        if declaration.name in declarations:
            diagnostics.append(_diagnostic(f"duplicate random declaration '{declaration.name}'", declaration))
        declarations[declaration.name] = declaration.distribution
        _validate_distribution(declaration.distribution, diagnostics)

    assignments = [stmt for stmt in _walk_statements(program.body) if isinstance(stmt, Assign)]
    program_variables = {stmt.target for stmt in assignments}
    for assignment in assignments:
        if assignment.target in declarations:
            diagnostics.append(
                _diagnostic(
                    f"cannot assign to declared random variable '{assignment.target}'", assignment
                )
            )

    known_names = program_variables | declarations.keys()

    def validate_expr(expr: Expr, *, allow_random: bool, allow_prob: bool = False) -> None:
        for item in _walk_expr(expr):
            if isinstance(item, Variable):
                if item.name not in known_names:
                    diagnostics.append(_diagnostic(f"unknown variable '{item.name}'", item))
                elif item.name in declarations and not allow_random:
                    diagnostics.append(
                        _diagnostic(
                            f"random variable '{item.name}' is not allowed in guards or invariants", item
                        )
                    )
            elif isinstance(item, ProbChoice) and not allow_prob:
                diagnostics.append(
                    _diagnostic("prob(...) is only valid as the direct condition of an if", item)
                )

    for stmt in _walk_statements(program.body):
        if isinstance(stmt, Assign):
            if isinstance(stmt.value, DistributionExpr):
                _validate_distribution(stmt.value, diagnostics)
            else:
                if not _is_arithmetic(stmt.value):
                    diagnostics.append(_diagnostic("assignment requires an arithmetic expression", stmt.value))
                validate_expr(stmt.value, allow_random=True)
        elif isinstance(stmt, If):
            if isinstance(stmt.condition, ProbChoice):
                probability = stmt.condition.probability
                if not _is_arithmetic(probability):
                    diagnostics.append(_diagnostic("probability must be arithmetic", probability))
                validate_expr(probability, allow_random=False)
                if isinstance(probability, Number) and not Decimal(0) <= probability.decimal <= Decimal(1):
                    diagnostics.append(_diagnostic("probability must be in [0, 1]", probability))
            else:
                if not _is_boolean(stmt.condition):
                    diagnostics.append(_diagnostic("if condition must be boolean", stmt.condition))
                validate_expr(stmt.condition, allow_random=False)
        elif isinstance(stmt, While):
            if not _is_boolean(stmt.guard):
                diagnostics.append(_diagnostic("while guard must be boolean", stmt.guard))
            validate_expr(stmt.guard, allow_random=False)
            if stmt.invariant:
                validate_expr(stmt.invariant, allow_random=False)
        elif isinstance(stmt, (Assert, Refute, Assume)):
            if not _is_boolean(stmt.condition):
                diagnostics.append(_diagnostic("statement condition must be boolean", stmt.condition))
            validate_expr(stmt.condition, allow_random=False)
        elif isinstance(stmt, Annotation):
            if not _is_boolean(stmt.predicate):
                diagnostics.append(_diagnostic("annotation must be boolean", stmt.predicate))
            validate_expr(stmt.predicate, allow_random=False)

    if diagnostics:
        raise SemanticError(diagnostics)
    symbols = ProgramSymbols(tuple(sorted(program_variables)), tuple(sorted(declarations)))
    return ProgramIR(program, symbols, declarations)

