from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import sympy as sp

from contractive_tool.algebra import Polynomial


@dataclass(frozen=True)
class InitialConfig:
    location: str
    valuation: Mapping[str, sp.Expr]


@dataclass(frozen=True)
class SemialgebraicRegion:
    predicates: tuple[str, ...]

    def to_data(self) -> dict[str, object]:
        return {"predicates": list(self.predicates), "interpretation": "conjunction"}


@dataclass(frozen=True)
class ConstraintOrigin:
    analysis_id: str
    goal_kind: str
    source_location: str | None
    transition_id: str | None
    template_kind: str
    source_span: Mapping[str, object] | None = None

    def to_data(self) -> dict[str, object]:
        return {
            "analysis_id": self.analysis_id,
            "goal_kind": self.goal_kind,
            "source_location": self.source_location,
            "transition_id": self.transition_id,
            "template_kind": self.template_kind,
            "source_span": self.source_span,
        }


@dataclass(frozen=True)
class PolynomialRelation:
    left: Polynomial
    relation: str
    right: Polynomial

    @property
    def normalized(self) -> Polynomial:
        return Polynomial(sp.expand(self.left.expression - self.right.expression))

    def to_data(self) -> dict[str, object]:
        return {
            "left": str(self.left),
            "relation": self.relation,
            "right": str(self.right),
            "normalized_left_minus_right": str(self.normalized),
        }


@dataclass(frozen=True)
class ProofObligation:
    id: str
    domain: SemialgebraicRegion
    relation: PolynomialRelation
    origin: ConstraintOrigin
    tags: frozenset[str]
    debug: Mapping[str, object] | None = None

    def to_data(self) -> dict[str, object]:
        return {
            "id": self.id,
            "domain": self.domain.to_data(),
            "relation": self.relation.to_data(),
            "origin": self.origin.to_data(),
            "tags": sorted(self.tags),
            "debug": self.debug,
        }


@dataclass(frozen=True)
class Objective:
    sense: str
    expression: sp.Expr
    meaning: str

    def to_data(self) -> dict[str, object]:
        return {
            "sense": self.sense,
            "expression": sp.sstr(self.expression),
            "numeric_value": float(sp.N(self.expression)) if not self.expression.free_symbols else None,
            "meaning": self.meaning,
        }


@dataclass(frozen=True)
class PolynomialObligationModel:
    analysis_id: str
    goal_kind: str
    state_symbols: tuple[str, ...]
    decision_variables: tuple[str, ...]
    obligations: tuple[ProofObligation, ...]
    objective: Objective
    required_tags: frozenset[str]

    @property
    def actual_tags(self) -> frozenset[str]:
        return frozenset(tag for item in self.obligations for tag in item.tags)

    def to_data(self) -> dict[str, object]:
        return {
            "model_kind": "polynomial_obligations",
            "analysis_id": self.analysis_id,
            "goal_kind": self.goal_kind,
            "state_symbols": list(self.state_symbols),
            "decision_variables": list(self.decision_variables),
            "required_tags": sorted(self.required_tags),
            "actual_tags": sorted(self.actual_tags),
            "required_tags_present": self.required_tags <= self.actual_tags,
            "objective": self.objective.to_data(),
            "obligations": [item.to_data() for item in self.obligations],
        }


@dataclass(frozen=True)
class ScalarMomentConstraint:
    left: sp.Expr
    relation: str
    right: sp.Expr
    origin: ConstraintOrigin
    tags: frozenset[str]

    def to_data(self) -> dict[str, object]:
        return {
            "left": sp.sstr(self.left),
            "left_numeric": float(sp.N(self.left)),
            "relation": self.relation,
            "right": sp.sstr(self.right),
            "right_numeric": float(sp.N(self.right)),
            "origin": self.origin.to_data(),
            "tags": sorted(self.tags),
        }


@dataclass(frozen=True)
class ScalarMomentModel:
    analysis_id: str
    goal_kind: str
    parameters: Mapping[str, sp.Expr]
    constraints: tuple[ScalarMomentConstraint, ...]
    objective: Objective
    assumptions: tuple[str, ...]

    def to_data(self) -> dict[str, object]:
        return {
            "model_kind": "scalar_moment",
            "analysis_id": self.analysis_id,
            "goal_kind": self.goal_kind,
            "parameters": {name: sp.sstr(value) for name, value in sorted(self.parameters.items())},
            "constraints": [item.to_data() for item in self.constraints],
            "objective": self.objective.to_data(),
            "assumptions": list(self.assumptions),
            "arithmetic": "exact symbolic",
        }
