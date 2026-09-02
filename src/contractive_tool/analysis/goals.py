from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import sympy as sp

from contractive_tool.algebra import Polynomial, PolynomialService
from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.analysis.ir import (
    ConstraintOrigin,
    InitialConfig,
    Objective,
    PolynomialObligationModel,
    PolynomialRelation,
    ProofObligation,
    ScalarMomentConstraint,
    ScalarMomentModel,
    SemialgebraicRegion,
)
from contractive_tool.analysis.templates import PolynomialTemplateInstance
from contractive_tool.errors import AnalysisError
from contractive_tool.expectation import ExpectationEngine
from contractive_tool.frontend.ast import Compare, Expr, Number, Variable, ast_to_data, format_expr
from contractive_tool.ir.cfg import ProgramCFG, TransitionGroup


def _origin(
    analysis_id: str,
    goal_kind: str,
    template_kind: str,
    cfg: ProgramCFG,
    *,
    location: str | None = None,
    group: TransitionGroup | None = None,
) -> ConstraintOrigin:
    span = group.origin if group else (cfg.locations[location].span if location else None)
    return ConstraintOrigin(
        analysis_id,
        goal_kind,
        location if location is not None else (group.source if group else None),
        group.id if group else None,
        template_kind,
        ast_to_data(span) if span is not None else None,
    )


def _domain(cfg: ProgramCFG, location: str, *extra: Expr) -> SemialgebraicRegion:
    predicates = [format_expr(cfg.locations[location].invariant)]
    predicates.extend(format_expr(item) for item in extra)
    return SemialgebraicRegion(tuple(predicates))


def _evaluate(poly: Polynomial, valuation: Mapping[str, sp.Expr]) -> sp.Expr:
    replacements = {sp.Symbol(name): value for name, value in valuation.items()}
    return sp.expand(poly.expression.subs(replacements, simultaneous=True))


@dataclass(frozen=True)
class TailBoundGoalSpec:
    analysis_id: str
    event: Expr
    horizon: int
    event_mode: str
    initial: InitialConfig
    normalization_scale: sp.Expr = sp.Integer(1)
    rho: sp.Expr = sp.Integer(1)
    locations: frozenset[str] | None = None


@dataclass(frozen=True)
class AssertionViolationGoalSpec:
    analysis_id: str
    initial: InitialConfig
    failure_locations: frozenset[str]
    normal_terminal: str
    reachability_mode: str = "eventual"
    horizon: int | None = None


class TailBoundGoal:
    kind = "tail_bound"

    def __init__(
        self,
        polynomial_service: PolynomialService | None = None,
        expectation_engine: ExpectationEngine | None = None,
    ):
        self.polynomials = polynomial_service or PolynomialService()
        self.expectation = expectation_engine or ExpectationEngine(self.polynomials)

    def validate(self, cfg: ProgramCFG, spec: TailBoundGoalSpec) -> None:
        if spec.horizon < 0:
            raise AnalysisError("tail-bound horizon must be nonnegative")
        if spec.event_mode != "at_horizon":
            raise AnalysisError(
                "stage 3A supports event_mode='at_horizon' only; by_horizon needs CFG augmentation"
            )
        if spec.initial.location not in cfg.locations:
            raise AnalysisError(f"unknown initial location '{spec.initial.location}'")
        if spec.normalization_scale.free_symbols or spec.normalization_scale <= 0:
            raise AnalysisError("tail normalization scale H must be positive")
        if spec.rho.free_symbols or spec.rho <= 0 or spec.rho > 1:
            raise AnalysisError("fixed contraction factor rho must be in (0, 1]")
        expected_variables = set(cfg.symbols.program_variables)
        supplied_variables = set(spec.initial.valuation)
        if supplied_variables != expected_variables:
            raise AnalysisError(
                "initial valuation must define exactly the program variables; "
                f"missing={sorted(expected_variables - supplied_variables)}, "
                f"unknown={sorted(supplied_variables - expected_variables)}"
            )
        unknown_locations = set(spec.locations or ()) - set(cfg.locations)
        if unknown_locations:
            raise AnalysisError(f"unknown tail event locations: {sorted(unknown_locations)}")

    def polynomial_obligations(
        self,
        cfg: ProgramCFG,
        spec: TailBoundGoalSpec,
        template: PolynomialTemplateInstance,
        *,
        positivity_margin: sp.Expr = sp.Integer(0),
    ) -> PolynomialObligationModel:
        self.validate(cfg, spec)
        if set(template.locations) != set(cfg.locations):
            raise AnalysisError("tail polynomial template must define eta at every CFG location")
        h = spec.normalization_scale
        certificate = {
            location: self.polynomials.normalize(template.expression_at(location).expression / h)
            for location in cfg.locations
        }
        obligations: list[ProofObligation] = []
        for location in cfg.locations:
            obligations.append(
                ProofObligation(
                    f"tail_eta_positive_{location}",
                    _domain(cfg, location),
                    PolynomialRelation(
                        template.expression_at(location),
                        ">=",
                        self.polynomials.normalize(positivity_margin),
                    ),
                    _origin(spec.analysis_id, self.kind, "polynomial_eta_k1", cfg, location=location),
                    frozenset({"eta_positive", "k=1"}),
                )
            )
        for group in cfg.transitions:
            pre, traces = self.expectation.transition_expectation(certificate, group)
            obligations.append(
                ProofObligation(
                    f"tail_contraction_{group.id}",
                    _domain(cfg, group.source, group.guard),
                    PolynomialRelation(
                        self.polynomials.scale(spec.rho, certificate[group.source]), ">=", pre
                    ),
                    _origin(spec.analysis_id, self.kind, "polynomial_eta_k1", cfg, group=group),
                    frozenset({"contraction", "at_horizon", "k=1"}),
                    {"branches": [trace.to_data() for trace in traces]},
                )
            )
        event_locations = spec.locations or frozenset(cfg.locations)
        for location in sorted(event_locations):
            obligations.append(
                ProofObligation(
                    f"tail_normalization_{location}",
                    _domain(cfg, location, spec.event),
                    PolynomialRelation(
                        certificate[location], ">=", self.polynomials.normalize(1)
                    ),
                    _origin(spec.analysis_id, self.kind, "polynomial_eta_k1", cfg, location=location),
                    frozenset({"tail_normalization", "at_horizon", "k=1"}),
                )
            )
        initial_value = _evaluate(certificate[spec.initial.location], spec.initial.valuation)
        objective = Objective(
            "minimize",
            sp.expand(spec.rho**spec.horizon * initial_value),
            f"rho^{spec.horizon} * C(initial), bounding Pr[event at horizon]",
        )
        model = PolynomialObligationModel(
            spec.analysis_id,
            self.kind,
            cfg.symbols.program_variables,
            template.decision_variables(),
            tuple(obligations),
            objective,
            frozenset({"contraction", "tail_normalization", "eta_positive"}),
        )
        if not model.required_tags <= model.actual_tags:
            raise AnalysisError("tail lowering lost a required obligation category")
        nonaffine = [
            item.id
            for item in model.obligations
            if not self.polynomials.is_affine_in(
                item.relation.normalized, model.decision_variables
            )
        ]
        if nonaffine:
            raise AnalysisError(f"tail obligations are non-affine in decisions: {nonaffine}")
        return model

    def kelly_scalar_model(
        self,
        cfg: ProgramCFG,
        spec: TailBoundGoalSpec,
        *,
        base_variable: str,
        lambda_value: sp.Expr,
        gains: tuple[tuple[sp.Expr, sp.Expr], ...],
        threshold: sp.Expr,
        rho: sp.Expr | None = None,
    ) -> ScalarMomentModel:
        self.validate(cfg, spec)
        if lambda_value.free_symbols or lambda_value <= 0:
            raise AnalysisError("Kelly lambda must be a fixed positive value")
        if threshold.free_symbols or threshold <= 0:
            raise AnalysisError("Kelly event threshold must be positive")
        if base_variable not in spec.initial.valuation:
            raise AnalysisError(f"initial valuation needs '{base_variable}' for Kelly bound")
        if not (
            isinstance(spec.event, Compare)
            and spec.event.operator == "<="
            and isinstance(spec.event.left, Variable)
            and spec.event.left.name == base_variable
            and isinstance(spec.event.right, Number)
            and arithmetic_to_symbolic(spec.event.right) == threshold
        ):
            raise AnalysisError(
                "Kelly normalization currently requires event 'base_variable <= threshold'"
            )
        if not gains:
            raise AnalysisError("Kelly scalar certificate needs at least one gain")
        probability_sum = sp.simplify(sum((probability for probability, _ in gains), sp.Integer(0)))
        if probability_sum != 1:
            raise AnalysisError("Kelly gain probabilities must sum exactly to one")
        if any(probability < 0 or gain <= 0 for probability, gain in gains):
            raise AnalysisError("Kelly probabilities must be nonnegative and gains positive")
        moment = sp.simplify(
            sum(
                (probability * gain ** (-lambda_value) for probability, gain in gains),
                sp.Integer(0),
            )
        )
        fixed_rho = sp.simplify(moment if rho is None else rho)
        difference = sp.simplify(fixed_rho - moment)
        if difference.is_nonnegative is not True:
            raise AnalysisError(
                "could not prove exact Kelly gain moment <= fixed rho; choose rho at least the moment"
            )
        if fixed_rho > 1:
            raise AnalysisError("Kelly gain moment is not contractive (rho > 1)")
        initial_base = spec.initial.valuation[base_variable]
        initial_certificate = sp.simplify((initial_base / threshold) ** (-lambda_value))
        bound = sp.simplify(fixed_rho**spec.horizon * initial_certificate)
        origin = _origin(spec.analysis_id, self.kind, "kelly_power", cfg, location=spec.initial.location)
        constraint = ScalarMomentConstraint(
            moment,
            "<=",
            fixed_rho,
            origin,
            frozenset({"contraction", "scalar_moment", "fixed_lambda"}),
        )
        return ScalarMomentModel(
            spec.analysis_id,
            self.kind,
            {
                "lambda": lambda_value,
                "rho": fixed_rho,
                "horizon": sp.Integer(spec.horizon),
                "threshold": threshold,
            },
            (constraint,),
            Objective(
                "evaluate",
                bound,
                f"rho^{spec.horizon} * ({base_variable}_initial / threshold)^(-lambda)",
            ),
            (
                "the listed gains are iid multiplicative updates of the base variable",
                "lambda, horizon, threshold and rho are fixed",
                "event is base_variable <= threshold at the fixed horizon",
            ),
        )


class AssertionViolationGoal:
    kind = "assertion_violation"

    def __init__(
        self,
        polynomial_service: PolynomialService | None = None,
        expectation_engine: ExpectationEngine | None = None,
    ):
        self.polynomials = polynomial_service or PolynomialService()
        self.expectation = expectation_engine or ExpectationEngine(self.polynomials)

    def validate(self, cfg: ProgramCFG, spec: AssertionViolationGoalSpec) -> None:
        if not spec.failure_locations:
            raise AnalysisError("assertion-violation goal requires failure locations")
        if not spec.failure_locations <= set(cfg.locations):
            raise AnalysisError("assertion-violation goal contains unknown failure locations")
        if spec.normal_terminal not in cfg.locations:
            raise AnalysisError("assertion-violation goal has an unknown normal terminal")
        if spec.reachability_mode != "eventual":
            raise AnalysisError("stage 3B supports reachability_mode='eventual' only")
        if spec.horizon is not None:
            raise AnalysisError("eventual assertion-violation goals do not take a horizon")
        if spec.initial.location not in cfg.locations:
            raise AnalysisError("assertion-violation initial location is unknown")
        expected_variables = set(cfg.symbols.program_variables)
        supplied_variables = set(spec.initial.valuation)
        if supplied_variables != expected_variables:
            raise AnalysisError(
                "initial valuation must define exactly the program variables; "
                f"missing={sorted(expected_variables - supplied_variables)}, "
                f"unknown={sorted(supplied_variables - expected_variables)}"
            )

    def obligations(
        self,
        cfg: ProgramCFG,
        spec: AssertionViolationGoalSpec,
        template: PolynomialTemplateInstance,
        *,
        factorization_q: Mapping[str, sp.Expr] | None = None,
        k: int = 1,
    ) -> PolynomialObligationModel:
        self.validate(cfg, spec)
        ordinary = set(cfg.locations) - set(spec.failure_locations) - {spec.normal_terminal}
        if set(template.locations) != ordinary:
            raise AnalysisError("assertion template must cover exactly the nonterminal locations")
        if k != 1:
            raise AnalysisError("convex fixed-parameter factorization currently supports k=1 only")
        q = factorization_q or {}
        unknown_q = set(q) - ordinary
        if unknown_q:
            raise AnalysisError(f"factorization q supplied for special/unknown locations: {unknown_q}")
        kind = "direct_theta" if factorization_q is None else "fixed_factorized_eta_k1"
        values: dict[str, Polynomial] = {}
        for location in ordinary:
            fixed_q = q.get(location, sp.Integer(1))
            if fixed_q.free_symbols or fixed_q <= 0:
                raise AnalysisError("factorization q values must be fixed positive constants")
            values[location] = self.polynomials.scale(fixed_q, template.expression_at(location))
        values[spec.normal_terminal] = self.polynomials.normalize(0)
        for failure in spec.failure_locations:
            values[failure] = self.polynomials.normalize(1)

        obligations: list[ProofObligation] = []
        for failure in sorted(spec.failure_locations):
            obligations.append(
                ProofObligation(
                    f"assert_failure_boundary_{failure}",
                    _domain(cfg, failure),
                    PolynomialRelation(values[failure], ">=", self.polynomials.normalize(1)),
                    _origin(spec.analysis_id, self.kind, kind, cfg, location=failure),
                    frozenset({"failure_boundary"}),
                )
            )
        obligations.append(
            ProofObligation(
                f"assert_normal_boundary_{spec.normal_terminal}",
                _domain(cfg, spec.normal_terminal),
                PolynomialRelation(
                    values[spec.normal_terminal], "=", self.polynomials.normalize(0)
                ),
                _origin(spec.analysis_id, self.kind, kind, cfg, location=spec.normal_terminal),
                frozenset({"normal_boundary"}),
            )
        )
        for location in cfg.locations:
            obligations.append(
                ProofObligation(
                    f"assert_nonnegative_{location}",
                    _domain(cfg, location),
                    PolynomialRelation(values[location], ">=", self.polynomials.normalize(0)),
                    _origin(spec.analysis_id, self.kind, kind, cfg, location=location),
                    frozenset({"nonnegative"}),
                )
            )
        for group in cfg.transitions:
            pre, traces = self.expectation.transition_expectation(values, group)
            obligations.append(
                ProofObligation(
                    f"assert_prefixed_{group.id}",
                    _domain(cfg, group.source, group.guard),
                    PolynomialRelation(values[group.source], ">=", pre),
                    _origin(spec.analysis_id, self.kind, kind, cfg, group=group),
                    frozenset({"prefixed_point"}),
                    {"branches": [trace.to_data() for trace in traces]},
                )
            )
        objective = Objective(
            "minimize",
            _evaluate(values[spec.initial.location], spec.initial.valuation),
            "Theta(initial), bounding eventual assertion-failure probability",
        )
        model = PolynomialObligationModel(
            spec.analysis_id,
            self.kind,
            cfg.symbols.program_variables,
            template.decision_variables(),
            tuple(obligations),
            objective,
            frozenset(
                {"failure_boundary", "normal_boundary", "nonnegative", "prefixed_point"}
            ),
        )
        if not model.required_tags <= model.actual_tags:
            raise AnalysisError("assertion lowering lost a required obligation category")
        nonaffine = [
            item.id
            for item in model.obligations
            if not self.polynomials.is_affine_in(
                item.relation.normalized, model.decision_variables
            )
        ]
        if nonaffine:
            raise AnalysisError(f"assertion obligations are non-affine in decisions: {nonaffine}")
        return model
