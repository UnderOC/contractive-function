from __future__ import annotations

from dataclasses import dataclass, field
import sympy as sp


def rational_data(value: sp.Expr) -> str:
    if value.is_Rational is not True:
        raise ValueError(f"Only exact rational coefficients are supported: {value}")
    return str(value)


@dataclass(frozen=True)
class BasicSet:
    variables: tuple[sp.Symbol, ...]
    generators: tuple[sp.Expr, ...] = ()
    equalities: tuple[sp.Expr, ...] = ()

    def to_data(self):
        return {"variables": [str(x) for x in self.variables],
                "generators": [str(x) for x in self.generators],
                "equalities": [str(x) for x in self.equalities]}


@dataclass(frozen=True)
class Implication:
    id: str
    domain: BasicSet
    conclusion: sp.Expr
    origin: dict
    tags: tuple[str, ...]

    def to_data(self):
        return {"id": self.id, "domain": self.domain.to_data(),
                "conclusion": str(self.conclusion), "origin": self.origin,
                "tags": list(self.tags)}


@dataclass
class ConicModel:
    decisions: list[str]
    objective: sp.Expr
    equalities: list[sp.Expr] = field(default_factory=list)
    nonnegative: list[str] = field(default_factory=list)
    psd_blocks: list[dict] = field(default_factory=list)
    coverage: dict = field(default_factory=dict)

    def to_data(self):
        symbols = set(sp.Symbol(x) for x in self.decisions)

        def affine(expr):
            free = tuple(sorted(expr.free_symbols, key=str))
            if set(free) - symbols:
                raise ValueError("Undeclared conic decision")
            poly = sp.Poly(sp.expand(expr), *free) if free else None
            if poly is not None and poly.total_degree() > 1:
                raise ValueError("Non-affine conic model")
            constant = expr.xreplace(dict.fromkeys(free, sp.Integer(0)))
            return {"constant": rational_data(constant), "coefficients": {
                str(x): rational_data(sp.diff(expr, x)) for x in free}}

        return {"schema_version": 1, "model_kind": "sdp" if self.psd_blocks else "lp",
                "decisions": self.decisions, "objective": affine(self.objective),
                "coefficient_equalities": [affine(x) for x in self.equalities],
                "nonnegative": self.nonnegative, "psd_blocks": self.psd_blocks,
                "coverage": self.coverage}

    @classmethod
    def from_data(cls, data):
        symbols = {name: sp.Symbol(name) for name in data["decisions"]}

        def affine(row):
            return sp.Rational(row["constant"]) + sum(
                (sp.Rational(value) * symbols[name] for name, value in row["coefficients"].items()),
                sp.Integer(0))

        return cls(list(symbols), affine(data["objective"]),
                   [affine(row) for row in data["coefficient_equalities"]],
                   data["nonnegative"], data["psd_blocks"], data["coverage"])
