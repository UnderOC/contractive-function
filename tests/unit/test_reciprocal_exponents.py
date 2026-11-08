from dataclasses import replace

import pytest
import sympy as sp

from contractive_tool.analysis.reciprocal import ReciprocalOptions, exponent_candidates
from contractive_tool.analysis.reciprocal_exponents import propose_exponents


def envelope(candidates, n):
    return min(sp.Rational(c['prefactor_upper'])*sp.Rational(c['decay_upper'])**n for c in candidates)


def test_adaptive_full_tail_improves_kelly_and_preserves_grid():
    args = (sp.Symbol('wealth'), sp.Integer(2), sp.Rational(26, 25), sp.Rational(28, 25), sp.Rational(4, 5))
    options = ReciprocalOptions()
    adaptive, _ = exponent_candidates(*args, options)
    grid, _ = exponent_candidates(*args, replace(options, adaptive_k=False))
    assert set(c['k'] for c in grid) <= set(c['k'] for c in adaptive)
    assert envelope(adaptive, 100) < sp.Rational(804, 1000) < envelope(grid, 100)
    assert envelope(adaptive, 1000) < envelope(grid, 1000)
    for n in (1, 20, 100, 1000):
        assert envelope(adaptive, n) <= envelope(grid, n)


@pytest.mark.parametrize('c,D,r,lower,upper', [
    ('26/25', '28/25', '4/5', 0, 1),
    ('29/25', '34/25', '4/5', 1, 8),
])
def test_derivative_bisection_brackets_minima_on_both_sides_of_one(c, D, r, lower, upper):
    values, audit = propose_exponents(2, c, D, r, ReciprocalOptions())
    rate = audit[0]
    assert rate['status'] == 'bracketed'
    assert lower < sp.Rational(rate['lower']) < sp.Rational(rate['upper']) < upper
    assert all(max(k.p, k.q) <= 2048 for k in values)


@pytest.mark.parametrize('c,D,r', [('2', '4', '1'), ('3/2', '5/2', '1'), ('3', '10', '2')])
def test_decreasing_q_uses_finite_upper_boundary(c, D, r):
    values, audit = propose_exponents(2, c, D, r, ReciprocalOptions())
    assert audit[0]['status'] == 'upper_boundary'
    assert sp.Integer(8) in values


def test_no_contraction_is_not_invented_from_mean_growth():
    # R*=1/2 or 2 equiprobably has mean 5/4 but E(log R*)=0.
    candidates, _ = exponent_candidates(sp.Symbol('x'), sp.Integer(2),
        sp.Rational(5, 4), sp.Rational(17, 8), sp.Rational(1, 2), ReciprocalOptions())
    assert candidates == []


def test_upper_boundary_does_not_claim_global_optimality_and_arithmetic_is_bounded():
    values, audit = propose_exponents(2, '26/25', '28/25', '4/5',
        ReciprocalOptions(k_upper='64', k_denominator=2048))
    assert all(max(k.p, k.q) <= 2048 for k in values)
    assert all(a['signs'] == 'numerical_proposals_only' for a in audit)


def test_adaptive_proposals_work_without_legacy_grid_near_the_optimum():
    candidates, _ = exponent_candidates(sp.Symbol('x'), sp.Integer(2), sp.Rational(26, 25),
        sp.Rational(28, 25), sp.Rational(4, 5), ReciprocalOptions(k_values=('1', '2')))
    assert candidates and all(sp.Rational(c['k']) < 1 for c in candidates)
