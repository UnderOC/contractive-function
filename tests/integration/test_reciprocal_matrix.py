from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.analysis.reciprocal import (
    ReciprocalOptions, search_reciprocal, second_moment_matrix, evaluate)
from contractive_tool.analysis.reciprocal_verification import verify_result

PROJECT = Path(__file__).resolve().parents[2]


def test_rational_schur_matrix_is_exactly_the_weighted_second_moment():
    eta, D, u, v = sp.symbols('eta D u v', positive=True)
    matrix = second_moment_matrix(eta, ((u, sp.Rational(3, 5)), (v, sp.Rational(2, 5))), D)
    schur = matrix[0, 0]-(matrix[0, 1:]*matrix[1:, 1:].inv()*matrix[1:, 0])[0]
    assert sp.expand(eta*schur-(D*eta**2-sp.Rational(3, 5)*u**2-sp.Rational(2, 5)*v**2)) == 0


@pytest.fixture(scope='module')
def matrix_result():
    cp = pytest.importorskip('cvxpy')
    pytest.importorskip('mosek')
    x = cp.Variable()
    try:
        cp.Problem(cp.Minimize(x), [x >= 1]).solve(solver=cp.MOSEK)
    except cp.error.SolverError as error:
        pytest.skip(str(error))
    round_ = prepare_random_round(PROJECT/'kelly_double_bound.pp')
    options = ReciprocalOptions(growth_values=('26/25',), support_values=('4/5',),
                                moment_values=('28/25',), feedback_points=0)
    return round_, options, search_reciprocal(round_, options=options)


def test_matrix_constraint_synthesizes_denominator_and_replays(matrix_result):
    round_, _, result = matrix_result
    assert result['status'] == 'proved'
    attempt = result['attempts'][0]
    assert attempt['seed_D'] == '28/25'
    assert attempt['stages'][0]['model']['coverage']['matrix']
    assert sp.expand(sp.sympify(attempt['eta'])-sp.Symbol('wealth')) == 0
    assert evaluate(result, 1000)['upper_bound_approx'] < 0.009
    assert verify_result(round_, result)['status'] == 'proved'


def test_too_tight_D_is_not_accepted(matrix_result):
    round_, options, _ = matrix_result
    result = search_reciprocal(round_, options=replace(options, moment_values=('11/10',)))
    assert result['status'] == 'no_certificate_found'
    assert not result['candidates']


def test_seed_certificate_survives_unknown_tightening(matrix_result, monkeypatch):
    import contractive_tool.analysis.reciprocal as module
    round_, options, original = matrix_result
    denominator = original['attempts'][0]['stages'][0]
    calls = []
    def solve(model, *args):
        calls.append(model)
        if len(calls) == 1:
            assert model.to_data() == denominator['model']
            return {'status': 'proved', 'verification': denominator['verification']}
        return {'status': 'unknown', 'reason': 'simulated_timeout'}
    monkeypatch.setattr(module, '_solve', solve)
    result = search_reciprocal(round_, options=options)
    assert result['status'] == 'proved'
    assert result['attempts'][0]['constants'] == {'c': '26/25', 'r0': '4/5', 'D': '28/25'}
    assert verify_result(round_, result)['status'] == 'proved'


@pytest.mark.parametrize('field', ['seed', 'matrix', 'psd'])
def test_matrix_proof_tampering_is_rejected(matrix_result, field):
    round_, _, result = matrix_result
    bad = deepcopy(result)
    attempt = bad['attempts'][0]
    if field == 'seed':
        attempt['seed_D'] = '11/10'
    elif field == 'matrix':
        attempt['stages'][0]['model']['coverage']['matrix'][0]['matrix'][0][0] = '0'
    else:
        attempt['stages'][0]['model']['psd_blocks'] = []
    assert verify_result(round_, bad)['status'] == 'verification_failed'
