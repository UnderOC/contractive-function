from copy import deepcopy
import json
from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis_pipeline import SearchOptions, run_analysis
from contractive_tool.analysis.symbolic_workflow import compare_candidates, verify_workflow

PROJECT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def backend():
    cp = pytest.importorskip('cvxpy')
    pytest.importorskip('mosek')
    x = cp.Variable()
    try:
        cp.Problem(cp.Minimize(x),[x>=1]).solve(solver=cp.MOSEK)
    except cp.error.SolverError as error:
        pytest.skip(str(error))


@pytest.fixture(scope='module')
def notes_workflow(tmp_path_factory,backend):
    root = tmp_path_factory.mktemp('symbolic_workflow')/'notes'
    result = run_analysis(PROJECT/'examples/cauchy_notes.pp','tailbound',root,
        options=SearchOptions(max_degree=1,max_c_steps=6,total_seconds=60,
            per_attempt_seconds=5,repair_seconds=4,verbose=False,
            workflow_config=str(PROJECT/'examples/cauchy_workflow.json')))
    return root,result


def test_notes_full_pipeline_passes_real_direct_eta_to_cauchy(notes_workflow):
    root,result = notes_workflow
    workflow = result['symbolic_workflow']
    assert result['status']=='proved' and workflow['route']=='incumbent_fixed_then_joint'
    assert workflow['stages'][0]['stage']=='direct_polynomial'
    assert workflow['stages'][0]['budget_seconds']==30
    assert any(s['stage']=='cauchy_fixed' and s['status']=='proved' for s in workflow['stages'])
    assert any(s['stage']=='cauchy_joint' and s['status']=='proved' for s in workflow['stages'])
    direct = {c['id']:c for c in workflow['candidates'] if c['method']=='direct_polynomial'}
    assert direct and all(c['k']=='1' for c in direct.values())
    for stage in workflow['stages']:
        if stage['stage']=='cauchy_fixed' and stage['status']=='proved':
            artifact = json.loads((root/stage['artifact']).read_text())
            assert artifact['input']['eta']==direct[stage['seed']]['eta']
            assert artifact['input']['eta']!='x'  # actual first-phase coefficients, not injected notes eta
    assert verify_workflow(root)['status']=='proved'


def test_integer_and_rational_comparison_is_exact_nested_and_per_horizon(notes_workflow):
    root,result = notes_workflow
    workflow = result['symbolic_workflow']
    assert [r['n'] for r in workflow['comparisons']]==[5,20,100]
    for row in workflow['comparisons']:
        assert compare_candidates(workflow['candidates'],row['n'])==row
        assert sp.Rational(row['integer']['k']).q==1
        assert sp.Rational(row['rational']['k']).q>1
        assert row['rational_no_worse'] and row['strict_improvement']
        assert sp.Rational(row['integer_over_rational_exact'])>1
        assert row['direct_polynomial'] is not None
    assert result['selection']['selection_n']==5
    assert (root/'analyses/tailbound/workflow/comparison.md').is_file()


def test_full_workflow_checker_and_cli_evaluate_do_not_solve(notes_workflow,monkeypatch,capsys):
    from contractive_tool.backends.cvxpy import mosek_solver
    from contractive_tool.cli import main
    def fail(*a,**kw): raise AssertionError('Verification must not solve')
    monkeypatch.setattr(mosek_solver,'solve',fail)
    root,result = notes_workflow
    assert main(['verify',str(root)])==0
    capsys.readouterr()
    assert main(['evaluate',str(root),'--n','20'])==0
    data=json.loads(capsys.readouterr().out)
    assert data['comparison']==result['symbolic_workflow']['comparisons'][1]


@pytest.mark.parametrize('field',['comparison','candidate','selection','seed'])
def test_workflow_tampering_is_rejected(notes_workflow,field):
    root,result = notes_workflow
    path = root/'summary.json'
    original = path.read_text()
    bad=deepcopy(result)
    if field=='comparison':
        bad['symbolic_workflow']['comparisons'][0]['integer']['upper_bound_exact']='0'
    elif field=='candidate':
        bad['symbolic_workflow']['candidates'][0]['k']='2'
    elif field=='selection':
        bad['selection']['decay_upper']='0'
    else:
        stage=next(s for s in bad['symbolic_workflow']['stages'] if s['stage']=='cauchy_fixed')
        stage['seed']='nonexistent'
    try:
        path.write_text(json.dumps(bad))
        assert verify_workflow(root)['status']=='verification_failed'
    finally:
        path.write_text(original)


def test_no_direct_certificate_enters_joint_and_finds_subunit_k(tmp_path,backend):
    source=tmp_path/'rare.pp'
    source.write_text('x := 2; {x >= 0} while x >= 1 do '
        '{x >= 1} if prob(0.99) then {x >= 1} x := 0.5*x '
        'else {x >= 1} x := 100*x fi od; refute true;')
    config=tmp_path/'config.json'
    config.write_text(json.dumps({
        'basis':['1/2 + 199*__cauchy_r_0/2'],
        'template':{'expression':'a*x','coefficients':['a'],'nonnegative':['a']},
        't_values':['1','11/10'],
        'exponents':{'interval':None,'values':['1/4','1/2','1','2']},
        'max_fixed_seeds':1}))
    result=run_analysis(source,'tailbound',tmp_path/'out',options=SearchOptions(
        max_degree=1,c_values=('9/10',),total_seconds=45,per_attempt_seconds=5,
        repair_seconds=3,verbose=False,workflow_config=str(config)))
    assert result['status']=='proved'
    workflow=result['symbolic_workflow']
    assert workflow['route']=='joint_without_polynomial_certificate'
    assert next(s for s in workflow['stages'] if s['stage']=='cauchy_fixed')['reason']=='no_polynomial_certificate'
    assert all(c['method']=='cauchy_joint' for c in workflow['candidates'])
    assert any(sp.Rational(c['k'])<1 for c in workflow['candidates'])
    assert all(r['integer'] is None and r['rational'] is not None for r in workflow['comparisons'])
    assert verify_workflow(tmp_path/'out')['status']=='proved'


def test_boolean_macro_path_does_not_enter_symbolic_workflow(tmp_path,backend,monkeypatch):
    import contractive_tool.analysis.symbolic_workflow as module
    def fail(*a,**kw): raise AssertionError('Boolean path must remain separate')
    monkeypatch.setattr(module,'run_symbolic_workflow',fail)
    result=run_analysis(PROJECT/'tests/fixtures/geometric_exit.pp','tailbound',tmp_path/'out',
        options=SearchOptions(max_degree=1,max_c_steps=3,verbose=False))
    assert result['status']=='proved' and 'symbolic_workflow' not in result
    assert not (tmp_path/'out/analyses/tailbound/workflow').exists()


def test_unsupported_cauchy_distribution_preserves_direct_certificate(tmp_path,backend):
    source=tmp_path/'uniform.pp'
    source.write_text('x := 2; {x >= 0} while x >= 1 do '
                      '{x >= 1} x := Uniform(0,0.5) od; refute true;')
    result=run_analysis(source,'tailbound',tmp_path/'out',options=SearchOptions(
        max_degree=1,c_values=('1/2',),total_seconds=30,verbose=False))
    assert result['status']=='proved'
    workflow=result['symbolic_workflow']
    assert any(s['stage']=='cauchy_prepare' and s['status']=='unsupported' for s in workflow['stages'])
    assert all(c['method']=='direct_polynomial' for c in workflow['candidates'])
    assert all(r['integer']['id']==r['rational']['id'] for r in workflow['comparisons'])
    assert verify_workflow(tmp_path/'out')['status']=='proved'


def test_cauchy_failure_preserves_direct_portfolio(notes_workflow,tmp_path,monkeypatch,backend):
    import contractive_tool.analysis.symbolic_workflow as module
    def fail(*a,**kw): raise module.AnalysisError('simulated Cauchy failure')
    monkeypatch.setattr(module,'search_fixed_eta',fail)
    monkeypatch.setattr(module,'search_template_eta',fail)
    result=run_analysis(PROJECT/'tests/fixtures/halving.pp','tailbound',tmp_path/'out',
        options=SearchOptions(max_degree=1,c_values=('3/4',),total_seconds=30,verbose=False))
    assert result['status']=='proved'
    workflow=result['symbolic_workflow']
    assert any(s['status']=='unknown' for s in workflow['stages'])
    assert all(c['method']=='direct_polynomial' for c in workflow['candidates'])
    assert verify_workflow(tmp_path/'out')['status']=='proved'
