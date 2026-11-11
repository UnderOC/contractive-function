import time
from types import SimpleNamespace

import pytest
import sympy as sp

from contractive_tool.analysis_pipeline import SearchOptions
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.ir import ConicModel
from contractive_tool.backends.cvxpy import repair as module
from contractive_tool.backends.cvxpy.verification import reconstruct, exact_psd


def singular_model():
    x,y,z = sp.symbols('x y z')
    model = ConicModel(['x','y','z'],x,[4*x-12*y+9*z],[],
                       [{'id':'Q','matrix':[['x','y'],['y','z']]}])
    values = {'x':.3141592653,'y':.3141592653*2/3+1e-10,'z':.3141592653*4/9}
    return model,values


def check_original(model, result):
    assert result['status']=='proved'
    sub = {sp.Symbol(n):sp.Rational(v) for n,v in result['exact_values'].items()}
    assert all(e.xreplace(sub)==0 for e in model.equalities)
    assert all(sub[sp.Symbol(n)]>=0 for n in model.nonnegative)
    assert all(exact_psd([[sub[sp.Symbol(n)] for n in row] for row in b['matrix']])
               for b in model.psd_blocks)
    assert model.objective.xreplace(sub)==sp.Rational(result['bound_exact'])


def test_general_nonzero_diagonal_kernel_recovers_exact_certificate(monkeypatch):
    model,values = singular_model()
    assert reconstruct(model,values)['status']=='solved_unverified'
    monkeypatch.setattr(module.mosek_solver,'solve',lambda *a,**kw:
                        {'status':'numerical_issue','raw_status':None,'log':'forced margin failure'})
    result,audit = module.repair(model,values)
    check_original(model,result)
    assert result['repair_stage']=='kernel_reconstruction'
    assert audit['solver_calls']==1
    face = audit['attempts'][1]['face_guess']['blocks'][0]
    assert face['rank_guess']==1 and face['kernel']==[['-2/3'],['1']]


def test_wrong_kernel_guess_cannot_prove_indefinite_original_model(monkeypatch):
    model,values = singular_model()
    x,y,z = sp.symbols('x y z')
    model.equalities += [x-1,y-2,z-1]
    calls=[]
    def fail(*a,**kw):
        calls.append(kw)
        return {'status':'infeasible','raw_status':'infeasible','log':'bad face'}
    monkeypatch.setattr(module.mosek_solver,'solve',fail)
    result,audit=module.repair(model,values,options=module.RepairOptions(max_solves=2))
    assert result['status']=='solved_unverified'
    assert audit['status']=='solved_unverified' and len(calls)==2
    assert len(audit['attempts'])<=3


def test_expired_or_disabled_repair_never_calls_solver(monkeypatch):
    model,values=singular_model()
    def forbidden(*a,**kw):
        raise AssertionError('No solve after budget expiration')
    monkeypatch.setattr(module.mosek_solver,'solve',forbidden)
    for kwargs in ({'deadline':time.monotonic()-1}, {'options':module.RepairOptions(seconds=0)},
                   {'options':module.RepairOptions(max_solves=0)}):
        result,audit=module.repair(model,values,**kwargs)
        assert result['status']=='solved_unverified' and audit['attempts']==[]


@pytest.mark.parametrize('options', [dict(repair_seconds=-1),dict(repair_relative_gap=float('nan')),
                                     dict(repair_max_solves=3)])
def test_invalid_repair_options(options):
    with pytest.raises(AnalysisError,match='Repair budgets'):
        SearchOptions(**options).validate()


def test_reconstruction_deadline_reports_unknown():
    model,values=singular_model()
    result=reconstruct(model,values,deadline=time.monotonic()-1)
    assert result['status']=='solved_unverified'
    assert result['reason']=='reconstruction_time_budget'


@pytest.mark.parametrize('outer_seconds,expected_window', [(30,5), (8,2), (6,0)])
def test_late_solver_candidate_has_separate_recovery_window(monkeypatch, outer_seconds, expected_window):
    # Numerical compilation/solve may cooperatively overrun the local five
    # seconds. Recovery gets its own window, but never extends the parent.
    started=time.monotonic()
    clock=SimpleNamespace(now=started)
    monkeypatch.setattr(module,'time',SimpleNamespace(monotonic=lambda:clock.now))
    x=sp.Symbol('x')
    model=ConicModel(['x'],x,[x-1],['x'],[])
    monkeypatch.setattr(module,'build_margin_model',lambda *a,**kw:object())
    calls=[]
    def solve(*a,**kw):
        calls.append(kw)
        assert kw['time_limit']==5
        clock.now+=6
        return {'status':'optimal','values':{'x':1.0}}
    monkeypatch.setattr(module.mosek_solver,'solve',solve)
    recovered=[]
    def recover(model,values,*,deadline,objective_cap):
        recovered.append(deadline)
        assert deadline==started+6+expected_window
        return reconstruct(model,values,deadline=deadline,objective_cap=objective_cap)
    monkeypatch.setattr(module,'reconstruct',recover)
    result,audit=module.repair(model,{'x':1.0},options=module.RepairOptions(seconds=5),
                             deadline=started+outer_seconds)
    assert len(calls)==1
    assert audit['budget_policy']=='separate_post_solve_reconstruction_v1'
    row=audit['attempts'][0]
    assert row['reconstruction_available_seconds']==expected_window
    if expected_window:
        check_original(model,result)
        assert len(recovered)==1
        assert result['repair_stage']=='margin_solve'
    else:
        assert not recovered
        assert result['status']=='solved_unverified'
        assert row['status']=='reconstruction_time_budget'


@pytest.mark.parametrize('invalid_kind', ['indefinite', 'objective_cap'])
def test_separate_recovery_keeps_exact_psd_and_objective_checks(monkeypatch, invalid_kind):
    started=time.monotonic()
    clock=SimpleNamespace(now=started)
    monkeypatch.setattr(module,'time',SimpleNamespace(monotonic=lambda:clock.now))
    x,y,z=sp.symbols('x y z')
    values={'x':1.,'y':2.,'z':1.} if invalid_kind=='indefinite' else {'x':2.,'y':0.,'z':2.}
    model=ConicModel(['x','y','z'],x,[s-values[str(s)] for s in (x,y,z)],[],
                     [{'id':'Q','matrix':[['x','y'],['y','z']]}])
    monkeypatch.setattr(module,'build_margin_model',lambda *a,**kw:object())
    def solve(*a,**kw):
        clock.now+=6
        return {'status':'optimal','values':values}
    monkeypatch.setattr(module.mosek_solver,'solve',solve)
    result,audit=module.repair(model,{'x':1.,'y':0.,'z':1.},
                             options=module.RepairOptions(seconds=5),deadline=started+30)
    assert result['status']=='solved_unverified'
    assert audit['solver_calls']==1
    verification=audit['attempts'][0]['verification']
    assert verification['status']=='solved_unverified'
    if invalid_kind=='objective_cap':
        assert all(a['rejected_reason']=='Reconstructed objective exceeds cap'
                   for a in verification['attempts'])


def test_repair_retries_precision_after_first_exact_point_exceeds_cap(monkeypatch):
    x=sp.Symbol('x')
    model=ConicModel(['x'],x,[],['x'],[])
    # At denominator 1000 the feasible solver value rounds up to 1/3,
    # exceeding the cap 0.3333. Higher precision satisfies the same cap.
    initial={'x':0.3332}
    numerical={'x':0.333299}
    monkeypatch.setattr(module,'build_margin_model',lambda *a,**kw:object())
    monkeypatch.setattr(module.mosek_solver,'solve',lambda *a,**kw:
                        {'status':'optimal','values':numerical})
    result,audit=module.repair(model,initial,
                             options=module.RepairOptions(relative_gap=0,max_solves=1))
    check_original(model,result)
    assert sp.Rational(result['bound_exact'])<=sp.Rational(audit['objective_cap'])
    attempts=audit['attempts'][0]['verification']['attempts']
    assert attempts[0]['denominator']==1000
    assert attempts[0]['rejected_reason']=='Reconstructed objective exceeds cap'
    assert attempts[-1]['denominator']==1000000
