from copy import deepcopy
from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.analysis.reciprocal import ReciprocalOptions, evaluate, search_reciprocal
from contractive_tool.analysis.reciprocal_verification import verify_result

PROJECT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def results():
    cp = pytest.importorskip('cvxpy')
    pytest.importorskip('mosek')
    x = cp.Variable()
    try:
        cp.Problem(cp.Minimize(x), [x >= 1]).solve(solver=cp.MOSEK)
    except cp.error.SolverError as error:
        pytest.skip(str(error))
    round_ = prepare_random_round(PROJECT/'contractive_examples/kelly/K6_two_sided_exit.pp')
    fixed = search_reciprocal(round_, eta=sp.Symbol('wealth'))
    template = search_reciprocal(round_, options=ReciprocalOptions(feedback_points=0))
    return round_, fixed, template


def test_fixed_eta_and_automatic_polynomial_synthesis(results):
    round_, fixed, template = results
    for result in (fixed, template):
        assert result['status'] == 'proved'
        assert verify_result(round_, result)['status'] == 'proved'
        assert evaluate(result, 0)['upper_bound_exact'] == '1'
        assert 0 < sp.Rational(evaluate(result, 1000)['upper_bound_exact']) < 1
    assert fixed['attempts'][0]['constants'] == {'c': '26/25', 'D': '28/25', 'r0': '4/5'}
    assert len(template['input']['coefficients']) == 3  # includes unused round counter
    assert all('round' not in c['eta'] for c in template['candidates'])


def test_source_replay_and_evaluation_need_no_solver(results, monkeypatch):
    from contractive_tool.backends.cvxpy import mosek_solver
    def fail(*a, **kw):
        raise AssertionError('Replay must not invoke the solver')
    monkeypatch.setattr(mosek_solver, 'solve', fail)
    round_, fixed, _ = results
    assert verify_result(round_, fixed)['status'] == 'proved'
    assert evaluate(fixed, 100)['upper_bound_approx'] < 1


@pytest.mark.parametrize('field', ['model', 'value', 'eta', 'b', 'c', 'D', 'r0', 'power', 'formula', 'round'])
def test_tampered_proofs_are_rejected(results, field):
    round_, fixed, _ = results
    bad = deepcopy(fixed)
    attempt = bad['attempts'][0]
    if field == 'model':
        attempt['stages'][0]['model']['coefficient_equalities'] = []
    elif field == 'value':
        values = attempt['stages'][0]['verification']['exact_values']
        values[next(iter(values))] = '-1'
    elif field in ('c', 'D', 'r0'):
        attempt['constants'][field] = '99'
    elif field in ('eta', 'b'):
        attempt[field] = '99'
    elif field == 'power':
        bad['candidates'][0]['moment']['r0_power']['upper'] = '0'
    elif field == 'formula':
        bad['candidates'][0]['expression'] = '0'
    else:
        bad['round']['law']['atoms'][0]['probability'] = '1'
    assert verify_result(round_, bad)['status'] == 'verification_failed'


def test_unbounded_kelly_cannot_use_bounded_reciprocal_theorem(results, unbounded_kelly_source):
    round_ = prepare_random_round(unbounded_kelly_source)
    fixed = search_reciprocal(round_, eta=sp.Symbol('wealth'))
    template = search_reciprocal(round_, options=ReciprocalOptions(growth_values=('33/32',)))
    assert fixed['status'] == template['status'] == 'no_certificate_found'
    assert not fixed['candidates'] and not template['candidates']


@pytest.mark.parametrize('program', [
    'x := 1; while x >= 1 do x := x od; refute true;',
    'x := 1; while x >= 1 do x := 0 od; refute true;',
    'x := 1; while x >= 1 do x := -x od; refute true;',
])
def test_no_false_certificate_or_terminal_reciprocal_evaluation(tmp_path, results, program):
    source = tmp_path/'counterexample.pp'
    source.write_text(program)
    # The raw-moment sufficient route must reject zero/negative successors,
    # even though the last two programs terminate. No reciprocal is evaluated.
    result = search_reciprocal(prepare_random_round(source), eta=sp.Symbol('x'))
    assert result['status'] == 'no_certificate_found'


def test_deterministic_growth_and_initial_exit_time_index(tmp_path, results):
    source = tmp_path/'growth.pp'
    source.write_text('x := 1; while x < 4 invariant x >= 1 do {x >= 1} x := 2*x od; refute true;')
    round_ = prepare_random_round(source)
    result = search_reciprocal(round_, eta=sp.Symbol('x'))
    assert verify_result(round_, result)['status'] == 'proved'
    assert evaluate(result, 1)['upper_bound_exact'] == '1'
    assert evaluate(result, 3)['upper_bound_approx'] < 1
    source.write_text('x := 4; while x < 4 do x := 2*x od; refute true;')
    round_ = prepare_random_round(source)
    result = search_reciprocal(round_)
    assert verify_result(round_, result)['status'] == 'proved'
    assert evaluate(result, 0)['upper_bound_exact'] == '0'


def test_unknown_after_success_keeps_certificates(results, monkeypatch):
    import contractive_tool.analysis.reciprocal as module
    round_, _, _ = results
    original = module._solve
    calls = []
    def limited(*args):
        calls.append(1)
        if len(calls) > 4:
            return {'status': 'unknown', 'reason': 'simulated_timeout'}
        return original(*args)
    monkeypatch.setattr(module, '_solve', limited)
    result = search_reciprocal(round_, options=ReciprocalOptions(growth_values=('33/32', '65/64')))
    assert result['attempts'][0]['status'] == 'proved'
    assert result['attempts'][1]['status'] == 'unknown'
    assert verify_result(round_, result)['status'] == 'proved'


def test_standalone_cli_and_unsupported_inputs(tmp_path, results, capsys):
    from contractive_tool.reciprocal_cli import main
    output = tmp_path/'result'
    assert main(['run', str(PROJECT/'contractive_examples/kelly/K6_two_sided_exit.pp'), '--out-dir', str(output)]) == 0
    assert main(['verify', str(output)]) == 0
    assert main(['evaluate', str(output), '--n', '100']) == 0
    assert main(['evaluate', str(output), '--n', '-1']) == 2
    capsys.readouterr()
    source = tmp_path/'continuous.pp'
    source.write_text('x := 1; while x < 2 do x := Uniform(1,3) od; refute true;')
    assert main(['run', str(source), '--out-dir', str(tmp_path/'continuous')]) == 3
    assert 'finite discrete' in capsys.readouterr().out
    source.write_text('while ???')
    assert main(['run', str(source), '--out-dir', str(tmp_path/'invalid')]) == 2
    assert 'error' in capsys.readouterr().out


def test_exact_finite_horizon_probability_is_below_certificate(results):
    # Independent propagation on the two rational wealth multipliers. This is
    # a regression check; the unbounded-time proof comes from the conic models.
    _, fixed, template = results
    alive = {sp.Integer(1): sp.Integer(1)}
    for n in range(101):
        truth = sum(alive.values())
        for result in (fixed, template):
            assert truth <= sp.Rational(evaluate(result, n)['upper_bound_exact'])
        next_alive = {}
        for wealth, probability in alive.items():
            for factor, weight in ((sp.Rational(6, 5), sp.Rational(3, 5)),
                                   (sp.Rational(4, 5), sp.Rational(2, 5))):
                new = factor*wealth
                if sp.Rational(1, 2) <= new < 2:
                    next_alive[new] = next_alive.get(new, 0)+weight*probability
        alive = next_alive
