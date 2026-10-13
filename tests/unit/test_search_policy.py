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


def test_environment_failure_stops_without_escalating(tmp_path,monkeypatch):
    monkeypatch.setattr(mosek_solver,'solve',lambda *a,**kw:
        {'status':'solver_failed','raw_status':None,'diagnostic':'license unavailable','log':'unavailable'})
    result=run_analysis(PROJECT/'tests/fixtures/halving.pp','tailbound',tmp_path/'unavailable')
    assert result['status']=='solver_failed' and result['degrees_attempted']==[2]
    assert result['parameter_points']==1


def test_resource_limit_keeps_diagnostic_artifacts(tmp_path):
    result=run_analysis(PROJECT/'tests/fixtures/halving.pp','tailbound',tmp_path/'limit',
        options=SearchOptions(max_degree=2,max_decisions=1))
    assert result['status']=='no_certificate_found' and result['attempt_count']==0
    history=json.loads((tmp_path/'limit/analyses/tailbound/search_history.json').read_text())
    assert all(row['status']=='generation_failed' and 'budget' in row['reason'] for row in history)
