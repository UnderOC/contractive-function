from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
import sympy as sp

from contractive_tool.positivity.ir import BasicSet, ConicModel


@dataclass(frozen=True)
class EncodingLimits:
    max_products: int = 256
    max_psd_dimension: int = 80
    max_decisions: int = 20000


class PositivityStrategy(Protocol):
    id: str

    def supports(self, domain: BasicSet) -> bool: ...
    def lower(self, domain: BasicSet, h: sp.Expr, model: ConicModel,
              namespace: str, degree: int, limits: EncodingLimits) -> None: ...


def new_scalar(model, name, nonnegative=False):
    model.decisions.append(name)
    if nonnegative:
        model.nonnegative.append(name)
    return sp.Symbol(name)


def match_coefficients(expr, variables, model):
    expr = sp.expand(expr)
    coefficients = sp.Poly(expr, *variables).coeffs() if variables else [expr]
    model.equalities.extend(c for c in coefficients if c != 0)
