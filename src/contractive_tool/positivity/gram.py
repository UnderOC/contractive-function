from __future__ import annotations

from math import comb
import sympy as sp

from contractive_tool.analysis.templates import total_degree_exponents
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.base import new_scalar


def monomials(variables, degree):
    return [sp.prod(x**a for x, a in zip(variables, powers))
            for powers in total_degree_exponents(len(variables), degree)]


def gram_polynomial(variables, degree, model, namespace, limits):
    dimension = comb(len(variables) + degree, degree)
    if dimension > limits.max_psd_dimension:
        raise AnalysisError("PSD dimension exceeds encoding budget")
    if len(model.decisions) + dimension * (dimension + 1) // 2 > limits.max_decisions:
        raise AnalysisError("Scalar decision count exceeds encoding budget")
    basis = monomials(variables, degree)
    if len(basis) == 1:
        return new_scalar(model, namespace + "_sos", nonnegative=True)
    matrix = [[None] * dimension for _ in basis]
    expr = sp.Integer(0)
    for i, left in enumerate(basis):
        for j in range(i, dimension):
            name = f"{namespace}_q_{i}_{j}"
            symbol = new_scalar(model, name)
            matrix[i][j] = matrix[j][i] = name
            expr += (1 if i == j else 2) * symbol * left * basis[j]
    model.psd_blocks.append({"id": namespace, "matrix": matrix,
                             "basis": [str(x) for x in basis]})
    return sp.expand(expr)


def free_polynomial(variables, degree, model, namespace, limits):
    count = comb(len(variables) + degree, degree)
    if len(model.decisions) + count > limits.max_decisions:
        raise AnalysisError("Equality multiplier exceeds encoding budget")
    return sp.expand(sum((new_scalar(model, f"{namespace}_{i}") * monomial
                         for i, monomial in enumerate(monomials(variables, degree))), sp.Integer(0)))
