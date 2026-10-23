import json
from pathlib import Path

from contractive_tool.analysis_pipeline import SearchOptions, run_analysis
from contractive_tool.backends.cvxpy import mosek_solver

PROJECT=Path(__file__).resolve().parents[2]


def test_parameter_budget_and_numerical_failure_do_not_claim_nonexistence(tmp_path,monkeypatch):
    monkeypatch.setattr(mosek_solver,'solve',lambda *a,**kw:
        {'status':'numerical_issue','raw_status':None,'diagnostic':'test unknown','log':'unknown'})
    result=run_analysis(PROJECT/'tests/fixtures/halving.pp','tailbound',tmp_path/'limited',
        options=SearchOptions(max_parameter_points=1,max_attempts_per_point=1))
    assert result['status']=='no_certificate_found'
    assert result['stop_reason']=='parameter_budget' and result['parameter_points']==1
    history=json.loads((tmp_path/'limited/analyses/tailbound/search_history.json').read_text())
    assert history[0]['status']=='numerical_issue'
    search=result['contraction_searches'][0]
    assert search['interval']==['0','1'] and search['stop_reason'] is None
    assert len(search['steps'])==1  # The global budget stops the pending probe.


def test_environment_failure_stops_without_escalating(tmp_path,monkeypatch):
    monkeypatch.setattr(mosek_solver,'solve',lambda *a,**kw:
        {'status':'solver_failed','raw_status':None,'diagnostic':'license unavailable','log':'unavailable'})
    result=run_analysis(PROJECT/'tests/fixtures/halving.pp','tailbound',tmp_path/'unavailable')
    assert result['status']=='solver_failed' and result['degrees_attempted']==[1]
    assert result['parameter_points']==1


def test_resource_limit_keeps_diagnostic_artifacts(tmp_path):
    result=run_analysis(PROJECT/'tests/fixtures/halving.pp','tailbound',tmp_path/'limit',
        options=SearchOptions(max_degree=2,max_decisions=1))
    assert result['status']=='no_certificate_found' and result['attempt_count']==0
    history=json.loads((tmp_path/'limit/analyses/tailbound/search_history.json').read_text())
    assert all(row['status']=='generation_failed' and 'budget' in row['reason'] for row in history)


def test_bisection_restarts_at_each_degree_and_limits_parameter_points(tmp_path,monkeypatch):
    monkeypatch.setattr(mosek_solver,'solve',lambda *a,**kw:
        {'status':'infeasible','raw_status':'infeasible','log':'test oracle'})
    result=run_analysis(PROJECT/'tests/fixtures/geometric_exit.pp','tailbound',tmp_path/'degrees',
        options=SearchOptions(initial_degree=0,max_degree=1,max_c_steps=3,max_attempts_per_point=1))
    assert result['status']=='no_certificate_found' and result['degrees_attempted']==[0,1]
    assert result['parameter_points']==6
    for search in result['contraction_searches']:
        assert [s['c'] for s in search['steps']]==['1/2','3/4','7/8']
        assert search['stop_reason']=='max_c_steps'
        assert search['best_verified_c'] is None
