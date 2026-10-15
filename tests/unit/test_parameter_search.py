import pytest
import sympy as sp

from contractive_tool.analysis.parameter_search import ContractionBisection
from contractive_tool.errors import AnalysisError


@pytest.mark.parametrize('threshold', [sp.Rational(1,2),sp.Rational(3,4),sp.Rational(99,100)])
def test_exact_bisection_retains_feasible_endpoint_and_honors_budget(threshold):
    search = ContractionBisection(10)
    for c in search.candidates():
        assert 0 < c < 1
        search.observe('proved' if c >= threshold else 'infeasible')
    assert len(search.history) == 10
    assert search.stop_reason == 'max_c_steps'
    assert search.lower < threshold <= search.upper
    assert search.upper-search.lower == sp.Rational(1,1024)
    assert search.best_verified == search.upper


def test_unknown_does_not_move_interval_or_discard_certificate():
    search = ContractionBisection(10)
    for c in search.candidates():
        search.observe('proved' if c == sp.Rational(1,2) else 'unknown')
    assert [r['c'] for r in search.history] == ['1/2','1/4']
    assert (search.lower,search.upper) == (0,sp.Rational(1,2))
    assert search.best_verified == sp.Rational(1,2)
    assert search.stop_reason == 'oracle_inconclusive'


def test_no_verified_upper_endpoint_is_not_reported_as_a_certificate():
    search = ContractionBisection(3)
    for c in search.candidates():
        search.observe('infeasible')
    assert [r['c'] for r in search.history] == ['1/2','3/4','7/8']
    assert search.to_data()['best_verified_c'] is None
    assert search.to_data()['upper_endpoint_verified'] is False
    assert search.to_data()['lower_endpoint_is_nonexistence_proof'] is False


@pytest.mark.parametrize('value', [0,-1,1.5,True])
def test_invalid_iteration_budget(value):
    with pytest.raises(AnalysisError,match='positive integer'):
        ContractionBisection(value)
