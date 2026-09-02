from __future__ import annotations

import sympy as sp

from contractive_tool.algebra import PolynomialService
from contractive_tool.expectation import ExpectationEngine
from contractive_tool.frontend.ast import (
    Binary,
    BooleanConstant,
    DistributionExpr,
    Number,
    SourceSpan,
    Variable,
)
from contractive_tool.ir.cfg import Branch, RandomSample, TransitionGroup, Update
from contractive_tool.probability.distributions import (
    BernoulliDistribution,
    FiniteDiscreteDistribution,
    IndependentRandomModel,
    NormalDistribution,
    UniformDistribution,
)


SPAN = SourceSpan.synthetic("expectation.pp")


def number(value: str) -> Number:
    return Number(value, SPAN)


def test_polynomial_adapter_uses_exact_numbers_and_simultaneous_substitution() -> None:
    service = PolynomialService()
    source = service.normalize("x - y + 0.1")
    update = Update({"x": Variable("y", SPAN), "y": Variable("x", SPAN)})
    substituted = service.substitute(source, update)
    assert substituted.expression == -sp.Symbol("x") + sp.Symbol("y") + sp.Rational(1, 10)
    assert service.variables(substituted) == frozenset({"x", "y"})


def test_discrete_uniform_normal_and_bernoulli_raw_moments_are_exact() -> None:
    discrete = FiniteDiscreteDistribution((0, 2), (sp.Rational(1, 4), sp.Rational(3, 4)))
    assert [discrete.raw_moment(i) for i in range(3)] == [1, sp.Rational(3, 2), 3]
    uniform = UniformDistribution(0, 2)
    assert [uniform.raw_moment(i) for i in range(4)] == [1, 1, sp.Rational(4, 3), 2]
    normal = NormalDistribution(2, 3)
    assert [normal.raw_moment(i) for i in range(4)] == [1, 2, 13, 62]
    bernoulli = BernoulliDistribution(sp.Rational(2, 5))
    assert [bernoulli.raw_moment(i) for i in range(4)] == [1, sp.Rational(2, 5), sp.Rational(2, 5), sp.Rational(2, 5)]


def test_independent_joint_moment_multiplies_and_explicit_provider_overrides() -> None:
    independent = IndependentRandomModel(
        {"r": UniformDistribution(0, 2), "z": BernoulliDistribution(sp.Rational(1, 2))}
    )
    assert independent.moment({"r": 2, "z": 1}) == sp.Rational(2, 3)

    class CorrelatedProvider:
        def moment(self, powers):
            assert powers == {"r": 1, "z": 1}
            return sp.Rational(7, 10)

    correlated = IndependentRandomModel(independent.distributions, CorrelatedProvider())
    assert correlated.moment({"r": 1, "z": 1}) == sp.Rational(7, 10)


def test_pre_expectation_records_simultaneous_substitution_moment_and_weight() -> None:
    service = PolynomialService()
    engine = ExpectationEngine(service)
    distribution = DistributionExpr("Uniform", (number("0"), number("2")), SPAN)
    update = Update(
        {
            "x": Binary("*", Variable("x", SPAN), Variable("__sample_r", SPAN), SPAN),
            "y": Variable("x", SPAN),
        },
        (RandomSample("__sample_r", distribution),),
    )
    branch = Branch("dst", number("0.5"), update)
    trace = engine.trace_branch(service.normalize("x**2 + y"), branch)
    x, y, r = sp.symbols("x y __sample_r")
    assert trace.after_simultaneous_substitution.expression == r**2 * x**2 + x
    assert trace.after_random_expectation.expression == sp.Rational(4, 3) * x**2 + x
    assert trace.weighted_expectation.expression == sp.Rational(2, 3) * x**2 + x / 2
    assert "after_simultaneous_substitution" in trace.to_data()


def test_transition_expectation_sums_probability_branches() -> None:
    service = PolynomialService()
    engine = ExpectationEngine(service)
    group = TransitionGroup(
        "choice",
        "src",
        BooleanConstant(True, SPAN),
        (
            Branch("win", number("0.6"), Update({"x": number("2")})),
            Branch("loss", number("0.4"), Update({"x": number("-1")})),
        ),
        SPAN,
    )
    result, traces = engine.transition_expectation(
        {"win": service.normalize("x**2"), "loss": service.normalize("x**2")}, group
    )
    assert result.expression == sp.Rational(14, 5)
    assert len(traces) == 2
