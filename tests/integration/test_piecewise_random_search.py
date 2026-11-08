from copy import deepcopy

import pytest
import sympy as sp

from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.analysis.cauchy import (
    CauchyOptions, EtaTemplate, search_fixed_eta, search_template_eta)
from contractive_tool.analysis.cauchy_verification import verify_result as verify_cauchy
from contractive_tool.analysis.reciprocal import ReciprocalOptions, search_reciprocal
from contractive_tool.analysis.reciprocal_verification import verify_result as verify_reciprocal


@pytest.fixture(scope='module', autouse=True)
def backend():
    cp = pytest.importorskip('cvxpy')
    pytest.importorskip('mosek')
    x = cp.Variable()
    try:
        cp.Problem(cp.Minimize(x), [x >= 1]).solve(solver=cp.MOSEK)
    except cp.error.SolverError as error:
        pytest.skip(str(error))


def test_conditional_cauchy_fixed_joint_and_source_replay(tmp_path, monkeypatch):
    source = tmp_path/'contracting.pp'
    source.write_text('x := 4; while x >= 1 invariant x >= 0 do {x >= 1} '
        'if x > 2 then {x > 2} x := 0.5*x else {x >= 1} x := 0.25*x fi od; refute true;')
    round_ = prepare_random_round(source)
    x,a,b = sp.symbols('x a b')
    options = CauchyOptions(total_seconds=20, solver_seconds=5)
    fixed = search_fixed_eta(round_, x, options=options)
    joint = search_template_eta(round_, EtaTemplate(a*x+b, (a,b), (a,b), (a+b-1,)),
                               t_values=('1/2',), options=options)
    from contractive_tool.backends.cvxpy import mosek_solver
    monkeypatch.setattr(mosek_solver, 'solve', lambda *a, **kw: pytest.fail('Replay invoked solver'))
    for result in (fixed, joint):
        assert result['status'] == 'proved'
        assert verify_cauchy(prepare_random_round(source), result)['status'] == 'proved'
        bad = deepcopy(result)
        bad['round']['pieces'].pop()
        assert verify_cauchy(round_, bad)['status'] == 'verification_failed'
        bad = deepcopy(result)
        bad['attempts'][0]['model']['coefficient_equalities'].pop()
        assert verify_cauchy(round_, bad)['status'] == 'verification_failed'


def test_conditional_reciprocal_synthesis_fixed_D_and_replay(tmp_path, monkeypatch):
    source = tmp_path/'growing.pp'
    source.write_text('x := 1; while x < 4 invariant x >= 1 do {x >= 1} '
        'if x < 2 then {x >= 1} x := 2*x else {x >= 1} x := 1.5*x fi od; refute true;')
    round_ = prepare_random_round(source)
    options = ReciprocalOptions(growth_values=('5/4',), moment_values=('4',),
                                feedback_points=0, total_seconds=25, solver_seconds=5)
    result = search_reciprocal(round_, options=options)
    assert result['status'] == 'proved'
    from contractive_tool.backends.cvxpy import mosek_solver
    monkeypatch.setattr(mosek_solver, 'solve', lambda *a, **kw: pytest.fail('Replay invoked solver'))
    assert verify_reciprocal(prepare_random_round(source), result)['status'] == 'proved'
    for field in ('pieces', 'guard', 'probability', 'model'):
        bad = deepcopy(result)
        if field == 'pieces':
            bad['round']['pieces'].pop()
        elif field == 'guard':
            bad['round']['pieces'][0]['guard']['strict_generators'] = []
        elif field == 'probability':
            bad['round']['law']['atoms'][0]['probability'] = '1/2'
        else:
            bad['attempts'][0]['stages'][0]['model']['coefficient_equalities'].pop()
        assert verify_reciprocal(round_, bad)['status'] == 'verification_failed'


def test_noncontracting_region_cannot_be_dropped(tmp_path):
    source = tmp_path/'stuck.pp'
    source.write_text('x := 4; while x >= 1 do '
        'if x > 2 then x := x else x := 0.5*x fi od; refute true;')
    round_ = prepare_random_round(source)
    result = search_fixed_eta(round_, sp.Symbol('x'), options=CauchyOptions(total_seconds=10))
    assert result['status'] == 'no_certificate_found'


def test_exit_successor_is_not_killed_for_reciprocal(tmp_path):
    source = tmp_path/'zero_exit.pp'
    source.write_text('x := 1; while x >= 1 and x < 4 do '
        'if x < 2 then x := 2*x else x := 0 fi od; refute true;')
    result = search_reciprocal(prepare_random_round(source), eta=sp.Symbol('x'),
                              options=ReciprocalOptions(total_seconds=10, feedback_points=0))
    assert result['status'] == 'no_certificate_found'
