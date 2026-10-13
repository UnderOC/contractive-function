from __future__ import annotations

from math import comb
import sympy as sp

from contractive_tool.analysis.templates import total_degree_exponents
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.base import match_coefficients, new_scalar
from contractive_tool.positivity.domains import interval_features


class HandelmanStrategy:
    id = "handelman"

    def supports(self, domain):
        # This first implementation proves box boundedness; general polytope LP analysis is optional.
        features = interval_features(domain)
        return not domain.equalities and features["affine_generators"] and (
            not domain.variables or features["box_interior"])

    def lower(self, domain, h, model, namespace, degree, limits):
        if not self.supports(domain):
            raise AnalysisError("Handelman requires a recognized bounded affine box domain")
        count = comb(len(domain.generators) + degree, degree)
        if count > limits.max_products or len(model.decisions) + count > limits.max_decisions:
            raise AnalysisError("Handelman product/variable count exceeds encoding budget")
        rhs = sp.Integer(0)
        for i, powers in enumerate(total_degree_exponents(len(domain.generators), degree)):
            rhs += new_scalar(model, f"{namespace}_a{i}", nonnegative=True) * sp.prod(
                g**a for g, a in zip(domain.generators, powers))
        match_coefficients(h - rhs, domain.variables, model)
