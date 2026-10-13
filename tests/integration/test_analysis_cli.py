import json
import subprocess
import sys
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[2]


def cli(*args):
    return subprocess.run([sys.executable,'-m','contractive_tool',*map(str,args)],text=True,capture_output=True)


def test_model_only_and_source_derived_goal(tmp_path):
    out=tmp_path/'model'
    process=cli('build-model',PROJECT/'kelly_unbounded.pp','--goal','tailbound','--out-dir',out,
                '--enabled-strategies','putinar')
    assert process.returncode==0,process.stderr
    summary=json.loads(process.stdout)
    assert summary['status']=='not_solved'
    goal=json.loads((out/'analyses/tailbound/goal.json').read_text())
    assert goal['initial']=={'wealth':'1','round':'0'} and goal['prefix_steps']==2
    assert goal['event_mode']=='late_bad_exit' and not goal['termination_assumed']
    assert not list(out.rglob('solver.json'))
    assert list(out.rglob('conic_model.json'))
    assert any('disabled' in p.read_text() for p in out.rglob('encoding_plan.json'))


def test_assertion_never_invokes_backend(tmp_path):
    out=tmp_path/'assertion'
    process=cli('solve',PROJECT/'kelly_unbounded.pp','--goal','assertion_violation','--out-dir',out)
    assert process.returncode==0,process.stderr
    result=json.loads(process.stdout)
    assert result['status']=='not_solved' and result['stop_reason']=='assertion_backend_not_implemented'
    assert list(out.rglob('polynomial_problem.json')) and not list(out.rglob('solver.json'))
    assert not list(out.rglob('conic_model.json'))


def test_only_source_and_target_are_required(tmp_path):
    source=tmp_path/'source.pp';source.write_text('x := 0; refute true;')
    process=subprocess.run([sys.executable,'-m','contractive_tool','analyze',str(source),
                            '--goal','assertion_violation'],cwd=tmp_path,text=True,capture_output=True)
    assert process.returncode==0,process.stderr
    assert Path(json.loads(process.stdout)['out_dir']).is_dir()


def test_old_arguments_and_fractional_family_rejected(tmp_path):
    process=cli('solve',PROJECT/'kelly_unbounded.pp','--goal','tailbound','--horizon','16')
    assert process.returncode==2
    process=cli('solve',PROJECT/'kelly_unbounded.pp','--goal','tailbound','--family','fractional_power')
    assert process.returncode==2 and 'fractional_k_not_implemented' in process.stderr


def test_evaluate_requires_verified_certificate(tmp_path):
    (tmp_path/'summary.json').write_text('{"status":"no_certificate_found"}')
    result=cli('evaluate',tmp_path,'--n','10')
    assert result.returncode==2 and 'no proved' in result.stderr
