import sympy as sp
from contractive_tool.analysis.goals import make_problem
from contractive_tool.analysis.semantics import prepare_program, prove_nonnegative
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.frontend.parser import parse_text
from contractive_tool.frontend.semantic import check_program
from contractive_tool.positivity.ir import BasicSet, Implication
from contractive_tool.positivity.registry import StrategyRegistry
from contractive_tool.positivity.selector import build_plan


def test_source_names_cannot_alias_synthesis_symbols():
    cfg=build_cfg(check_program(parse_text('v_L_refute_1_0 := 1; refute true;')))
    problem=make_problem(cfg,prepare_program(cfg),2,sp.Rational(1,2))
    assert not set(problem.decisions)&set(cfg.symbols.program_variables)
    x=sp.Symbol('o0_s0_q_0_0')
    obligation=Implication('id',BasicSet((x,)),x*x,{},('test',))
    model,_=build_plan([obligation],[],sp.Integer(0),StrategyRegistry(),'putinar')
    assert str(x) not in model.decisions
    x=sp.Symbol('_f0')
    assert prove_nonnegative(BasicSet((x,),(x,)),x) is not None
