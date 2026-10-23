"""Exact polynomial guard regions, closed only after symbolic pullback.

Strict inequalities matter when an update maps an entire region to the loop
boundary. Closing a guard before substitution would turn ``0 > 0`` into true.
The SOS backend still receives closed supersets; no epsilon margin is used.
"""
from dataclasses import dataclass
from itertools import product

import sympy as sp

from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.ast import BooleanConstant, BoolBinary, BoolUnary, Compare
from contractive_tool.positivity.ir import BasicSet


def primitive(expression):
    # Remove only a positive rational factor, preserving the inequality sign.
    return sp.expand(expression).as_content_primitive()[1]


@dataclass(frozen=True)
class GuardRegion:
    variables: tuple
    generators: tuple = ()
    equalities: tuple = ()
    strict: tuple = ()

    def intersect(self, other):
        return GuardRegion(self.variables, self.generators + other.generators,
                           self.equalities + other.equalities, self.strict + other.strict).simplify()

    def substitute(self, updates):
        parts = [tuple(sp.expand(p.subs(updates, simultaneous=True)) for p in expressions)
                 for expressions in (self.generators, self.equalities, self.strict)]
        if any(p.free_symbols - set(self.variables) for part in parts for p in part):
            raise AnalysisError('A guard depending on a fresh sample needs truncated-moment integration')
        return GuardRegion(self.variables, *parts).simplify()

    def simplify(self):
        """Drop exact tautologies and provably empty regions; never guess feasibility."""
        gs, es, ss = [tuple(dict.fromkeys(primitive(p) for p in part))
                      for part in (self.generators, self.equalities, self.strict)]
        if (any(p.is_number and p < 0 for p in gs)
                or any(p.is_number and p != 0 for p in es)
                or any(p.is_number and p <= 0 for p in ss)):
            return None
        # p > 0 is incompatible with p = 0 or -p >= 0 (including -p > 0).
        if any(p in es or -p in es or -p in gs or -p in ss for p in ss):
            return None
        return GuardRegion(self.variables,
                           tuple(p for p in gs if not p.is_number and p not in ss),
                           tuple(p for p in es if not p.is_number),
                           tuple(p for p in ss if not p.is_number))

    def closure(self):
        """A closed covering proof domain, not necessarily the minimal closure."""
        return BasicSet(self.variables, self.generators + self.strict, self.equalities)

    def to_data(self):
        return {**BasicSet(self.variables, self.generators, self.equalities).to_data(),
                'strict_generators': list(map(str, self.strict))}


def guard_regions(expr, variables, *, negated=False, max_regions=256):
    """DNF regions with exact >, >= and = semantics, including complements."""
    if isinstance(expr, BooleanConstant):
        return [GuardRegion(variables)] if expr.value != negated else []
    if isinstance(expr, BoolUnary):
        return guard_regions(expr.operand, variables, negated=not negated, max_regions=max_regions)
    if isinstance(expr, BoolBinary):
        left = guard_regions(expr.left, variables, negated=negated, max_regions=max_regions)
        right = guard_regions(expr.right, variables, negated=negated, max_regions=max_regions)
        if (expr.operator == 'and') != negated:
            if len(left) * len(right) > max_regions:
                raise AnalysisError('Symbolic guard DNF exceeds region budget')
            return list(dict.fromkeys(r for a, b in product(left, right)
                                      if (r := a.intersect(b)) is not None))
        if len(left) + len(right) > max_regions:
            raise AnalysisError('Symbolic guard DNF exceeds region budget')
        return list(dict.fromkeys(left + right))
    if not isinstance(expr, Compare):
        raise AnalysisError('Unsupported non-polynomial predicate')
    op = expr.operator
    if negated:
        op = {'<': '>=', '<=': '>', '>': '<=', '>=': '<', '=': '!=', '!=': '='}[op]
    delta = sp.expand(arithmetic_to_symbolic(expr.left) - arithmetic_to_symbolic(expr.right))
    if delta.free_symbols - set(variables):
        raise AnalysisError('Domain contains unknown or decision symbols')
    if op == '=':
        regions = [GuardRegion(variables, equalities=(delta,))]
    elif op == '!=':
        regions = [GuardRegion(variables, strict=(delta,)), GuardRegion(variables, strict=(-delta,))]
    elif op in {'>', '<'}:
        regions = [GuardRegion(variables, strict=(delta if op == '>' else -delta,))]
    else:
        regions = [GuardRegion(variables, generators=(delta if op == '>=' else -delta,))]
    return [r for region in regions if (r := region.simplify()) is not None]
