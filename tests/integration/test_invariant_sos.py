from copy import deepcopy
import json

import pytest
import sympy as sp

from contractive_tool.analysis.invariant_certification import InvariantProver, check_invariant_certificate
from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.analysis.cauchy import CauchyOptions, search_fixed_eta
from contractive_tool.analysis.cauchy_verification import verify_result
from contractive_tool.analysis_pipeline import SearchOptions, run_analysis
from contractive_tool.analysis.symbolic_workflow import verify_workflow
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.ir import BasicSet


@pytest.fixture(scope='module', autouse=True)
def backend():
    cp = pytest.importorskip('cvxpy')
    pytest.importorskip('mosek')
    x = cp.Variable()
    try:
        cp.Problem(cp.Minimize(x), [x >= 1]).solve(solver=cp.MOSEK)
    except cp.error.SolverError as error:
        pytest.skip(str(error))


def test_quartic_sos_fallback_and_exact_tamper_rejection(monkeypatch):
    x = sp.Symbol('x')
    domain, h = BasicSet((x,)), x**4+x*x+1
    proof = InvariantProver()(domain, h, 'quartic')
    assert proof['witness']['kind'] == 'putinar'
    assert proof['witness']['order'] == 2
    from contractive_tool.backends.cvxpy import mosek_solver
    monkeypatch.setattr(mosek_solver, 'solve', lambda *a, **kw: pytest.fail('Replay invoked solver'))
    assert check_invariant_certificate(domain, h, proof)
    assert InvariantProver(saved_evidence={'proof':proof})(domain, h, 'quartic') == proof
    for change in ('model', 'values', 'conclusion'):
        bad = deepcopy(proof)
        if change == 'model':
            bad['witness']['model']['coefficient_equalities'].pop()
        elif change == 'values':
            bad['witness']['exact_values'] = dict.fromkeys(bad['witness']['exact_values'], '0')
        else:
            bad['conclusion'] = '0'
        assert not check_invariant_certificate(domain, h, bad)


def test_sos_fallback_uses_domain_multiplier():
    x = sp.Symbol('x')
    domain, h = BasicSet((x,), (1-x*x,)), 2-x**4
    proof = InvariantProver()(domain, h, 'quartic on interval')
    assert proof['witness']['kind'] == 'putinar'
    assert check_invariant_certificate(domain, h, proof)
    assert not check_invariant_certificate(BasicSet((x,)), h, proof)


def test_sos_invariant_source_and_public_workflow_replay(tmp_path, monkeypatch):
    source = tmp_path/'quartic.pp'
    source.write_text('x := 2; {x*x*x*x+x*x+1 >= 0} while x >= 1 do '
                      '{x*x*x*x+x*x+1 >= 0} x := 0.5*x+0.25 od; refute true;')
    root = tmp_path/'run'
    result = run_analysis(source, 'tailbound', root,
        options=SearchOptions(initial_degree=1, max_degree=1, c_values=('3/4',),
            max_c_steps=1, total_seconds=15, reciprocal_seconds=0,
            per_attempt_seconds=3, repair_seconds=1, verbose=False))
    assert result['status'] == 'proved'
    assert 'symbolic_workflow' in result
    saved = json.loads((root/'analyses/tailbound/domain_evidence.json').read_text())
    assert 'putinar' in str(saved)
    round_ = prepare_random_round(source, invariant_evidence=saved)
    fixed = search_fixed_eta(round_, sp.Symbol('x'), options=CauchyOptions(total_seconds=10, scalar_strategy="sos", scalar_order=1))
    assert fixed['status'] == 'proved'
    from contractive_tool.backends.cvxpy import mosek_solver
    monkeypatch.setattr(mosek_solver, 'solve', lambda *a, **kw: pytest.fail('Replay invoked solver'))
    assert verify_result(prepare_random_round(source, invariant_evidence=saved), fixed)['status'] == 'proved'
    assert verify_workflow(root)['status'] == 'proved'
    path = root/'analyses/tailbound/domain_evidence.json'
    bad = deepcopy(saved)
    bad['proofs'].pop()
    path.write_text(json.dumps(bad))
    assert verify_workflow(root)['status'] == 'verification_failed'
    with pytest.raises(AnalysisError):
        prepare_random_round(source, invariant_evidence=bad)
