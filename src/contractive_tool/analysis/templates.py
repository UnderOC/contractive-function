from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Iterable

import sympy as sp

from contractive_tool.algebra import Polynomial, PolynomialService
from contractive_tool.errors import AnalysisError
from contractive_tool.ir.cfg import ProgramCFG


def total_degree_exponents(variable_count: int, degree: int) -> tuple[tuple[int, ...], ...]:
    if degree < 0:
        raise AnalysisError("polynomial degree must be nonnegative")
    candidates = product(range(degree + 1), repeat=variable_count)
    return tuple(sorted((item for item in candidates if sum(item) <= degree), key=lambda x: (sum(x), x)))


@dataclass(frozen=True)
class PolynomialTemplateInstance:
    kind: str
    expressions: dict[str, Polynomial]
    decisions: tuple[str, ...]
    degree: int
    locations: tuple[str, ...]

    def expression_at(self, location: str) -> Polynomial:
        return self.expressions[location]

    def decision_variables(self) -> tuple[str, ...]:
        return self.decisions

    def metadata(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "degree": self.degree,
            "locations": list(self.locations),
            "decision_variable_count": len(self.decisions),
            "expressions": {name: str(value) for name, value in sorted(self.expressions.items())},
        }


class PolynomialTemplateFactory:
    kind = "polynomial"

    def __init__(self, polynomial_service: PolynomialService | None = None):
        self.polynomials = polynomial_service or PolynomialService()

    def instantiate(
        self,
        cfg: ProgramCFG,
        *,
        degree: int,
        prefix: str,
        locations: Iterable[str] | None = None,
    ) -> PolynomialTemplateInstance:
        selected = tuple(locations if locations is not None else cfg.locations)
        variables = tuple(sp.Symbol(name) for name in cfg.symbols.program_variables)
        exponents = total_degree_exponents(len(variables), degree)
        expressions: dict[str, Polynomial] = {}
        decisions: list[str] = []
        for location in selected:
            terms: list[sp.Expr] = []
            for index, powers in enumerate(exponents):
                decision_name = f"{prefix}_{location}_{index}"
                decisions.append(decision_name)
                monomial = sp.Integer(1)
                for variable, power in zip(variables, powers):
                    monomial *= variable**power
                terms.append(sp.Symbol(decision_name) * monomial)
            expressions[location] = self.polynomials.normalize(sum(terms, sp.Integer(0)))
        return PolynomialTemplateInstance(
            self.kind, expressions, tuple(decisions), degree, selected
        )
