from __future__ import annotations

import sympy as sp
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.base import match_coefficients
from contractive_tool.positivity.gram import free_polynomial, gram_polynomial


def polynomial_degree(expr, variables):
    return int(sp.Poly(expr, *variables).total_degree()) if variables and expr != 0 else 0


def lower_sos(domain, h, model, namespace, order, limits, products):
    if polynomial_degree(h, domain.variables) > 2 * order:
        raise AnalysisError("Relaxation order is too small for conclusion")
    rhs = gram_polynomial(domain.variables, order, model, namespace + "_s0", limits)
    for i, g in enumerate(products):
        degree = polynomial_degree(g, domain.variables)
        multiplier_degree = order - (degree + 1) // 2
        if multiplier_degree >= 0:
            rhs += g * gram_polynomial(domain.variables, multiplier_degree, model,
                                      namespace + f"_s{i+1}", limits)
    for i, equality in enumerate(domain.equalities):
        degree = 2 * order - polynomial_degree(equality, domain.variables)
        if degree >= 0:
            rhs += equality * free_polynomial(domain.variables, degree, model,
                                               namespace + f"_ideal{i}", limits)
    match_coefficients(h - rhs, domain.variables, model)


class PutinarStrategy:
    id = "putinar"

    def supports(self, domain):
        return True

    def lower(self, domain, h, model, namespace, degree, limits):
        lower_sos(domain, h, model, namespace, degree, limits, domain.generators)
