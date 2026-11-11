"""Kelly: independent budgets, three result groups and source-only replay."""
from copy import deepcopy
import json
from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis_pipeline import SearchOptions, run_analysis
from contractive_tool.analysis.symbolic_workflow import compare_candidates, verify_workflow

PROJECT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def kelly_workflow(tmp_path_factory):
    cp = pytest.importorskip('cvxpy')
    pytest.importorskip('mosek')
    x = cp.Variable()
    try:
        cp.Problem(cp.Minimize(x),[x>=1]).solve(solver=cp.MOSEK)
    except cp.error.SolverError as error:
        pytest.skip(str(error))
    root = tmp_path_factory.mktemp('reciprocal_workflow')
    config = root/'config.json'
    config.write_text(json.dumps({'max_fixed_seeds':1,'t_values':['1/2'],
        'exponents':{'interval':None,'values':['1/2','1','3/2']},
        'reciprocal':{'growth_values':['33/32'],'feedback_points':1}}))
    options = SearchOptions(initial_degree=2,max_degree=2,c_values=('99/100',),
        tail_variables=('wealth',),total_seconds=30,reciprocal_seconds=30,
        per_attempt_seconds=5,repair_seconds=3,workflow_config=str(config),verbose=False,
        comparison_ns=(20,100,1000))
    result = run_analysis(PROJECT/'contractive_examples/kelly/K6_two_sided_exit.pp','tailbound',root/'run',options=options)
    return root/'run',result,options


def test_three_groups_have_verified_results_and_exact_envelope(kelly_workflow):
    root,result,_ = kelly_workflow
    assert result['status']=='proved'
    workflow = result['symbolic_workflow']
    stage = next(s for s in workflow['stages'] if s['stage']=='reciprocal')
    assert stage['status']=='proved' and stage['budget_seconds']==30
    for row in workflow['comparisons']:
        assert row['integer'] and row['noninteger'] and row['reciprocal']
        assert row['integer']['method']!='reciprocal'
        assert row['noninteger']['method']=='positive_jensen'
        assert row['reciprocal']['method']=='reciprocal'
        assert row['overall']['upper_bound_numeric'] <= min(row[k]['upper_bound_numeric']
            for k in ('integer','noninteger','reciprocal'))
    artifact=json.loads((root/stage['artifact']).read_text())
    assert artifact['input']['coefficients']  # denominator coefficients genuinely synthesized
    assert artifact['options']['variables']==['wealth']
    assert all(row['overall']['method']!='positive_jensen' for row in workflow['comparisons'])
    assert verify_workflow(root)['status']=='proved'


def test_cli_verifies_and_evaluates_both_routes_without_solver(kelly_workflow,monkeypatch,capsys):
    from contractive_tool.backends.cvxpy import mosek_solver
    from contractive_tool.cli import main
    def fail(*a,**kw): raise AssertionError('Replay must not solve')
    monkeypatch.setattr(mosek_solver,'solve',fail)
    root,result,_=kelly_workflow
    assert main(['verify',str(root)])==0
    capsys.readouterr()
    assert main(['evaluate',str(root),'--n','1000'])==0
    output=json.loads(capsys.readouterr().out)
    assert output['comparison']==result['symbolic_workflow']['comparisons'][-1]
    assert output['upper_bound_exact']==output['comparison']['overall']['upper_bound_exact']
    # Large powers serialize without disabling Python's integer-string limit.
    assert compare_candidates(result['symbolic_workflow']['candidates'],10000)['overall']


@pytest.mark.parametrize('field',['reciprocal_eta','jensen_parent','reciprocal_reference','comparison'])
def test_integrated_provenance_tampering_is_rejected(kelly_workflow,field):
    root,result,_=kelly_workflow
    bad=deepcopy(result)
    candidates=bad['symbolic_workflow']['candidates']
    if field=='reciprocal_eta':
        next(c for c in candidates if c['method']=='reciprocal')['eta']='wealth'
    elif field=='jensen_parent':
        next(c for c in candidates if c['method']=='positive_jensen')['reference']['seed']='missing'
    elif field=='reciprocal_reference':
        next(c for c in candidates if c['method']=='reciprocal')['reference']['candidate']=9999
    else:
        bad['symbolic_workflow']['comparisons'][0]['overall']=None
    path=root/'summary.json';original=path.read_text()
    try:
        path.write_text(json.dumps(bad))
        assert verify_workflow(root)['status']=='verification_failed'
    finally:
        path.write_text(original)


def test_positive_budget_exhaustion_does_not_cancel_reciprocal(kelly_workflow,tmp_path):
    from dataclasses import replace
    _,_,options=kelly_workflow
    result=run_analysis(PROJECT/'contractive_examples/kelly/K6_two_sided_exit.pp','tailbound',tmp_path/'run',
        options=replace(options,total_seconds=.001))
    workflow=result['symbolic_workflow']
    assert result['status']=='proved'
    assert next(s for s in workflow['stages'] if s['stage']=='reciprocal')['status']=='proved'
    assert all(row['integer'] is None and row['overall']['method']=='reciprocal'
               for row in workflow['comparisons'])
    assert verify_workflow(tmp_path/'run')['status']=='proved'


def test_reciprocal_failure_retains_positive_proofs(kelly_workflow,tmp_path,monkeypatch):
    import contractive_tool.analysis.reciprocal as module
    def fail(*a,**kw): raise module.AnalysisError('simulated reciprocal failure')
    monkeypatch.setattr(module,'search_reciprocal',fail)
    _,_,options=kelly_workflow
    result=run_analysis(PROJECT/'contractive_examples/kelly/K6_two_sided_exit.pp','tailbound',tmp_path/'run',options=options)
    assert result['status']=='proved'
    workflow=result['symbolic_workflow']
    assert next(s for s in workflow['stages'] if s['stage']=='reciprocal')['status']=='unknown'
    assert all(row['reciprocal'] is None and row['integer'] for row in workflow['comparisons'])
    assert verify_workflow(tmp_path/'run')['status']=='proved'


def test_jensen_candidates_cannot_improve_parent(kelly_workflow):
    _,result,_=kelly_workflow
    pool={c['id']:c for c in result['symbolic_workflow']['candidates']}
    for c in pool.values():
        if c['method']!='positive_jensen':
            continue
        parent=pool[c['reference']['seed']]
        for n in (0,20,100,1000):
            value=lambda b:min(1,sp.Rational(b['prefactor_upper'])*sp.Rational(b['decay_upper'])**n)
            assert value(parent)<=value(c)
