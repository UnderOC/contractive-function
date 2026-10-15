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
        options=SearchOptions(initial_degree=0,max_degree=2,c_values=('9/10','99/100'),tail_rule='late_bad_exit'))
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
        options=SearchOptions(initial_degree=2,max_degree=3,c_values=('1/2',),max_attempts_per_point=1))
    assert result['status']=='no_certificate_found',result
    assert result['degrees_attempted']==[2,3] and result['selection'] is None
    assert result['attempt_count']==2
    history=json.loads((tmp_path/'solve/analyses/tailbound/search_history.json').read_text())
    assert all(row['status'] in {'infeasible','numerical_issue','solved_unverified'} for row in history)
    assert list((tmp_path/'solve').rglob('solver.log'))


def test_probabilistic_uniform_bound_covers_exact_geometric_tail(tmp_path,mosek_available):
    from contractive_tool.analysis_pipeline import run_analysis, SearchOptions
    result=run_analysis(PROJECT/'tests/fixtures/geometric_exit.pp','tailbound',tmp_path/'geometric',
                        options=SearchOptions(initial_degree=2,tail_rule='late_bad_exit',c_values=('1/2','9/10','99/100')))
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


@pytest.mark.parametrize('filename,count,c', [('01_coupon2.pp',2,'1/2'),('02_coupon4.pp',4,'3/4')])
def test_round_tail_synthesis_recovers_exact_coupon_certificate(tmp_path,mosek_available,filename,count,c):
    from contractive_tool.analysis_pipeline import run_analysis, SearchOptions
    out = tmp_path/'round'
    result = run_analysis(PROJECT/'tailbound_benchmark_pack/pp'/filename,'tailbound',out,
                          options=SearchOptions(max_degree=1))
    assert result['status'] == 'proved', result
    assert result['tail_rule'] == 'round_survival'
    assert result['parameter_points'] == 10
    search = result['contraction_searches'][0]
    assert search['method'] == 'bisection' and search['stop_reason'] == 'max_c_steps'
    assert search['best_verified_c'] == c
    assert search['steps'][0]['c'] == '1/2'
    assert sp.Rational(search['interval'][1])-sp.Rational(search['interval'][0]) == sp.Rational(1,1024)
    bound = result['selection']
    assert bound['c'] == c and bound['A_exact'] == str(count)
    assert bound['event'] == 'K > n' and bound['time_unit'] == 'completed_loop_iterations'
    certificate = json.loads((out/bound['certificate']).read_text())
    eta = sp.sympify(next(iter(certificate['polynomials'].values())))
    assert sp.expand(eta-(count-sum(sp.Symbol(f'c{i}') for i in range(count)))) == 0
    # Independent exact coupon-collector distribution, for checking the clock/bound.
    probabilities = [sp.Integer(1)]+[sp.Integer(0)]*count
    for n in range(40):
        assert 1-probabilities[count] <= count*sp.Rational(c)**n
        probabilities = [probabilities[j]*sp.Rational(j,count)
                         +(probabilities[j-1]*sp.Rational(count-j+1,count) if j else 0)
                         for j in range(count+1)]
    verification = json.loads((out/bound['certificate']).with_name('verification.json').read_text())
    assert verification['status'] == 'proved'
    assert verification['round_evidence'] == 'round_evidence.json'


def test_round_mode_rejects_unsupported_input_and_assertion_stays_model_only(tmp_path):
    from contractive_tool.analysis_pipeline import run_analysis, SearchOptions
    options = SearchOptions(initial_degree=1,max_degree=1,tail_rule='round_survival')
    source=tmp_path/'nested.pp'
    source.write_text('x := 2; while x > 0 do while x > 0 do x := x - 1 od od; refute true;')
    unsupported = run_analysis(source,'tailbound',tmp_path/'unsupported',options=options)
    assert unsupported['status'] == 'unsupported'
    assert unsupported['stop_reason'] == 'round_evidence_unavailable'
    assertion = run_analysis(PROJECT/'tailbound_benchmark_pack/pp/02_coupon4.pp','assertion_violation',
                             tmp_path/'assertion',options=options)
    assert assertion['status'] == 'not_solved'
    assert assertion['stop_reason'] == 'assertion_backend_not_implemented'
    assert not list((tmp_path/'assertion').rglob('solver.json'))


def test_bisection_preserves_verified_certificate_on_inconclusive_next_point(tmp_path,mosek_available,monkeypatch):
    from contractive_tool.analysis_pipeline import run_analysis, SearchOptions
    from contractive_tool.backends.cvxpy import mosek_solver
    real_solve=mosek_solver.solve
    calls=0
    def unknown_after_first(*args,**kwargs):
        nonlocal calls
        calls+=1
        if calls==1:
            return real_solve(*args,**kwargs)
        return {'status':'numerical_issue','raw_status':None,'log':'test unknown'}
    monkeypatch.setattr(mosek_solver,'solve',unknown_after_first)
    result=run_analysis(PROJECT/'tests/fixtures/geometric_exit.pp','tailbound',tmp_path/'partial',
                        options=SearchOptions(initial_degree=1,max_c_steps=4,max_attempts_per_point=1))
    assert result['status']=='proved' and result['selection']['c']=='1/2'
    assert result['parameter_points']==2
    search=result['contraction_searches'][0]
    assert search['interval']==['0','1/2']
    assert search['stop_reason']=='oracle_inconclusive'


def test_rcd_symbolic_round_synthesis_is_generic_and_matches_exact_tail(tmp_path,mosek_available):
    from contractive_tool.analysis_pipeline import run_analysis, SearchOptions
    source=tmp_path/'renamed_coordinates.pp'
    source.write_text((PROJECT/'RCD_example.pp').read_text().replace('x','u').replace('y','v'))
    out=tmp_path/'rcd'
    result=run_analysis(source,'tailbound',out,options=SearchOptions(max_degree=2,max_c_steps=5))
    assert result['status']=='proved',result
    assert result['degrees_attempted']==[1,2]
    bound=result['selection']
    assert bound['kernel']=='symbolic' and bound['c']=='5/8' and bound['A_exact']=='1024'
    assert result['termination']=='proved_almost_sure' and not result['termination_assumed']
    certificate=json.loads((out/bound['certificate']).read_text())
    eta=sp.sympify(next(iter(certificate['polynomials'].values())))
    u,v=sp.symbols('u v'); h=(u+v/2)*(v+u/2)
    expected=sp.Rational(4096,3)*(u*u+u*v+v*v)
    assert sp.rem(eta-expected,h,u,v)==0
    pre=(eta.subs(u,-v/2)+eta.subs(v,-u/2))/2
    assert sp.rem(sp.Rational(5,8)*eta-pre,h,u,v)==0
    assert eta.subs({u:-sp.Rational(1,64),v:sp.Rational(1,32)})==1
    for n in range(80):
        # Five effective updates reach the threshold exactly; K>n means at most four.
        exact=sum(sp.binomial(n,j) for j in range(min(4,n)+1))/sp.Integer(2)**n
        assert exact<=1024*sp.Rational(5,8)**n
    verification=json.loads((out/bound['certificate']).with_name('verification.json').read_text())
    assert verification['status']=='proved'


def test_symbolic_nonterminating_loop_cannot_obtain_zero_certificate(tmp_path,mosek_available):
    from contractive_tool.analysis_pipeline import run_analysis, SearchOptions
    source=tmp_path/'forever.pp'
    source.write_text('x := 2; while true do x := x od; refute true;')
    result=run_analysis(source,'tailbound',tmp_path/'forever',
                        options=SearchOptions(max_degree=1,max_c_steps=2))
    assert result['tail_rule']=='round_survival' and result['selection'] is None
    assert result['status']=='no_certificate_found'
