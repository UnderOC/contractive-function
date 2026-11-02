import sympy as sp
import pytest

from contractive_tool.analysis.assertion import make_assertion_problem, evaluate_bound
from contractive_tool.analysis.semantics import prepare_program
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.frontend.parser import parse_text
from contractive_tool.frontend.semantic import check_program
from contractive_tool.errors import AnalysisError


def problem(source, c='9/10', margin='1/100'):
    cfg = build_cfg(check_program(parse_text(source)))
    evidence = prepare_program(cfg)
    return cfg, evidence, make_assertion_problem(cfg, evidence, 1, c, margin=margin)


def test_raw_normal_terminal_is_included_in_full_moment_and_no_terminal_drift():
    cfg, evidence, p = problem('x := 0; if prob(0.25) then refute true else skip fi;')
    assert p.expressions[cfg.failure_terminal] == 1
    assert p.expressions[cfg.normal_terminal] == sp.Rational(1, 100)
    skip = next(loc for loc in cfg.locations.values() if loc.kind == 'skip')
    drift = next(o for o in p.obligations if o.origin['location'] == skip.id and 'full_first_moment' in o.tags)
    assert sp.expand(drift.conclusion-(sp.Rational(9,10)*p.expressions[skip.id]-sp.Rational(1,100))) == 0
    assert all(o.origin['location'] not in (cfg.failure_terminal,cfg.normal_terminal) for o in p.obligations)
    symbols = tuple(map(sp.Symbol, p.decisions))
    assert all(sp.Poly(o.conclusion, *symbols).total_degree() <= 1 for o in p.obligations)
    assert p.objective == p.expressions[evidence.start].subs(evidence.initial, simultaneous=True)
    assert p.context['prefix_steps'] == 1


def test_random_initialization_integrates_raw_potential_without_prefix_multiplier():
    cfg, evidence, p = problem('x := Bernoulli(0.25); refute x = 1;')
    expr = p.expressions[evidence.start]
    assert sp.expand(p.objective-(sp.Rational(3,4)*expr.subs('x',0)+sp.Rational(1,4)*expr.subs('x',1))) == 0


@pytest.mark.parametrize('c,margin', [('1','1/100'),('0','1/100'),('2','1/100'),('9/10','0'),('9/10','2')])
def test_strict_parameter_domain(c, margin):
    with pytest.raises(AnalysisError):
        problem('x := 0; refute true;', c, margin)


def test_eventual_probability_never_decays_and_late_event_has_n_plus_one():
    bound = {'A_exact':'1/2', 'c':'1/2', 'prefix_steps':2}
    assert evaluate_bound(bound, 'eventual', 100)['upper_bound_exact'] == '1/2'
    assert evaluate_bound(bound, 'late_failure', 0)['upper_bound_exact'] == '1/4'
    assert evaluate_bound(bound, 'point_failure', 2)['upper_bound_exact'] == '1/8'
    assert evaluate_bound(bound, 'late_failure', 2, 'program_entry')['upper_bound_exact'] == '1/4'
    assert evaluate_bound(bound, 'late_failure', 0, 'program_entry')['upper_bound_exact'] == '1/2'
    assert evaluate_bound(bound, 'point_failure', 1, 'program_entry')['upper_bound_exact'] == '0'


def test_intermediate_assertion_has_its_own_raw_transition():
    cfg, _, p = problem('x := 0; while x < 1 do refute x = 0; x := x + 1 od;')
    refute = next(l.id for l in cfg.locations.values() if l.kind == 'refute')
    certified = {o.origin['transition'] for o in p.obligations
                 if o.origin['location'] == refute and 'full_first_moment' in o.tags}
    assert certified == {g.id for g in cfg.outgoing(refute)}
