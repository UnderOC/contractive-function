from copy import deepcopy
from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis.invariant_certification import (
    InvariantProver, check_invariant_certificate, quadratic_matrix)
from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.backends.cvxpy.verification import exact_psd
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.ir import BasicSet

PROJECT = Path(__file__).resolve().parents[2]
x, y = sp.symbols('x y')


@pytest.mark.parametrize('h,positive', [
    (3*y*y/4, True), ((x+2*y-3)**2, True),
    ((x+y/2)**2/4+3*y*y/4, True),
    (x*x-1, False), (x*x+2*x, False), (x*y, False)])
def test_exact_quadratic_including_singular_and_shifted(h, positive):
    matrix = quadratic_matrix((x, y), h)
    assert matrix is not None
    assert exact_psd(matrix) is positive


def test_quadratic_remainder_keeps_domain_and_checks_all_fields(monkeypatch):
    from contractive_tool.backends.cvxpy import mosek_solver
    monkeypatch.setattr(mosek_solver, 'solve', lambda *a, **kw: pytest.fail('Unexpected solver'))
    f = x*x+x*y+y*y
    domain = BasicSet((x,y), (f, 2*(3-f)))
    h = 3-sp.Rational(3,4)*y*y
    certificate = InvariantProver()(domain, h, 'upper invariant')
    assert certificate['witness']['weight'] == '1/2'
    assert check_invariant_certificate(domain, h, certificate)
    for field in ('weight', 'matrix', 'domain', 'conclusion'):
        bad = deepcopy(certificate)
        if field == 'weight':
            bad['witness']['weight'] = '-1/2'
        elif field == 'matrix':
            bad['witness']['matrix'][0][0] = '1'
        elif field == 'domain':
            bad['domain']['generators'].pop()
        else:
            bad['conclusion'] = '0'
        assert not check_invariant_certificate(domain, h, bad)
    assert not check_invariant_certificate(BasicSet((x,y)), h, certificate)


def test_affine_equality_is_rebuilt_not_trusted():
    domain = BasicSet((x,y), equalities=(y-x,))
    proof = InvariantProver()(domain, x*y, 'equality substitution')
    assert check_invariant_certificate(domain, x*y, proof)
    assert not check_invariant_certificate(BasicSet((x,y)), x*y, proof)


@pytest.mark.parametrize('source', sorted((PROJECT/'contractive_examples/rcd').glob('*.pp')))
def test_all_rcd_prepare_and_replay_without_solver(source, monkeypatch):
    from contractive_tool.backends.cvxpy import mosek_solver
    monkeypatch.setattr(mosek_solver, 'solve', lambda *a, **kw: pytest.fail('RCD should use exact algebraic proofs'))
    round_ = prepare_random_round(source)
    saved = round_.evidence['domain_evidence']
    # R6's equality invariant closes with exact Farkas identities; the
    # original inequality examples require the quadratic SOS path.
    expected = ('exact_farkas_identity' if source.stem == 'rcd_06_equality_reference'
                else 'exact_invariant_sos')
    assert expected in str(saved)
    assert prepare_random_round(source, invariant_evidence=saved).to_data() == round_.to_data()
    bad = deepcopy(saved)
    # Removing a source transition's entire proof must also be rejected.
    bad['proofs'].pop()
    with pytest.raises(AnalysisError):
        prepare_random_round(source, invariant_evidence=bad)


def test_numerical_success_alone_is_not_a_proof(monkeypatch):
    from contractive_tool.backends.cvxpy import builder, mosek_solver, verification
    monkeypatch.setattr(builder, 'build', lambda model: model)
    monkeypatch.setattr(mosek_solver, 'solve', lambda *a, **kw: {'status':'solved_unverified','values':{}})
    monkeypatch.setattr(verification, 'reconstruct', lambda *a, **kw: {'status':'solved_unverified','reason':'test'})
    with pytest.raises(AnalysisError, match='Cannot certify'):
        InvariantProver()(BasicSet((x,)), x**4+x*x+1, 'quartic')


def test_expired_budget_does_not_call_solver(monkeypatch):
    from contractive_tool.backends.cvxpy import mosek_solver
    monkeypatch.setattr(mosek_solver, 'solve', lambda *a, **kw: pytest.fail('Expired budget'))
    with pytest.raises(AnalysisError, match='invariant_time_budget'):
        InvariantProver(total_seconds=0)(BasicSet((x,)), x**4+1, 'quartic')


def test_false_invariant_rejected_without_trusting_annotation(tmp_path):
    source = tmp_path/'false.pp'
    source.write_text('x := 0; {x*x <= 1} while x < 1 do {x*x <= 1} x := 2 od; refute true;')
    with pytest.raises(AnalysisError, match='Cannot certify inductive invariant'):
        prepare_random_round(source)


def test_empty_target_region_reports_analysis_error(tmp_path):
    source = tmp_path/'empty.pp'
    source.write_text('x := 0; while x < 1 do {false} x := 2 od; refute true;')
    with pytest.raises(AnalysisError, match='no target invariant region'):
        prepare_random_round(source)
