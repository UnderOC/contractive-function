from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis.rounds import prepare_round_kernel, make_round_problem
from contractive_tool.analysis.semantics import prepare_program
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.parser import parse_text
from contractive_tool.frontend.semantic import check_program


PROJECT = Path(__file__).resolve().parents[2]


def compile_round(source):
    cfg = build_cfg(check_program(parse_text(source)))
    return cfg, prepare_round_kernel(cfg,prepare_program(cfg))


def test_coupon_kernel_strict_boundary_and_exact_moment_are_generic():
    source = (PROJECT/'tailbound_benchmark_pack/pp/02_coupon4.pp').read_text()
    for i in range(4):
        source = source.replace(f'c{i}',f'flag{i}')
    cfg,kernel = compile_round(source)
    assert len(kernel.states) == 16
    assert sum(row['active'] for row in kernel.states.values()) == 15
    assert not kernel.states[(1,1,1,1)]['active']
    assert kernel.to_data()['clock']['pcfg_relation'] == 'T = 4 + 4*K + 2'
    eta = 4-sum(kernel.variables)
    for state,row in kernel.states.items():
        value = eta.subs(dict(zip(kernel.variables,state)))
        if row['active']:
            assert value >= 1
            assert len(row['paths']) == 4
            assert {p['probability'] for p in row['paths']} == {'1/4'}
            pre = sum(sp.Rational(p['probability'])*eta.subs(dict(zip(kernel.variables,map(sp.Rational,p['state']))))
                      for p in row['paths'])
            assert pre == sp.Rational(3,4)*value
        else:
            assert value == 0
    problem = make_round_problem(cfg,kernel,1,sp.Rational(9,10))
    assert len(problem.decisions) == 5
    assert len(problem.obligations) == 31
    assert all(not o.domain.variables for o in problem.obligations)
    assert all(sp.Poly(o.conclusion,*map(sp.Symbol,problem.decisions)).total_degree() <= 1
               for o in problem.obligations)


def test_sequential_update_and_guard_are_evaluated_in_current_state():
    cfg,kernel = compile_round('''x := 0;
        {0 <= x and x <= 1} while x = 0 do
          x := 1;
          if x = 1 then x := 1 else x := 0 fi
        od; refute true;''')
    assert kernel.states[(0,)]['active']
    assert [p['state'] for p in kernel.states[(0,)]['paths']] == [['1']]
    assert not kernel.states[(1,)]['active']


@pytest.mark.parametrize('source,reason',[
    ('x := 0; while x < 3 do x := x + 1 od; refute true;', 'does not preserve'),
    ('x := 0; while x = 0 do while x = 0 do skip od od; refute true;', 'cyclic'),
    ('x := 0; while x = 0 do x := Uniform(0,1) od; refute true;', 'Sampled'),
    ('x := 0; while x = 0 do refute true od; refute true;', 'Early exits'),
])
def test_unsupported_rounds_are_rejected_with_reason(source,reason):
    with pytest.raises(AnalysisError,match=reason):
        compile_round(source)


def test_nontermination_cannot_get_a_zero_survival_certificate():
    cfg,kernel = compile_round('x := 0; while true do skip od; refute true;')
    problem = make_round_problem(cfg,kernel,1,sp.Rational(9,10))
    assert all(row['active'] for row in kernel.states.values())
    # Every state requires eta >= 1, while its self-loop requires eta <= 0.
    for i in range(len(kernel.states)):
        normalization,contraction = problem.obligations[2*i:2*i+2]
        assert sp.expand(normalization.conclusion+10*contraction.conclusion) == -1


def test_completed_polynomial_need_not_vanish_for_boolean_killed_process():
    cfg,kernel = compile_round((PROJECT/'tests/fixtures/geometric_exit.pp').read_text())
    problem = make_round_problem(cfg,kernel,0,sp.Rational(1,2))
    # V=1 is positive even at x=1. Killing the completed branch gives Pre=1/2.
    values = {sp.Symbol(name):sp.Integer(1) for name in problem.decisions}
    assert all(o.conclusion.xreplace(values)>=0 for o in problem.obligations)
    assert not any('completed_zero' in o.id for o in problem.obligations)
