from copy import deepcopy
from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis.cauchy import (
    CauchyOptions, ExponentOptions, EtaTemplate, search_fixed_eta, search_template_eta, evaluate)
from contractive_tool.analysis.cauchy_verification import verify_result
from contractive_tool.analysis.random_rounds import prepare_random_round

PROJECT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def notes_results(tmp_path_factory):
    cp=pytest.importorskip('cvxpy')
    pytest.importorskip('mosek')
    x=cp.Variable()
    try:
        cp.Problem(cp.Minimize(x),[x>=1]).solve(solver=cp.MOSEK)
    except cp.error.SolverError as error:
        pytest.skip(str(error))
    round_=prepare_random_round(PROJECT/'examples/cauchy_notes.pp')
    x,a,b=sp.symbols('x alpha beta'); basis=(1,10*round_.law.symbols[0])
    options=CauchyOptions(exponents=ExponentOptions(interval=('1/4','4'),coarse_points=16,refinements=1))
    root=tmp_path_factory.mktemp('cauchy')
    fixed=search_fixed_eta(round_,x,basis=basis,options=options,out_dir=root/'fixed')
    template=EtaTemplate(a*x+b,(a,b),(a,b),(a+b-1,))
    joint=search_template_eta(round_,template,t_values=('21/50','1/2','3/5','7/10'),
                             basis=basis,options=options,out_dir=root/'template')
    return round_,fixed,joint


def test_fixed_eta_recovers_notes_optimum_and_fractional_tail(notes_results):
    round_,result,_=notes_results
    assert result['status']=='proved'
    assert result['attempts'][0]['B']=='17/100'
    c=next(c for c in result['candidates'] if c['k']=='3/2')
    assert sp.Rational(c['decay_upper'])<sp.Rational(7,20)
    # Exact worst-case y=1 witnesses that B cannot be smaller for this eta/basis.
    x,y=sp.symbols('x y')
    _,q,_=round_.decompose(x,(1,10*round_.law.symbols[0]))
    assert sp.cancel(sum(v*v for v in q)/x**2).subs(y,1)==sp.Rational(17,100)


def test_template_eta_is_synthesized_at_each_t(notes_results):
    round_,_,result=notes_results
    assert result['status']=='proved'
    assert len(result['attempts'])==4 and all(a['status']=='proved' for a in result['attempts'])
    x=sp.Symbol('x')
    from contractive_tool.analysis.cauchy_expressions import parse_expression
    etas=[]
    for a in result['attempts']:
        eta=parse_expression(a['eta'],round_.variables)
        alpha,beta=eta.coeff(x),eta.subs(x,0)
        assert alpha.is_Rational and beta.is_Rational and 0<=alpha<=1 and alpha+beta==1
        assert alpha != 1  # actual optimization, not injected eta=x
        assert any(c['attempt']==result['attempts'].index(a) for c in result['candidates'])
        etas.append(eta)
    assert len(set(etas))==4


def test_independent_check_and_evaluation_do_not_call_solver(notes_results,monkeypatch):
    from contractive_tool.backends.cvxpy import mosek_solver
    def fail(*a,**kw): raise AssertionError('checker/evaluation must not solve')
    monkeypatch.setattr(mosek_solver,'solve',fail)
    round_,fixed,joint=notes_results
    for result in (fixed,joint):
        assert verify_result(round_,result)['status']=='proved'
        bound=evaluate(result,20)
        assert 0<sp.Rational(bound['upper_bound_exact'])<1
        assert sp.Rational(evaluate(result,0)['upper_bound_exact'])==1


@pytest.mark.parametrize('mutation', ['coefficient','B','moment','model','round','eta','formula'])
def test_tampered_artifacts_are_rejected(notes_results,mutation):
    round_,fixed,_=notes_results
    bad=deepcopy(fixed)
    if mutation=='coefficient':
        values=bad['attempts'][0]['verification']['exact_values']; values[next(iter(values))]='-1'
    elif mutation=='B': bad['candidates'][0]['B']='1/100'
    elif mutation=='moment': bad['candidates'][0]['moment']['upper']='0'
    elif mutation=='model': bad['attempts'][0]['model']['coefficient_equalities']=[]
    elif mutation=='round': bad['round']['law']['atoms'][0]['probability']='1'
    elif mutation=='eta': bad['candidates'][0]['eta']='x+1'
    elif mutation=='formula': bad['candidates'][0]['expression']='0'
    assert verify_result(round_,bad)['status']=='verification_failed'


def test_unknown_after_success_preserves_verified_candidates(notes_results,monkeypatch):
    import contractive_tool.analysis.cauchy as module
    round_,_,joint=notes_results
    first=joint['attempts'][0]
    calls=[]
    def replay(model,options,deadline):
        calls.append(model)
        if len(calls)==1:
            return {'status':'proved','verification':first['verification']}
        return {'status':'unknown','reason':'simulated_timeout'}
    monkeypatch.setattr(module,'_solve',replay)
    x,a,b=sp.symbols('x alpha beta')
    result=search_template_eta(round_,EtaTemplate(a*x+b,(a,b),(a,b),(a+b-1,)),
        basis=(1,10*round_.law.symbols[0]),t_values=('21/50','1/2'))
    assert result['status']=='proved' and result['attempts'][1]['status']=='unknown'
    assert result['candidates'] and verify_result(round_,result)['status']=='proved'


def test_zero_norm_and_initial_exit_have_correct_time_index(tmp_path,notes_results):
    source=tmp_path/'zero.pp'
    source.write_text('x := 2; while x >= 1 do x := 0 od; refute true;')
    round_=prepare_random_round(source)
    result=search_fixed_eta(round_,sp.Symbol('x'))
    assert result['status']=='proved' and result['special_case']=='one_step_termination'
    assert verify_result(round_,result)['status']=='proved'
    assert evaluate(result,0)['upper_bound_exact']=='1'
    assert evaluate(result,1)['upper_bound_exact']=='0'
    source.write_text('x := 0; while x >= 1 do x := 0 od; refute true;')
    round_=prepare_random_round(source)
    result=search_fixed_eta(round_,sp.Symbol('x'))
    assert verify_result(round_,result)['status']=='proved'
    assert evaluate(result,0)['upper_bound_exact']=='0'


def test_cli_replays_full_pipeline(tmp_path,capsys,notes_results):
    from contractive_tool.cauchy_cli import main
    assert main(['run',str(PROJECT/'examples/cauchy_notes.pp'),'--config',
        str(PROJECT/'examples/cauchy_notes.json'),'--mode','fixed','--out-dir',str(tmp_path/'run')])==0
    assert main(['verify',str(tmp_path/'run/fixed')])==0
    assert main(['evaluate',str(tmp_path/'run/fixed'),'--n','10'])==0


def test_negative_successor_cannot_pass_using_only_norm_bound(tmp_path,notes_results):
    source=tmp_path/'negative.pp'
    source.write_text('x := 2; while x >= 1 do x := -0.5*x od; refute true;')
    result=search_fixed_eta(prepare_random_round(source),sp.Symbol('x'))
    assert result['status']=='no_certificate_found' and not result['candidates']


def test_fractional_search_succeeds_when_first_moment_does_not_contract(tmp_path,notes_results):
    source=tmp_path/'rare_jump.pp'
    source.write_text('x := 2; while x >= 1 do if prob(0.99) then '
                      'x := 0.5*x else x := 100*x fi od; refute true;')
    round_=prepare_random_round(source)
    z=round_.law.symbols[0]
    result=search_fixed_eta(round_,sp.Symbol('x'),basis=(sp.Rational(1,2)+sp.Rational(199,2)*z,),
        options=CauchyOptions(exponents=ExponentOptions(values=('1/2','1'))))
    assert result['status']=='proved' and result['attempts'][0]['B']=='1'
    assert [c['k'] for c in result['candidates']]==['1/2']
    assert verify_result(round_,result)['status']=='proved'
