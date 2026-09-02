from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import sympy as sp

from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.ast import Binary, Expr, Number, Unary, Variable
from contractive_tool.ir.cfg import Update


def _exact_number(text: str) -> sp.Rational:
    """Interpret source decimals as exact rationals, never binary floats."""
    return sp.Rational(text)


def arithmetic_to_symbolic(expr: Expr | sp.Expr | int | str) -> sp.Expr:
    if isinstance(expr, sp.Expr):
        return expr
    if isinstance(expr, int):
        return sp.Integer(expr)
    if isinstance(expr, str):
        return sp.sympify(expr, rational=True)
    if isinstance(expr, Number):
        return _exact_number(expr.text)
    if isinstance(expr, Variable):
        return sp.Symbol(expr.name)
    if isinstance(expr, Unary):
        operand = arithmetic_to_symbolic(expr.operand)
        return operand if expr.operator == "+" else -operand
    if isinstance(expr, Binary):
        left = arithmetic_to_symbolic(expr.left)
        right = arithmetic_to_symbolic(expr.right)
        if expr.operator == "+":
            return left + right
        if expr.operator == "-":
            return left - right
        if expr.operator == "*":
            return left * right
    raise AnalysisError(f"expression is not polynomial arithmetic: {type(expr).__name__}")


@dataclass(frozen=True)
class Polynomial:
    """Backend-neutral polynomial value; the SymPy expression is adapter-private."""

    _expression: sp.Expr

    @property
    def expression(self) -> sp.Expr:
        """Escape hatch for lowering modules; callers should prefer the service API."""
        return self._expression

    def __str__(self) -> str:
        return sp.sstr(self._expression)

    def to_data(self) -> dict[str, object]:
        return {"kind": "polynomial", "expression": str(self)}


class PolynomialService:
    """Thin, stable adapter for normalization, coefficients and simultaneous updates."""

    def normalize(self, expr: Expr | sp.Expr | Polynomial | int | str) -> Polynomial:
        raw = expr.expression if isinstance(expr, Polynomial) else arithmetic_to_symbolic(expr)
        expanded = sp.expand(raw)
        try:
            symbols = sorted(expanded.free_symbols, key=lambda item: item.name)
            if symbols:
                sp.Poly(expanded, *symbols)
            elif expanded.is_number is not True:
                raise sp.PolynomialError
        except sp.PolynomialError as error:
            raise AnalysisError(f"expression is not a polynomial: {expanded}") from error
        return Polynomial(expanded)

    def symbol(self, name: str) -> sp.Symbol:
        return sp.Symbol(name)

    def substitute(
        self,
        poly: Polynomial,
        update: Update | Mapping[str, Expr | sp.Expr | Polynomial | int | str],
    ) -> Polynomial:
        assignments = update.assignments if isinstance(update, Update) else update
        replacements = {
            sp.Symbol(name): (
                value.expression if isinstance(value, Polynomial) else arithmetic_to_symbolic(value)
            )
            for name, value in assignments.items()
        }
        # SymPy's simultaneous mode prevents x := y, y := x from becoming y := y.
        return self.normalize(poly.expression.subs(replacements, simultaneous=True))

    def variables(self, poly: Polynomial) -> frozenset[str]:
        return frozenset(symbol.name for symbol in poly.expression.free_symbols)

    def coefficients(
        self, poly: Polynomial, state_variables: tuple[str, ...]
    ) -> Mapping[tuple[int, ...], sp.Expr]:
        symbols = tuple(sp.Symbol(name) for name in state_variables)
        if not symbols:
            return {(): poly.expression}
        try:
            parsed = sp.Poly(poly.expression, *symbols)
        except sp.PolynomialError as error:
            raise AnalysisError(
                f"expression is not polynomial in state variables {state_variables}"
            ) from error
        return {monomial: coefficient for monomial, coefficient in parsed.terms()}

    def add(self, *polynomials: Polynomial) -> Polynomial:
        return self.normalize(sum((item.expression for item in polynomials), sp.Integer(0)))

    def scale(self, scalar: Expr | sp.Expr | int | str, poly: Polynomial) -> Polynomial:
        return self.normalize(arithmetic_to_symbolic(scalar) * poly.expression)

    def is_affine_in(self, poly: Polynomial, decision_variables: tuple[str, ...]) -> bool:
        if not decision_variables:
            return True
        symbols = tuple(sp.Symbol(name) for name in decision_variables)
        try:
            decision_poly = sp.Poly(poly.expression, *symbols)
        except sp.PolynomialError:
            return False
        return decision_poly.total_degree() <= 1
