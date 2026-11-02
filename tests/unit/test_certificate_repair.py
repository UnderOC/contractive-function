import time

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
