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
            and all(e.subs(values)==0 for e in domain.equalities)
            and all(g.subs(values)>0 for g in getattr(domain,'strict',())))


def test_rcd_symbolic_expectation_and_nonzero_exit_boundary():
    cfg,kernel=compile_round((PROJECT/'RCD_example.pp').read_text())
    x,y=sp.symbols('x y')
    f=(x*x+x*y+y*y)/2
    cases=kernel.partitioned_preconditions(f)
    assert len(cases)==4
    assert kernel.expectation_mode=='exact_piecewise_survival'
    assert {p for _,p in cases}=={sp.Integer(0),sp.Rational(3,16)*x*x,
        sp.Rational(3,16)*y*y,sp.Rational(3,16)*(x*x+y*y).expand()}
    # Check exact indicators, including landing exactly on the exit boundary.
    for state in ({x:-sp.Rational(1,2),y:1},
                  {x:-sp.Rational(1,32),y:sp.Rational(1,16)},
                  {x:-sp.Rational(1,40),y:sp.Rational(1,20)},
                  {x:sp.Rational(1,40),y:sp.Rational(1,40)}):
        state={key:sp.Rational(value) for key,value in state.items()}
        expected=0
        for updated in ({x:-state[y]/2,y:state[y]}, {x:state[x],y:-state[x]/2}):
            after=f.subs(updated)
            if after>sp.Rational(3,8192):
                expected+=after/2
        matches=[p.subs(state) for domain,p in cases if holds(domain,state)]
        assert matches and all(v==expected for v in matches)
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
    assert kernel.to_data()['expectation_mode']=='raw_round_moments'


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


def test_survival_contraction_does_not_normalize_on_closed_exit_region():
    cfg,kernel=compile_round('x := 2; {x >= 0} while x > 1 do {x >= 0} x := 0.5*x od; refute true;')
    problem=make_symbolic_round_problem(cfg,kernel,1,sp.Rational(1,2))
    a,b=map(sp.Symbol,problem.decisions)
    vals={a:0,b:1}; x=sp.Symbol('x')
    for o in problem.obligations:
        for v in (sp.Rational(1,2),1,2,10):
            if holds(o.domain,{x:v}):
                assert o.conclusion.subs(vals).subs(x,v)>=0


@pytest.mark.parametrize('guard,after,expected',[
    ('x > 1','1',0), ('x >= 1','1',1),
    ('x < 3','3',0), ('x <= 3','3',1),
    ('x != 1','1',0), ('x = 2','2',1),
    ('x > 1 and x < 3','1',0), ('x > 1 or x < 0','0',0),
])
def test_boundary_is_classified_before_closing_domains(guard,after,expected):
    _,kernel=compile_round(f'x := 2; while {guard} do x := {after} od; refute true;')
    cases=kernel.partitioned_preconditions(sp.Integer(1))
    matches=[p for d,p in cases if holds(d,{sp.Symbol('x'):2})]
    assert matches and all(p==expected for p in matches)


def test_two_branch_survival_partition_matches_direct_execution():
    _,kernel=compile_round('''x := 4; while x > 1 do
      if prob(0.5) then x := 0.5*x else x := 0.25*x fi
    od; refute true;''')
    x=sp.Symbol('x'); eta=1+x+x*x
    cases=kernel.partitioned_preconditions(eta)
    for v in (sp.Rational(3,2),2,3,4,5,8):
        v=sp.Rational(v)
        expected=sum((eta.subs(x,target)/2 if target>1 else 0)
                     for target in (v/2,sp.Rational(v,4)))
        matches=[p.subs(x,v) for d,p in cases if holds(d,{x:v})]
        assert matches and all(p==expected for p in matches)


def test_guard_pullback_through_multiple_assignments_and_state_probability():
    _,kernel=compile_round('''x := 2; p := 0.25;
      {0 <= p and p <= 1} while x > 1 do
        {0 <= p and p <= 1} if prob(p) then
          {0 <= p and p <= 1} x := x + 2;
          {0 <= p and p <= 1} x := 0.5*x
        else
          {0 <= p and p <= 1} x := x - 1
        fi
      od; refute true;''')
    x,p=sp.symbols('x p')
    cases=kernel.partitioned_preconditions(1+x*x)
    for v in (sp.Rational(3,2),2,3,4):
        v=sp.Rational(v)
        expected=sum(prob*(1+target*target) if target>1 else 0
                     for prob,target in ((sp.Rational(1,4),(v+2)/2),(sp.Rational(3,4),v-1)))
        vals={x:v,p:sp.Rational(1,4)}
        matches=[expr.subs(vals) for d,expr in cases if holds(d,vals)]
        assert matches and all(expr==expected for expr in matches)


def test_piecewise_case_budget_is_explicit():
    cfg=build_cfg(check_program(parse_text('''x := 4; while x > 1 do
        if prob(0.5) then x := 0.5*x else x := 0.25*x fi od; refute true;''')))
    with pytest.raises(AnalysisError,match='case budget'):
        prepare_symbolic_round_kernel(cfg,prepare_program(cfg),max_cases=2)


def test_continuous_sampling_keeps_labeled_raw_rule():
    _,kernel=compile_round('x := 2; while x > 1 do x := Uniform(0,2) od; refute true;')
    assert kernel.expectation_mode=='raw_round_moments'
    cases=kernel.preconditions(sp.Symbol('x'))
    assert len(cases)==1 and cases[0][1]==1
