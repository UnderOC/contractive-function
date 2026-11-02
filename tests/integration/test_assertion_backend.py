import json
from pathlib import Path

import sympy as sp

from contractive_tool.analysis_pipeline import SearchOptions, run_analysis
from contractive_tool.assertion_pipeline import verify_assertion, evaluate_assertion


def settings(**kwargs):
    return SearchOptions(**{'initial_degree':0,'max_degree':0,'c_values':('99/100',),
        'max_attempts_per_point':1,'total_seconds':30,'verbose':False,**kwargs})


def test_real_solver_failure_probability_replay_and_tampering(tmp_path):
    source = tmp_path/'coin.pp'
    source.write_text('x := 0; if prob(0.25) then refute true else skip fi;')
    out = tmp_path/'result'
    result = run_analysis(source, 'assertion_violation', out, options=settings())
    assert result['status'] == 'proved'
    assert result['termination'] == 'unknown' and not result['termination_assumed']
    value = sp.Rational(result['selection']['A_exact'])
    assert sp.Rational(1,4) <= value < sp.Rational(27,100)
    assert list(out.rglob('solver.json'))
    assert verify_assertion(out)['status'] == 'proved'
    assert evaluate_assertion(out)['upper_bound_exact'] == result['selection']['upper_bound_exact']
    assert evaluate_assertion(out, event='late_failure', n=0)['event'] == 'n < tau_f < infinity'
    # Summary and certificate claims are re-derived, not trusted as input.
    path = out/'summary.json'
    original = path.read_text()
    changed = json.loads(original)
    changed['selection']['A_exact'] = '0'
    path.write_text(json.dumps(changed))
    assert verify_assertion(out)['status'] == 'verification_failed'
    path.write_text(original)
    cert_path = out/result['selection']['certificate']
    cert = json.loads(cert_path.read_text())
    cert['raw_polynomials']['l_t'] = '0'
    cert_path.write_text(json.dumps(cert))
    assert verify_assertion(out)['status'] == 'verification_failed'


def test_assertion_never_uses_tail_workflow_or_requires_it(tmp_path, monkeypatch):
    import contractive_tool.analysis_pipeline as tail
    def forbidden(*args, **kwargs):
        raise AssertionError('Tail workflow must not run')
    monkeypatch.setattr(tail, '_run_polynomial_analysis', forbidden)
    monkeypatch.setattr(tail, 'prepare_round_kernel', forbidden)
    source = tmp_path/'immediate.pp'
    source.write_text('x := 0; refute true;')
    result = run_analysis(source, 'assertion_violation', tmp_path/'result', options=settings())
    assert result['status'] == 'proved'
    assert result['selection']['upper_bound_exact'] == '1'


def test_infinite_loop_is_not_mistaken_for_zero_risk_certificate(tmp_path):
    # A uniform positive raw eta cannot strictly contract on this self-loop.
    source = tmp_path/'nonterminating.pp'
    source.write_text('x := 0; if prob(0.25) then refute true else while true do skip od fi;')
    result = run_analysis(source, 'assertion_violation', tmp_path/'result', options=settings())
    assert result['status'] == 'no_certificate_found'
    assert result['selection'] is None
    assert result['termination'] == 'unknown'


def test_model_only_does_not_invoke_solver_and_numerical_unknown_is_not_proof(tmp_path, monkeypatch):
    from contractive_tool.backends.cvxpy import mosek_solver
    source = tmp_path/'immediate.pp'
    source.write_text('x := 0; refute true;')
    def forbidden(*args, **kwargs):
        raise AssertionError('Model-only invoked solver')
    monkeypatch.setattr(mosek_solver, 'solve', forbidden)
    model = run_analysis(source, 'assertion_violation', tmp_path/'model', options=settings(), model_only=True)
    assert model['stop_reason'] == 'model_only'
    assert list((tmp_path/'model').rglob('conic_model.json'))
    monkeypatch.setattr(mosek_solver, 'solve', lambda *a, **kw:
        {'status':'numerical_issue','raw_status':None,'log':'test unknown'})
    unknown = run_analysis(source, 'assertion_violation', tmp_path/'unknown', options=settings())
    assert unknown['status'] == 'no_certificate_found'


def test_best_initial_bound_is_selected_instead_of_smallest_c(tmp_path):
    source = tmp_path/'immediate.pp'
    source.write_text('x := 0; refute true;')
    result = run_analysis(source, 'assertion_violation', tmp_path/'result',
                          options=settings(c_values=('1/2','99/100')))
    assert result['status'] == 'proved' and len(result['proved_candidates']) == 2
    assert result['selection']['c'] == '99/100'
