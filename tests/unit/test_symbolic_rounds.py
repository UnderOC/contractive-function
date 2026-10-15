from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis.symbolic_rounds import prepare_symbolic_round_kernel, make_symbolic_round_problem
from contractive_tool.analysis.semantics import prepare_program
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.parser import parse_text
from contractive_tool.frontend.semantic import check_program


PROJECT = Path(__file__).resolve().parents[2]


def compile_round(source):
    cfg=build_cfg(check_program(parse_text(source)))
    return cfg,prepare_symbolic_round_kernel(cfg,prepare_program(cfg))


def holds(domain, values):
    return (all(g.subs(values)>=0 for g in domain.generators)
            and all(e.subs(values)==0 for e in domain.equalities))


def test_rcd_symbolic_expectation_and_nonzero_exit_boundary():
    cfg,kernel=compile_round((PROJECT/'RCD_example.pp').read_text())
    x,y=sp.symbols('x y')
    f=(x*x+x*y+y*y)/2
    cases=kernel.preconditions(f)
    assert len(cases)==1
    assert sp.expand(cases[0][1]-sp.Rational(3,16)*(x*x+y*y))==0
    assert kernel.to_data()['clock']['pcfg_relation']=='T = 2 + 3*K + 2'
    problem=make_symbolic_round_problem(cfg,kernel,2,sp.Rational(5,8))
    assert len(problem.decisions)==6
    # A completed state at the threshold has V=1, and must remain admissible.
    exit_state={x:-sp.Rational(1,64),y:sp.Rational(1,32)}
    assert (f*sp.Rational(8192,3)).subs(exit_state)==1
    assert all('completed_zero' not in o.id for o in problem.obligations)
    assert all(o.domain.equalities for o in problem.obligations)


def test_probabilistic_branches_with_conditional_updates_preserve_joint_cases():
    _,kernel=compile_round('''x := 2; while true do
      if prob(0.5) then
        x := x + 1;
        if x > 0 then x := 2*x else x := -x fi
      else x := x - 1 fi
    od; refute true;''')
    x=sp.Symbol('x')
    cases=kernel.preconditions(x)
    assert len(cases)==2
    for value in (-3,-1,0,2):
        expected=sp.Rational(1,2)*(2*(value+1) if value+1>0 else -(value+1))+sp.Rational(1,2)*(value-1)
        matches=[p.subs(x,value) for domain,p in cases if holds(domain,{x:value})]
        assert matches and all(p==expected for p in matches)


def test_fresh_samples_are_integrated_at_each_occurrence():
    _,kernel=compile_round('''random r ~ Bernoulli(0.5);
      x := 2; y := 0; while true do x := r; y := r od; refute true;''')
    x,y=sp.symbols('x y')
    cases=kernel.preconditions(x*y)
    assert len(cases)==1 and cases[0][1]==sp.Rational(1,4)


@pytest.mark.parametrize('source,reason',[
    ('x := 2; while x > 0 do x := Uniform(0,1); if x > 0.5 then x := 0 else x := 1 fi od; refute true;', 'truncated'),
    ('x := 2; while x > 0 do while x > 1 do x := x - 1 od od; refute true;', 'Nested'),
    ('x := 2; while x > 0 do if prob(0.5) then refute true else x := 0 fi od; refute true;', 'body paths'),
])
def test_unsupported_rounds_are_explicit(source,reason):
    with pytest.raises(AnalysisError,match=reason):
        compile_round(source)


def test_random_initial_state_objective_and_no_prefix_discount():
    cfg,kernel=compile_round('x := Uniform(1,2); while x > 1 do x := 0.5*x od; refute true;')
    problem=make_symbolic_round_problem(cfg,kernel,1,sp.Rational(3,4))
    coefficient0,coefficient1=map(sp.Symbol,problem.decisions)
    assert problem.objective==coefficient0+sp.Rational(3,2)*coefficient1


def test_raw_contraction_does_not_normalize_on_closed_exit_region():
    cfg,kernel=compile_round('x := 2; {x >= 0} while x > 1 do {x >= 0} x := 0.5*x od; refute true;')
    problem=make_symbolic_round_problem(cfg,kernel,1,sp.Rational(1,2))
    a,b=map(sp.Symbol,problem.decisions)
    vals={a:0,b:1}; x=sp.Symbol('x')
    for o in problem.obligations:
        for v in (sp.Rational(1,2),1,2,10):
            if holds(o.domain,{x:v}):
                assert o.conclusion.subs(vals).subs(x,v)>=0
