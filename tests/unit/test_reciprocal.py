from dataclasses import replace

import pytest
import sympy as sp

from contractive_tool.analysis.reciprocal import ReciprocalOptions, exponent_candidates, moment_bound
from contractive_tool.errors import AnalysisError
from contractive_tool.probability.fractional_moments import verify_power


def test_two_point_moment_bound_recovers_kelly_law():
    row = moment_bound('26/25', '28/25', '4/5', '1/2')
    assert row['p_star'] == '2/5' and row['z_star'] == '6/5'
    assert verify_power(row['r0_power']) and verify_power(row['z_power'])
    assert sp.Rational(row['decay_upper']) < 1
    assert row['r0_power']['base'] == '5/4'
    assert row['z_power']['base'] == '5/6'


def test_deterministic_second_moment_and_equal_support_are_handled():
    candidates, _ = exponent_candidates(sp.Symbol('x'), sp.Integer(4), sp.Integer(2),
        sp.Integer(4), sp.Integer(2), ReciprocalOptions(k_values=('1',)))
    assert candidates[0]['moment']['p_star'] == '0'
    assert candidates[0]['decay_upper'] == '1/2'
    assert candidates[0]['prefactor_upper'] == '4'


def test_mean_growth_alone_does_not_imply_contraction():
    # Mean 1.01 with large variance/low support has no negative-moment
    # contraction in this grid, despite c>1.
    candidates, history = exponent_candidates(sp.Symbol('x'), sp.Integer(2),
        sp.Rational(101, 100), sp.Integer(10), sp.Rational(1, 10), ReciprocalOptions())
    assert not candidates and all(h['status'] == 'no_contraction' for h in history)


@pytest.mark.parametrize('params', [
    (1, 2, '1/2', 1), (2, 3, 1, 1), (2, 4, 0, 1),
    (2, 4, 2, 1), (2, 4, 1, 0),
])
def test_invalid_moment_hypotheses_are_rejected(params):
    with pytest.raises(AnalysisError):
        moment_bound(*params)


@pytest.mark.parametrize('kwargs', [
    {'epsilon': '0'}, {'growth_values': ('1',)}, {'support_values': ('0',)},
    {'k_values': ('-1/2',)}, {'total_seconds': float('inf')}, {'degree': -1},
])
def test_invalid_search_settings_are_rejected(kwargs):
    with pytest.raises(AnalysisError):
        replace(ReciprocalOptions(), **kwargs).validate()
