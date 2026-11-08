from collections import defaultdict
from fractions import Fraction
from itertools import product
from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.analysis.cauchy import CauchyOptions, EtaTemplate, build_fixed_model, build_template_model
from contractive_tool.analysis.reciprocal import ReciprocalOptions, build_denominator_model, build_moment_model
from contractive_tool.errors import AnalysisError
from contractive_examples.pp_semantics import Program

PROJECT = Path(__file__).resolve().parents[2]


def distributions(round_, state):
    values = {sp.Symbol(k): sp.Rational(v) for k, v in state.items()}
    found = []
    for piece in round_.pieces:
        if not (all(g.subs(values) >= 0 for g in piece.domain.generators)
                and all(g.subs(values) == 0 for g in piece.domain.equalities)
                and all(g.subs(values) > 0 for g in piece.guard.strict)):
            continue
        outcomes = defaultdict(lambda: sp.Integer(0))
        for atom, probability in round_.law.atoms:
            sub = {**values, **dict(zip(round_.law.symbols, atom))}
            outcomes[tuple(piece.update[v].subs(sub, simultaneous=True) for v in round_.variables)] += probability
        assert sum(outcomes.values()) == 1
        found.append(dict(outcomes))
    return found


@pytest.mark.parametrize('name,count,atoms', [
    ('Q1_biased_noisy_two_actions', 2, 4), ('Q3_three_action_max', 5, 3)])
def test_qlearning_distributions_match_independent_interpreter(name, count, atoms):
    source = PROJECT/'contractive_examples/qlearning'/f'{name}.pp'
    round_ = prepare_random_round(source)
    program = Program(source)
    assert len(round_.pieces) == count and len(round_.law.atoms) == atoms
    checked = overlaps = 0
    # Include all-equal states, maximum ties, and both sides of the guards.
    for coordinates in product((Fraction(0), Fraction(1, 2), Fraction(1)), repeat=len(round_.variables)):
        state = dict(zip(map(str, round_.variables), coordinates))
        if not program.active(state):
            continue
        expected = defaultdict(lambda: sp.Integer(0))
        for probability, successor in program.successors(state):
            expected[tuple(sp.Rational(successor[str(v)]) for v in round_.variables)] += sp.Rational(probability)
        actual = distributions(round_, state)
        assert actual and all(a == dict(expected) for a in actual)
        checked += 1
        overlaps += len(actual) > 1
    assert checked > 5
    if name.startswith('Q3'):
        assert overlaps  # Overlapping covers must not add probability twice.
    eta = 1+sum(v**2 for v in round_.variables)
    for piece, (_, numerator, coefficients, basis) in zip(round_.pieces, round_.decompositions(eta)):
        assert sp.expand(numerator-sum(a*b for a,b in zip(coefficients,basis))) == 0
        for atom, _ in round_.law.atoms:
            sub = dict(zip(round_.law.symbols, atom))
            assert sp.expand((numerator-eta.subs(piece.update, simultaneous=True)).subs(sub)) == 0
    with pytest.raises(AnalysisError, match='region-wise'):
        round_.decompose(eta)


def test_random_then_conditional_pullback_and_raw_exit(tmp_path):
    source = tmp_path/'random_guard.pp'
    source.write_text('x := 2; while x >= 1 do '
        'if prob(0.5) then x := x+1 else x := x-1 fi; '
        'if x >= 2 then x := 0.5*x else x := 0 fi od; refute true;')
    round_ = prepare_random_round(source)
    for x, expected in ((1, {(sp.Integer(1),): sp.Rational(1,2), (sp.Integer(0),): sp.Rational(1,2)}),
                        (2, {(sp.Rational(3,2),): sp.Rational(1,2), (sp.Integer(0),): sp.Rational(1,2)}),
                        (3, {(sp.Integer(2),): sp.Rational(1,2), (sp.Integer(1),): sp.Rational(1,2)})):
        actual = distributions(round_, {'x': x})
        assert actual and all(a == expected for a in actual)
    with pytest.raises(AnalysisError, match='budget'):
        prepare_random_round(source, max_cases=1)


def test_constant_false_guard_is_removed_before_closure(tmp_path):
    source = tmp_path/'boundary.pp'
    source.write_text('x := 2; while x >= 1 do x := 0; '
                      'if x > 0 then x := 99 else x := -1 fi od; refute true;')
    round_ = prepare_random_round(source)
    assert distributions(round_, {'x': 2}) == [{(sp.Integer(-1),): sp.Integer(1)}]


def test_common_cdf_law_handles_different_regional_probabilities(tmp_path):
    source = tmp_path/'different_laws.pp'
    source.write_text('x := 2; while x >= 1 do if x > 2 then '
        'if prob(0.5) then x := 0 else x := 1 fi else '
        'if prob(0.25) then x := 2 else x := 3 fi fi od; refute true;')
    round_ = prepare_random_round(source)
    assert len(round_.law.atoms) == 3
    assert distributions(round_, {'x': 3}) == [{(sp.Integer(0),): sp.Rational(1,2), (sp.Integer(1),): sp.Rational(1,2)}]
    assert distributions(round_, {'x': 2}) == [{(sp.Integer(2),): sp.Rational(1,4), (sp.Integer(3),): sp.Rational(3,4)}]


def test_shared_coefficients_and_region_obligations(tmp_path):
    source = tmp_path/'models.pp'
    source.write_text('x := 1; while x < 4 invariant x >= 1 do {x >= 1} '
        'if x < 2 then {x >= 1} x := 2*x else {x >= 1} x := 3*x fi od; refute true;')
    round_ = prepare_random_round(source)
    x,a,b = sp.symbols('x a b')
    template = EtaTemplate(a*x+b, (a,b))
    fixed, _ = build_fixed_model(round_, x)
    joint, _ = build_template_model(round_, template, sp.Rational(1,2))
    reciprocal, _, _ = build_denominator_model(round_, template, ReciprocalOptions(), 2, 1, 9)
    assert len(joint.coverage['matrix']) == len(reciprocal.coverage['matrix']) == len(round_.pieces)
    assert sum('_norm_' in s['id'] for s in fixed.coverage['scalar']) == len(round_.pieces)
    for model in (joint, reciprocal):
        decisions = tuple(map(sp.Symbol, model.decisions))
        assert all(sp.Poly(e, *decisions).total_degree() <= 1 for e in model.equalities)
    for kind in ('c', 'r0', 'D'):
        model, _ = build_moment_model(round_, x, kind, ReciprocalOptions(), c=2)
        assert len(model.coverage['scalar']) >= len(round_.pieces)


@pytest.mark.parametrize('mode', ['fixed', 'template'])
def test_construction_timeout_is_unknown_and_never_solved(tmp_path, monkeypatch, mode):
    import contractive_tool.analysis.cauchy as module
    source = tmp_path/'budget.pp'
    source.write_text('x := 2; while x >= 1 do '
                      'if x > 2 then x := 0.5*x else x := 0.25*x fi od; refute true;')
    round_ = prepare_random_round(source)
    calls = []
    def expire(deadline):
        assert deadline is not None
        calls.append(1)
        if len(calls) == 3:
            raise module.StateModelBudgetExceeded('injected construction timeout')
    monkeypatch.setattr(module, '_check_state_budget', expire)
    monkeypatch.setattr(module, '_solve', lambda *args: pytest.fail('Incomplete model reached solver'))
    x,a = sp.symbols('x a')
    result = (module.search_fixed_eta(round_, x) if mode == 'fixed' else
              module.search_template_eta(round_, EtaTemplate(a*x,(a,)), t_values=('1/2',)))
    assert result['status'] == 'no_certificate_found' and not result['candidates']
    assert result['stop_reason'] == 'state_model_time_budget'
    assert result['attempts'][0]['status'] == 'unknown'


def test_matrix_lowering_and_serialization_observe_budget():
    from contractive_tool.positivity.ir import BasicSet, ConicModel
    from contractive_tool.positivity.matrix_sos import lower_matrix_sos
    from contractive_tool.positivity.base import EncodingLimits
    x = sp.Symbol('x')
    model = ConicModel([], sp.Integer(0))
    calls = []
    def budget():
        calls.append(1)
        if len(calls) == 2:
            raise TimeoutError('budget')
    with pytest.raises(TimeoutError):
        lower_matrix_sos(BasicSet((x,), (x,)), sp.eye(2), model, 'test', 0,
                         EncodingLimits(), [x], check_budget=budget)
    assert len(model.psd_blocks) == 1
    calls.clear()
    model.equalities.append(sp.Symbol(model.decisions[0])-1)
    with pytest.raises(TimeoutError):
        model.to_data(check_budget=budget)
    assert model.to_data()['model_kind'] == 'sdp'
