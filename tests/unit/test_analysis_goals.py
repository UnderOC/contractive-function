from __future__ import annotations

from pathlib import Path

import pytest
import sympy as sp

from contractive_tool.analysis.goals import (
    AssertionViolationGoal,
    AssertionViolationGoalSpec,
    TailBoundGoal,
    TailBoundGoalSpec,
)
from contractive_tool.analysis.ir import InitialConfig
from contractive_tool.analysis.templates import PolynomialTemplateFactory, total_degree_exponents
from contractive_tool.analysis_pipeline import infer_iid_multiplicative_gains, parse_event
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.parser import parse_file, parse_text
from contractive_tool.frontend.semantic import check_program


PROJECT = Path(__file__).resolve().parents[2]


def graph(source: str):
    return build_cfg(check_program(parse_text(source, "goal.pp")))


def sample_graph(name: str):
    return build_cfg(check_program(parse_file(PROJECT / name)))


def test_total_degree_basis_and_tail_k1_obligations_are_affine() -> None:
    cfg = sample_graph("kelly_simple.pp")
    template = PolynomialTemplateFactory().instantiate(cfg, degree=1, prefix="eta")
    assert len(total_degree_exponents(2, 1)) == 3
    event = parse_event("wealth <= 0.6", cfg)
    spec = TailBoundGoalSpec(
        "tail",
        event,
        3,
        "at_horizon",
        InitialConfig(cfg.initial_location, {"wealth": sp.Integer(1), "round": sp.Integer(0)}),
        sp.Integer(1),
        sp.Rational(99, 100),
    )
    model = TailBoundGoal().polynomial_obligations(
        cfg, spec, template, positivity_margin=sp.Rational(1, 10**6)
    )
    assert model.required_tags <= model.actual_tags
    assert {"contraction", "tail_normalization", "eta_positive"} <= model.actual_tags
    assert all(
        TailBoundGoal().polynomials.is_affine_in(
            obligation.relation.normalized, model.decision_variables
        )
        for obligation in model.obligations
    )
    contraction = next(item for item in model.obligations if "contraction" in item.tags)
    assert contraction.debug is not None and "branches" in contraction.debug


def test_kelly_fixed_lambda_builds_exact_scalar_moment_and_horizon_bound() -> None:
    cfg = sample_graph("kelly_simple.pp")
    loop = next(item.id for item in cfg.locations.values() if item.kind == "while")
    event = parse_event("wealth <= 0.6", cfg)
    spec = TailBoundGoalSpec(
        "kelly",
        event,
        3,
        "at_horizon",
        InitialConfig(loop, {"wealth": sp.Integer(1), "round": sp.Integer(0)}),
    )
    gains = infer_iid_multiplicative_gains(cfg, "wealth")
    model = TailBoundGoal().kelly_scalar_model(
        cfg,
        spec,
        base_variable="wealth",
        lambda_value=sp.Rational(1, 2),
        gains=gains,
        threshold=sp.Rational(3, 5),
    )
    expected = sp.Rational(3, 5) / sp.sqrt(sp.Rational(6, 5)) + sp.Rational(2, 5) / sp.sqrt(sp.Rational(4, 5))
    assert sp.simplify(model.constraints[0].left - expected) == 0
    assert sp.simplify(model.objective.expression - expected**3 * sp.sqrt(sp.Rational(3, 5))) == 0
    assert model.to_data()["arithmetic"] == "exact symbolic"


def test_tail_rejects_by_horizon_without_cfg_augmentation() -> None:
    cfg = graph("x := 1;")
    event = parse_event("x <= 0", cfg)
    spec = TailBoundGoalSpec(
        "bad",
        event,
        2,
        "by_horizon",
        InitialConfig(cfg.initial_location, {"x": sp.Integer(1)}),
    )
    with pytest.raises(AnalysisError, match="CFG augmentation"):
        TailBoundGoal().validate(cfg, spec)


def test_assertion_direct_and_fixed_factorized_obligations_have_boundaries() -> None:
    cfg = sample_graph("uniform_multiplicative.pp")
    ordinary = set(cfg.locations) - {cfg.normal_terminal, cfg.failure_terminal}
    spec = AssertionViolationGoalSpec(
        "assertion",
        InitialConfig(cfg.initial_location, {"x": sp.Integer(1), "r": sp.Integer(0)}),
        frozenset({cfg.failure_terminal}),
        cfg.normal_terminal,
    )
    template = PolynomialTemplateFactory().instantiate(
        cfg, degree=2, prefix="theta", locations=sorted(ordinary)
    )
    direct = AssertionViolationGoal().obligations(cfg, spec, template)
    assert direct.required_tags <= direct.actual_tags
    failure = next(item for item in direct.obligations if "failure_boundary" in item.tags)
    normal = next(item for item in direct.obligations if "normal_boundary" in item.tags)
    assert str(failure.relation.left) == "1" and str(failure.relation.right) == "1"
    assert normal.relation.relation == "=" and str(normal.relation.left) == "0"
    sample_prefixed = next(
        item
        for item in direct.obligations
        if "prefixed_point" in item.tags
        and item.debug
        and any("__sample" in branch["after_simultaneous_substitution"] for branch in item.debug["branches"])
    )
    assert all("__sample" not in branch["after_random_expectation"] for branch in sample_prefixed.debug["branches"])

    factor_template = PolynomialTemplateFactory().instantiate(
        cfg, degree=1, prefix="eta", locations=sorted(ordinary)
    )
    factorized = AssertionViolationGoal().obligations(
        cfg,
        spec,
        factor_template,
        factorization_q={location: sp.Integer(2) for location in ordinary},
        k=1,
    )
    assert factorized.required_tags <= factorized.actual_tags
    with pytest.raises(AnalysisError, match="k=1"):
        AssertionViolationGoal().obligations(cfg, spec, factor_template, k=2)


def test_assertion_goal_requires_failure_location() -> None:
    cfg = graph("x := 1;")
    spec = AssertionViolationGoalSpec(
        "missing",
        InitialConfig(cfg.initial_location, {"x": sp.Integer(1)}),
        frozenset(),
        cfg.normal_terminal,
    )
    with pytest.raises(AnalysisError, match="requires failure"):
        AssertionViolationGoal().validate(cfg, spec)
