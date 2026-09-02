from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol

import sympy as sp

from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.ast import DistributionExpr


class Distribution(Protocol):
    def validate(self) -> None: ...

    def raw_moment(self, order: int) -> sp.Expr: ...


class JointMomentProvider(Protocol):
    def moment(self, powers: Mapping[str, int]) -> sp.Expr: ...


def _validate_order(order: int) -> None:
    if not isinstance(order, int) or order < 0:
        raise AnalysisError(f"moment order must be a nonnegative integer, got {order!r}")


@dataclass(frozen=True)
class FiniteDiscreteDistribution:
    values: tuple[sp.Expr, ...]
    probabilities: tuple[sp.Expr, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", tuple(sp.sympify(item) for item in self.values))
        object.__setattr__(
            self, "probabilities", tuple(sp.sympify(item) for item in self.probabilities)
        )

    def validate(self) -> None:
        if not self.values or len(self.values) != len(self.probabilities):
            raise AnalysisError("finite discrete distribution needs equally-sized nonempty data")
        if sp.simplify(sum(self.probabilities, sp.Integer(0)) - 1) != 0:
            raise AnalysisError("finite discrete probabilities must sum exactly to one")
        for probability in self.probabilities:
            if probability.is_nonnegative is False:
                raise AnalysisError("finite discrete probabilities must be nonnegative")

    def raw_moment(self, order: int) -> sp.Expr:
        _validate_order(order)
        self.validate()
        return sp.simplify(
            sum(
                (probability * value**order for value, probability in zip(self.values, self.probabilities)),
                sp.Integer(0),
            )
        )


@dataclass(frozen=True)
class BernoulliDistribution:
    probability: sp.Expr

    def __post_init__(self) -> None:
        object.__setattr__(self, "probability", sp.sympify(self.probability))

    def validate(self) -> None:
        if self.probability.is_number is not True:
            raise AnalysisError("Bernoulli parameter must be a numeric constant")
        if self.probability < 0 or self.probability > 1:
            raise AnalysisError("Bernoulli probability must be in [0, 1]")

    def raw_moment(self, order: int) -> sp.Expr:
        _validate_order(order)
        self.validate()
        return sp.Integer(1) if order == 0 else self.probability


@dataclass(frozen=True)
class UniformDistribution:
    lower: sp.Expr
    upper: sp.Expr

    def __post_init__(self) -> None:
        object.__setattr__(self, "lower", sp.sympify(self.lower))
        object.__setattr__(self, "upper", sp.sympify(self.upper))

    def validate(self) -> None:
        if self.lower.is_number is not True or self.upper.is_number is not True:
            raise AnalysisError("Uniform parameters must be numeric constants")
        if self.lower >= self.upper:
            raise AnalysisError("Uniform requires lower < upper")

    def raw_moment(self, order: int) -> sp.Expr:
        _validate_order(order)
        self.validate()
        return sp.factor(
            (self.upper ** (order + 1) - self.lower ** (order + 1))
            / ((order + 1) * (self.upper - self.lower))
        )


@dataclass(frozen=True)
class NormalDistribution:
    mean: sp.Expr
    standard_deviation: sp.Expr

    def __post_init__(self) -> None:
        object.__setattr__(self, "mean", sp.sympify(self.mean))
        object.__setattr__(
            self, "standard_deviation", sp.sympify(self.standard_deviation)
        )

    def validate(self) -> None:
        if self.mean.is_number is not True or self.standard_deviation.is_number is not True:
            raise AnalysisError("Normal parameters must be numeric constants")
        if self.standard_deviation <= 0:
            raise AnalysisError("Normal requires a positive standard deviation")

    def raw_moment(self, order: int) -> sp.Expr:
        _validate_order(order)
        self.validate()
        result = sp.Integer(0)
        for pairs in range(order // 2 + 1):
            even_order = 2 * pairs
            central = sp.Integer(1) if pairs == 0 else sp.factorial2(even_order - 1)
            result += (
                sp.binomial(order, even_order)
                * self.mean ** (order - even_order)
                * self.standard_deviation**even_order
                * central
            )
        return sp.expand(result)


def distribution_from_ast(distribution: DistributionExpr) -> Distribution:
    arguments = tuple(arithmetic_to_symbolic(item) for item in distribution.arguments)
    if distribution.name == "Uniform":
        result: Distribution = UniformDistribution(*arguments)
    elif distribution.name == "Normal":
        result = NormalDistribution(*arguments)
    elif distribution.name == "Bernoulli":
        result = BernoulliDistribution(*arguments)
    else:
        raise AnalysisError(f"unsupported distribution '{distribution.name}'")
    result.validate()
    return result


@dataclass(frozen=True)
class IndependentRandomModel:
    distributions: Mapping[str, Distribution]
    joint_provider: JointMomentProvider | None = None

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(sorted(self.distributions))

    def moment(self, powers: Mapping[str, int]) -> sp.Expr:
        unknown = set(powers) - set(self.distributions)
        if unknown:
            raise AnalysisError(f"no distribution for random symbol(s): {', '.join(sorted(unknown))}")
        cleaned = {name: order for name, order in powers.items() if order}
        if self.joint_provider is not None and len(cleaned) > 1:
            return sp.simplify(self.joint_provider.moment(cleaned))
        result = sp.Integer(1)
        for name, order in cleaned.items():
            result *= self.distributions[name].raw_moment(order)
        return sp.simplify(result)
