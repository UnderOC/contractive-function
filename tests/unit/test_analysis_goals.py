import pytest
import sympy as sp
from contractive_tool.analysis.goals import make_problem
from contractive_tool.analysis.degree_policy import DegreePolicy
from contractive_tool.analysis.certificate_families import FractionalPowerFamily
from contractive_tool.analysis.semantics import prepare_program
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.parser import parse_text
from contractive_tool.frontend.semantic import check_program


def graph(source):
    return build_cfg(check_program(parse_text(source)))


def test_direct_degree_prefix_clock_and_affine_coefficients():
    cfg=graph('x := 4; {x >= 0} while x >= 1 do {x >= 1} x := x * 0.5 od; refute true;')
    evidence=prepare_program(cfg)
    c=sp.Rational(9,10)
    problem=make_problem(cfg,evidence,2,c)
    assert len(evidence.prefix)==1
    assert problem.objective == problem.expressions[evidence.start].subs({'x':4})/c
    unknowns=[sp.Symbol(n) for n in problem.decisions]
    assert all(sp.Poly(o.conclusion,*unknowns).total_degree()<=1 for o in problem.obligations)
    assert problem.expressions[cfg.normal_terminal]==0
    assert problem.expressions[cfg.failure_terminal]==1
    assert all(cfg.locations[o.origin['location']].kind not in {'normal_terminal','failure_terminal'}
               for o in problem.obligations)
    assertion=make_problem(cfg,evidence,2,c,'assertion_violation')
    assert assertion.objective == assertion.expressions[evidence.start].subs({'x':4})
    assert any('prefixed_point' in o.tags for o in assertion.obligations)


def test_degree_schedule_and_fractional_extension():
    assert list(DegreePolicy().degrees())==[2,3,4,5,6]
    assert list(DegreePolicy(2,6,2).degrees())==[2,4,6]
    with pytest.raises(AnalysisError): list(DegreePolicy(3,2).degrees())
    with pytest.raises(AnalysisError,match='fractional'): FractionalPowerFamily().instantiate()


def test_invalid_invariant_is_rejected_before_synthesis():
    cfg=graph('x := 1; {x >= 0} while x >= 0 do {x >= 0} x := x - 1 od; refute true;')
    with pytest.raises(AnalysisError,match='inductive invariant'):
        prepare_program(cfg)


def test_false_initial_invariant_and_missing_initial_value_rejected():
    with pytest.raises(AnalysisError,match='Initial control'):
        prepare_program(graph('x := 1; {x = 0} while x > 0 do skip od; refute true;'))
    with pytest.raises(AnalysisError,match='initialize'):
        prepare_program(graph('while x > 0 do x := x - 1 od; refute true;'))


def test_nonterminating_loop_is_not_assumed_to_exit():
    cfg=graph('x := 0; while true do skip od; refute true;')
    evidence=prepare_program(cfg)
    problem=make_problem(cfg,evidence,2,sp.Rational(1,2))
    # No termination premise and no finite-horizon domain enumeration.
    assert any('contraction' in o.tags for o in problem.obligations)
    assert all(not o.domain.generators for o in problem.obligations)
