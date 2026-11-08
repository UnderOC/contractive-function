from types import SimpleNamespace

import pytest
import sympy as sp

from contractive_tool.analysis.goals import make_problem
from contractive_tool.analysis.rounds import make_round_problem, prepare_round_kernel
from contractive_tool.analysis.semantics import prepare_program
from contractive_tool.analysis.symbolic_rounds import make_symbolic_round_problem, prepare_symbolic_round_kernel
from contractive_tool.analysis.symbolic_workflow import _template
from contractive_tool.analysis_pipeline import selected_bound
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.parser import parse_text
from contractive_tool.frontend.semantic import check_program


def test_tail_restriction_keeps_update_dependencies_in_both_proof_rules():
    cfg = build_cfg(check_program(parse_text(
        'x := 1; y := 0; while x > 0 do x := y; y := y+1 od; refute true;')))
    evidence = prepare_program(cfg)
    kernel = prepare_symbolic_round_kernel(cfg, evidence)
    direct = make_problem(cfg, evidence, 2, sp.Rational(9,10), template_variables=('x',))
    symbolic = make_symbolic_round_problem(cfg, kernel, 2, sp.Rational(9,10), template_variables=('x',))
    for problem in (direct, symbolic):
        assert all(sp.Symbol('y') not in e.free_symbols for e in problem.expressions.values())
        dependent = [o for o in problem.obligations if sp.Symbol('y') in o.conclusion.free_symbols]
        assert dependent and all(sp.Symbol('y') in o.domain.variables for o in dependent)
    bound = selected_bound({'bound_exact':'2','bound_numeric':2}, direct, cfg)
    assert 'termination_consequence' not in bound  # late bad exit does not establish termination
    with pytest.raises(AnalysisError, match='distinct program variables'):
        make_symbolic_round_problem(cfg, kernel, 2, sp.Rational(9,10), template_variables=('missing',))


def test_boolean_restriction_preserves_full_state_kernel():
    cfg = build_cfg(check_program(parse_text(
        'x := 0; y := 0; while x = 0 do x := 1; y := 1-y od; refute true;')))
    kernel = prepare_round_kernel(cfg, prepare_program(cfg))
    full = make_round_problem(cfg, kernel, 1, sp.Rational(9,10))
    restricted = make_round_problem(cfg, kernel, 1, sp.Rational(9,10), template_variables=('x',))
    assert len(restricted.decisions) == 2 and len(full.decisions) == 3
    assert [o.id for o in full.obligations] == [o.id for o in restricted.obligations]
    assert full.context['clock'] == restricted.context['clock']


def test_cauchy_templates_respect_selection_with_and_without_seed():
    x, y = sp.symbols('x y')
    round_ = SimpleNamespace(variables=(x,y), law=SimpleNamespace(symbols=()))
    for seed in (None, 1+x+x**2):
        template = _template(round_, seed, 2, {}, 20, ('x',))
        assert x in template.expression.free_symbols and y not in template.expression.free_symbols
    config = {'template': {'expression':'a*y', 'coefficients':['a']}}
    with pytest.raises(AnalysisError, match='excluded tail variable'):
        _template(round_, None, 2, config, 20, ('x',))
    with pytest.raises(AnalysisError, match='excluded tail variable'):
        _template(round_, x+y, 2, {}, 20, ('x',))
