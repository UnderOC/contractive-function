from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.analysis.reciprocal import ReciprocalOptions, evaluate, search_reciprocal
from contractive_tool.analysis.reciprocal_feedback import feedback_search, propose_parameters
from contractive_tool.analysis.reciprocal_verification import verify_result

PROJECT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def feedback_result():
    cp = pytest.importorskip('cvxpy')
    pytest.importorskip('mosek')
    x = cp.Variable()
    try:
        cp.Problem(cp.Minimize(x), [x >= 1]).solve(solver=cp.MOSEK)
    except cp.error.SolverError as error:
        pytest.skip(str(error))
    round_ = prepare_random_round(PROJECT/'contractive_examples/kelly/K6_two_sided_exit.pp')
    options = ReciprocalOptions(growth_values=('33/32',), feedback_points=6)
    result = search_reciprocal(round_, options=options)
    return round_, options, result


def test_automatic_feedback_improves_full_tail_and_replays(feedback_result):
    round_, options, result = feedback_result
    assert result['status'] == 'proved'
    assert verify_result(round_, result)['status'] == 'proved'
    initial = deepcopy(result)
    initial['candidates'] = [c for c in result['candidates'] if c['attempt'] == 0]
    assert evaluate(initial, 1000)['upper_bound_approx'] > 0.5
    assert evaluate(result, 1000)['upper_bound_approx'] < 0.05
    assert len(result['feedback_history']) <= options.feedback_points
    assert any(h.get('improved') for h in result['feedback_history'])
    assert all(a['seed_D'] is not None for a in result['attempts'] if a['origin'] == 'feedback')
    json.dumps(result)  # SymPy booleans must not leak into serialized artifacts.


@pytest.mark.parametrize('field', ['parent', 'seed', 'cap', 'step'])
def test_feedback_provenance_and_constraints_cannot_be_forged(feedback_result, field):
    round_, _, result = feedback_result
    bad = deepcopy(result)
    attempt = next(a for a in bad['attempts'] if a['origin'] == 'feedback' and a['status'] == 'proved')
    if field == 'parent':
        attempt['feedback']['parent'] = len(bad['attempts'])
    elif field == 'seed':
        attempt['seed_D'] = '1'
    elif field == 'cap':
        attempt['b_cap'] = '1'
    else:
        attempt['feedback']['step'] = '1/2'
    assert verify_result(round_, bad)['status'] == 'verification_failed'


def test_feedback_deadline_retains_incumbents(feedback_result):
    _, options, result = feedback_result
    retained = deepcopy(result)
    before = deepcopy(retained['candidates'])
    def fail(*args, **kwargs):
        raise AssertionError('No solve after feedback deadline')
    feedback_search(retained, fail, options, deadline=1, clock=lambda: 2)
    assert retained['candidates'] == before
    assert retained['feedback_stop_reason'] == 'time_budget'


def test_all_unknown_feedback_shrinks_steps_without_losing_proof(feedback_result):
    _, options, result = feedback_result
    retained = deepcopy(result)
    retained['attempts'] = retained['attempts'][:1]
    retained['candidates'] = [c for c in retained['candidates'] if c['attempt'] == 0]
    retained['feedback_history'] = []
    before = deepcopy(retained['candidates'])
    def unknown(c, r, D, **kwargs):
        attempt = {'status': 'unknown', 'seed_c': str(c), 'seed_r0': str(r), 'seed_D': str(D),
                   'b_cap': str(kwargs['b_cap']), 'origin': 'feedback'}
        retained['attempts'].append(attempt)
        return attempt
    feedback_search(retained, unknown, options, deadline=10, clock=lambda: 0)
    assert retained['candidates'] == before
    history = retained['feedback_history']
    assert all(not h.get('improved', False) for h in history)
    assert history[0]['step'] == '1/4' and history[3]['step'] == '1/8'
    assert retained['feedback_stop_reason'] == 'point_budget'


def test_feedback_is_independent_of_program_variable_names(feedback_result, tmp_path):
    _, options, _ = feedback_result
    source = tmp_path/'renamed.pp'
    source.write_text((PROJECT/'contractive_examples/kelly/K6_two_sided_exit.pp').read_text().replace('wealth', 'capital').replace('round', 'ticks'))
    round_ = prepare_random_round(source)
    result = search_reciprocal(round_, options=replace(options, feedback_points=1))
    assert evaluate(result, 1000)['upper_bound_approx'] < 0.05
    assert verify_result(round_, result)['status'] == 'proved'


def test_version_one_grid_artifacts_remain_replayable(feedback_result):
    round_, options, _ = feedback_result
    result = search_reciprocal(round_, eta=sp.Symbol('wealth'),
                              options=replace(options, adaptive_k=False, feedback_points=0))
    result['schema_version'] = 1
    for key in ('adaptive_k', 'k_upper', 'k_steps', 'k_denominator', 'target_ns',
                'feedback_points', 'feedback_seconds', 'feedback_step', 'moment_values', 'matrix_multiplier_degree'):
        result['options'].pop(key)
    assert verify_result(round_, result)['status'] == 'proved'


def test_parameter_proposal_obeys_moment_hypotheses(feedback_result):
    _, _, result = feedback_result
    parent = result['attempts'][0]
    for direction in ('growth', 'variance', 'support'):
        proposal = propose_parameters(parent, direction, '1/4')
        c, r, D, cap = (sp.Rational(proposal[key]) for key in ('seed_c', 'seed_r0', 'seed_D', 'b_cap'))
        assert c > 1 and 0 < r < c and D >= c*c and cap >= sp.Rational(parent['b'])
