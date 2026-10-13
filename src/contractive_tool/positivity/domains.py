from __future__ import annotations

from itertools import product
import sympy as sp

from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.ast import BooleanConstant, BoolBinary, BoolUnary, Compare
from contractive_tool.positivity.ir import BasicSet


def predicate_regions(expr, variables, *, negated=False, max_regions=128):
    """DNF basic closed supersets of a source predicate, without shrinking strict guards."""
    if isinstance(expr, BooleanConstant):
        return [BasicSet(variables)] if expr.value != negated else []
    if isinstance(expr, BoolUnary):
        return predicate_regions(expr.operand, variables, negated=not negated,
                                 max_regions=max_regions)
    if isinstance(expr, BoolBinary):
        left = predicate_regions(expr.left, variables, negated=negated, max_regions=max_regions)
        right = predicate_regions(expr.right, variables, negated=negated, max_regions=max_regions)
        conjunction = (expr.operator == "and") != negated
        if conjunction:
            if len(left) * len(right) > max_regions:
                raise AnalysisError("Predicate DNF exceeds region budget")
            return [BasicSet(variables, a.generators + b.generators, a.equalities + b.equalities)
                    for a, b in product(left, right)]
        if len(left) + len(right) > max_regions:
            raise AnalysisError("Predicate DNF exceeds region budget")
        return left + right
    if not isinstance(expr, Compare):
        raise AnalysisError("Unsupported non-polynomial predicate")
    op = expr.operator
    if negated:
        op = {"<": ">=", "<=": ">", ">": "<=", ">=": "<", "=": "!=", "!=": "="}[op]
    delta = sp.expand(arithmetic_to_symbolic(expr.left) - arithmetic_to_symbolic(expr.right))
    if delta.free_symbols - set(variables):
        raise AnalysisError("Domain contains unknown or decision symbols")
    if op == "=":
        return [BasicSet(variables, equalities=(delta,))]
    if op == "!=":
        # Closure of either open side; a conservative, covering proof domain.
        return [BasicSet(variables, (delta,)), BasicSet(variables, (-delta,))]
    return [BasicSet(variables, (delta if op in {">", ">="} else -delta,))]


def eliminate_fixed_equalities(domain, conclusion):
    """Substitute affine equalities exactly; keep remaining equality ideal generators."""
    substitutions = {}
    remaining = list(domain.equalities)
    variables = list(domain.variables)
    while True:
        found = False
        for index, equality in enumerate(remaining):
            equality = sp.expand(equality.subs(substitutions))
            for variable in variables:
                coeff = sp.diff(equality, variable)
                if coeff.is_number and coeff != 0 and sp.diff(equality, variable, 2) == 0:
                    solution = sp.expand(variable - equality / coeff)
                    if variable in solution.free_symbols:
                        continue
                    substitutions = {x: value.subs(variable, solution) for x, value in substitutions.items()}
                    substitutions[variable] = solution
                    remaining.pop(index)
                    remaining = [sp.expand(e.subs(variable, solution)) for e in remaining]
                    variables.remove(variable)
                    found = True
                    break
            if found:
                break
        if not found:
            break
    generators = tuple(sp.expand(g.subs(substitutions, simultaneous=True)) for g in domain.generators)
    remaining = tuple(sp.expand(e.subs(substitutions, simultaneous=True)) for e in remaining)
    return BasicSet(tuple(variables), generators, remaining), sp.expand(
        conclusion.subs(substitutions, simultaneous=True))


def interval_features(domain):
    """Conservative exact bounded-box recognition. Unknown is never treated as proved."""
    bounds = {x: [None, None] for x in domain.variables}
    affine = not domain.equalities
    for g in domain.generators:
        involved = g.free_symbols
        if domain.variables and sp.Poly(g, *domain.variables).total_degree() > 1:
            affine = False
        if len(involved) != 1:
            continue
        x = next(iter(involved))
        a = sp.diff(g, x)
        if a.is_Rational and a != 0 and not a.has(x):
            b = sp.expand(g - a * x)
            if b.is_Rational:
                value = -b / a
                slot = 0 if a > 0 else 1
                current = bounds[x][slot]
                bounds[x][slot] = value if current is None else (
                    max(current, value) if slot == 0 else min(current, value))
    compact = affine and all(a is not None and b is not None for a, b in bounds.values())
    interior = compact and all(a < b for a, b in bounds.values())
    return {"affine_generators": affine, "compactness": "proved" if compact else "unknown",
            "box_interior": interior, "archimedean": "unknown",
            "bounds": {str(x): [str(a), str(b)] for x, (a, b) in bounds.items()}}
