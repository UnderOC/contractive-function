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
    assert goal['event_mode']=='round_survival' and not goal['termination_assumed']
    assert goal['proof_domain']=='symbolic real polynomial invariant domains'
    assert not list(out.rglob('solver.json'))
    assert list(out.rglob('conic_model.json'))
    assert any('disabled' in p.read_text() for p in out.rglob('encoding_plan.json'))


def test_assertion_goal_is_unavailable_without_creating_output(tmp_path):
    out = tmp_path/'assertion'
    for command in ('solve', 'analyze', 'build-model'):
        process = cli(command, PROJECT/'kelly_unbounded.pp', '--goal',
                      'assertion_violation', '--out-dir', out)
        assert process.returncode == 2
        assert 'invalid choice' in process.stderr
        assert not out.exists()


def test_assertion_artifacts_are_rejected(tmp_path):
    (tmp_path/'summary.json').write_text(json.dumps({
        'goal': 'assertion_violation', 'status': 'proved', 'selection': {'bound': '1/2'}}))
    for command in ('verify', 'evaluate'):
        process = cli(command, tmp_path)
        assert process.returncode == 2
        assert 'Only tailbound' in process.stderr


def test_only_source_and_target_are_required(tmp_path):
    source=tmp_path/'source.pp';source.write_text('x := 0; refute true;')
    process=subprocess.run([sys.executable,'-m','contractive_tool','analyze',str(source),
                            '--goal','tailbound'],cwd=tmp_path,text=True,capture_output=True)
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
