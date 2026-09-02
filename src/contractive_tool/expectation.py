from __future__ import annotations

from dataclasses import dataclass

import sympy as sp

from contractive_tool.algebra import Polynomial, PolynomialService
from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.errors import AnalysisError
from contractive_tool.ir.cfg import Branch, TransitionGroup
from contractive_tool.probability.distributions import (
    IndependentRandomModel,
    distribution_from_ast,
)


@dataclass(frozen=True)
class ExpectationTrace:
    destination_function: Polynomial
    after_simultaneous_substitution: Polynomial
    after_random_expectation: Polynomial
    branch_probability: Polynomial
    weighted_expectation: Polynomial

    def to_data(self) -> dict[str, object]:
        return {
            "destination_function": str(self.destination_function),
            "after_simultaneous_substitution": str(self.after_simultaneous_substitution),
            "after_random_expectation": str(self.after_random_expectation),
            "branch_probability": str(self.branch_probability),
            "weighted_expectation": str(self.weighted_expectation),
        }


class ExpectationEngine:
    def __init__(self, polynomial_service: PolynomialService | None = None):
        self.polynomials = polynomial_service or PolynomialService()

    def _model_for_branch(
        self, branch: Branch, random_model: IndependentRandomModel | None
    ) -> IndependentRandomModel:
        distributions = dict(random_model.distributions) if random_model else {}
        for sample in branch.update.samples:
            distributions[sample.symbol] = distribution_from_ast(sample.distribution)
        provider = random_model.joint_provider if random_model else None
        return IndependentRandomModel(distributions, provider)

    def _eliminate_random(
        self, poly: Polynomial, random_model: IndependentRandomModel
    ) -> Polynomial:
        random_symbols = tuple(sp.Symbol(name) for name in random_model.symbols)
        if not random_symbols:
            return poly
        try:
            expanded = sp.Poly(poly.expression, *random_symbols)
        except sp.PolynomialError as error:
            raise AnalysisError("pre-expectation requires polynomial random dependence") from error
        result = sp.Integer(0)
        for exponents, coefficient in expanded.terms():
            powers = {
                symbol.name: exponent
                for symbol, exponent in zip(random_symbols, exponents)
                if exponent
            }
            result += coefficient * random_model.moment(powers)
        return self.polynomials.normalize(result)

    def trace_branch(
        self,
        function: Polynomial,
        branch: Branch,
        random_model: IndependentRandomModel | None = None,
    ) -> ExpectationTrace:
        substituted = self.polynomials.substitute(function, branch.update)
        model = self._model_for_branch(branch, random_model)
        expected = self._eliminate_random(substituted, model)
        probability = self.polynomials.normalize(arithmetic_to_symbolic(branch.probability))
        weighted = self.polynomials.normalize(probability.expression * expected.expression)
        return ExpectationTrace(function, substituted, expected, probability, weighted)

    def branch_expectation(
        self,
        function: Polynomial,
        branch: Branch,
        random_model: IndependentRandomModel | None = None,
    ) -> Polynomial:
        return self.trace_branch(function, branch, random_model).weighted_expectation

    def transition_expectation(
        self,
        destination_functions: dict[str, Polynomial],
        group: TransitionGroup,
        random_model: IndependentRandomModel | None = None,
    ) -> tuple[Polynomial, tuple[ExpectationTrace, ...]]:
        traces = tuple(
            self.trace_branch(destination_functions[branch.destination], branch, random_model)
            for branch in group.branches
        )
        return self.polynomials.add(*(trace.weighted_expectation for trace in traces)), traces
