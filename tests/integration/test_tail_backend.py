from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest
import sympy as sp

from contractive_tool.backends.cvxpy.builder import build
from contractive_tool.backends.cvxpy.mosek_solver import solve
from contractive_tool.backends.cvxpy.verification import reconstruct
from contractive_tool.positivity.ir import BasicSet, Implication
from contractive_tool.positivity.registry import StrategyRegistry
from contractive_tool.positivity.selector import build_plan


PROJECT=Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def mosek_available():
    pytest.importorskip("cvxpy")
    import cvxpy as cp
    pytest.importorskip("mosek")
    x=cp.Variable()
    try:
        cp.Problem(cp.Minimize(x),[x>=1]).solve(solver=cp.MOSEK)
    except Exception as error:
        if "license" in str(error).lower() or "1008" in str(error):
            pytest.skip(f"MOSEK license unavailable: {type(error).__name__}")
        raise


@pytest.mark.parametrize("strategy",StrategyRegistry.known)
def test_real_mosek_interval_nonnegative_certificate(strategy,mosek_available):
    x=sp.Symbol("x")
    obligation=Implication("interval",BasicSet((x,),(x,1-x)),x*(1-x),{},("test",))
    model,_=build_plan([obligation],[],sp.Integer(0),StrategyRegistry(),strategy,
                      order=2,handelman_degree=2,fallback=False)
    result=solve(build(model))
    assert result["raw_status"]=="optimal",result
    verified=reconstruct(model,result["values"])
    # LP can be exactly reconstructed; a singular SDP must at least remain explicitly unverified.
    assert verified["status"] in {"proved","solved_unverified"}


def test_real_mosek_simple_sdp_and_infeasible_model(mosek_available):
    import cvxpy as cp
    t=cp.Variable()
    problem=cp.Problem(cp.Minimize(t),[cp.bmat([[t,1],[1,t]]) >> 0])
    problem.solve(solver=cp.MOSEK)
    assert problem.status=="optimal" and abs(problem.value-1)<1e-7
    infeasible=cp.Problem(cp.Minimize(t),[t>=1,t<=0])
    infeasible.solve(solver=cp.MOSEK)
    assert infeasible.status=="infeasible"



def test_real_degree_escalation_exact_uniform_bound_and_evaluation(tmp_path,mosek_available,monkeypatch):
    from contractive_tool.analysis_pipeline import run_analysis, SearchOptions
    from contractive_tool.cli import main
    from contractive_tool.backends.cvxpy import mosek_solver
    out=tmp_path/'halving'
    result=run_analysis(PROJECT/'tests/fixtures/halving.pp','tailbound',out,
        options=SearchOptions(initial_degree=0,max_degree=2,c_values=('9/10','99/100')))
    assert result['status']=='proved' and result['degrees_attempted']==[0,1]
    assert result['stop_reason']=='first_successful_degree'
    assert result['selection']['c']=='9/10' and len(result['proved_candidates'])==2
    # This source exits in exactly nine pCFG steps. The formula must cover every n.
    bound=result['selection']; A=sp.Rational(bound['A_exact']); c=sp.Rational(bound['c'])
    assert all(A*c**n>=1 for n in range(9))
    certificate=json.loads((out/bound['certificate']).read_text())
    assert certificate['integer_power_factorization_required'] is False
    verified=json.loads((out/bound['certificate']).with_name('verification.json').read_text())
    assert verified['status']=='proved' and verified['method']=='rational_affine_reconstruction_exact_psd'
    def must_not_solve(*args,**kwargs): raise AssertionError('Evaluation must not invoke solver')
    monkeypatch.setattr(mosek_solver,'solve',must_not_solve)
    assert main(['evaluate',str(out),'--n','50'])==0


def test_real_kelly_pipeline_is_generic_and_reports_search_scope(tmp_path,mosek_available):
    from contractive_tool.analysis_pipeline import run_analysis, SearchOptions
    # Renaming the file and variables cannot activate another certificate family.
    source=tmp_path/'renamed.pp'
    source.write_text((PROJECT/'kelly_unbounded.pp').read_text().replace('wealth','capital').replace('round','steps'))
    result=run_analysis(source,'tailbound',tmp_path/'solve',
        options=SearchOptions(max_degree=3,c_values=('1/2',),max_attempts_per_point=1))
    assert result['status']=='no_certificate_found',result
    assert result['degrees_attempted']==[2,3] and result['selection'] is None
    assert result['attempt_count']==2
    history=json.loads((tmp_path/'solve/analyses/tailbound/search_history.json').read_text())
    assert all(row['status'] in {'infeasible','numerical_issue','solved_unverified'} for row in history)
    assert list((tmp_path/'solve').rglob('solver.log'))


def test_probabilistic_uniform_bound_covers_exact_geometric_tail(tmp_path,mosek_available):
    from contractive_tool.analysis_pipeline import run_analysis
    result=run_analysis(PROJECT/'tests/fixtures/geometric_exit.pp','tailbound',tmp_path/'geometric')
    assert result['status']=='proved' and result['degrees_attempted']==[2]
    bound=result['selection']; A=sp.Rational(bound['A_exact']); c=sp.Rational(bound['c'])
    # J~Geom(1/2), T=3J+3 includes initialization, exit guard and refute.
    for n in range(100):
        exact_tail=sp.Rational(1,2)**max(0,(n-3)//3)
        assert exact_tail<=A*c**n
    assert len(result['pareto_candidates'])==2


def test_previously_proved_certificate_survives_later_solver_failure(tmp_path,mosek_available,monkeypatch):
    from contractive_tool.analysis_pipeline import run_analysis, SearchOptions
    from contractive_tool.backends.cvxpy import mosek_solver
    real_solve=mosek_solver.solve
    calls=0
    def fail_after_first(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==1:
            return real_solve(*args,**kwargs)
        return {'status':'solver_failed','raw_status':None,'diagnostic':'test environment failure','log':'failure'}
    monkeypatch.setattr(mosek_solver,'solve',fail_after_first)
    result=run_analysis(PROJECT/'tests/fixtures/halving.pp','tailbound',tmp_path/'partial',
                       options=SearchOptions(initial_degree=1,c_values=('9/10','99/100')))
    assert result['status']=='proved' and result['stop_reason']=='solver_failed'
    assert result['selection']['c']=='9/10'
    assert result['degrees_attempted']==[1]
