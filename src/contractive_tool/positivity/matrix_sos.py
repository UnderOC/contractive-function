"""Matrix SOS lowering to the existing rational affine ConicModel.

The degree is the degree of each multiplier's monomial basis. Generator
products are supplied separately; all products must be nonnegative on domain.
"""
from itertools import combinations

import sympy as sp

from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.base import new_scalar, match_coefficients
from contractive_tool.positivity.gram import monomials, free_polynomial


def generator_products(domain, max_factors, limits):
    if type(max_factors) is not int or max_factors < 1:
        raise AnalysisError('Generator product depth must be positive')
    products = []
    for size in range(1, min(max_factors, len(domain.generators))+1):
        for factors in combinations(domain.generators, size):
            if len(products) >= limits.max_products:
                raise AnalysisError('Generator product budget exceeded')
            value = sp.expand(sp.prod(factors))
            if value != 0 and value not in products:
                products.append(value)
    return products


def matrix_gram(variables, size, degree, model, namespace, limits):
    if degree < 0:
        raise AnalysisError('Matrix multiplier degree must be nonnegative')
    # Preflight before materializing a potentially enormous basis.
    from math import comb
    dimension = size * comb(len(variables)+degree, degree)
    if dimension > limits.max_psd_dimension:
        raise AnalysisError('Matrix SOS PSD dimension exceeds budget')
    if len(model.decisions)+dimension*(dimension+1)//2 > limits.max_decisions:
        raise AnalysisError('Matrix SOS decision count exceeds budget')
    basis = monomials(variables, degree)
    names = [[None]*dimension for _ in range(dimension)]
    for i in range(dimension):
        for j in range(i, dimension):
            name = f'{namespace}_q_{i}_{j}'
            new_scalar(model, name)
            names[i][j] = names[j][i] = name
    model.psd_blocks.append({'id': namespace, 'matrix': names,
                             'basis': [f'{m} * e{j}' for m in basis for j in range(size)]})
    return sp.Matrix(size, size, lambda i, j: sp.expand(sum(
        left*right*sp.Symbol(names[a*size+i][b*size+j])
        for a, left in enumerate(basis) for b, right in enumerate(basis))))


def lower_matrix_sos(domain, matrix, model, namespace, degree, limits, products, *, check_budget=None):
    matrix = sp.Matrix(matrix)
    if matrix.rows != matrix.cols or matrix != matrix.T:
        raise AnalysisError('Matrix positivity requires a symmetric square matrix')
    size = matrix.rows
    if check_budget is not None:
        check_budget()
    rhs = matrix_gram(domain.variables, size, degree, model, namespace+'_s0', limits)
    for i, g in enumerate(products):
        if check_budget is not None:
            check_budget()
        rhs += g*matrix_gram(domain.variables, size, degree, model, namespace+f'_s{i+1}', limits)
    for index, equality in enumerate(domain.equalities):
        multiplier = sp.zeros(size)
        for i in range(size):
            for j in range(i, size):
                if check_budget is not None:
                    check_budget()
                multiplier[i, j] = multiplier[j, i] = free_polynomial(
                    domain.variables, 2*degree, model, f'{namespace}_h{index}_{i}_{j}', limits)
        rhs += equality*multiplier
    for i in range(size):
        for j in range(i, size):
            if check_budget is not None:
                check_budget()
            match_coefficients(matrix[i, j]-rhs[i, j], domain.variables, model)
