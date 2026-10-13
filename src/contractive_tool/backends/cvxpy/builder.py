from __future__ import annotations

from dataclasses import dataclass
import math
import sympy as sp

from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.ir import ConicModel


@dataclass
class BuiltModel:
    ir: ConicModel
    problem: object
    vector: object
    indices: dict


def build(model):
    import cvxpy as cp
    if len(set(model.decisions)) != len(model.decisions):
        raise AnalysisError("Duplicate conic decision IDs")
    # Round-trip validates exact affine coefficients before floating-point conversion.
    data = model.to_data()
    indices = {name: index for index, name in enumerate(model.decisions)}
    vector = cp.Variable(max(1, len(indices)), name="conic_decisions")

    def affine(row):
        constant = float(sp.Rational(row["constant"]))
        coefficients = [float(sp.Rational(v)) for v in row["coefficients"].values()]
        if not all(math.isfinite(x) for x in [constant, *coefficients]):
            raise AnalysisError("Non-finite coefficient conversion")
        return constant + sum((value * vector[indices[name]]
                               for name, value in zip(row["coefficients"], coefficients)), 0)

    constraints = [affine(row) == 0 for row in data["coefficient_equalities"]]
    constraints += [vector[indices[name]] >= 0 for name in model.nonnegative]
    constraints += [cp.bmat([[vector[indices[name]] for name in row]
                             for row in block["matrix"]]) >> 0 for block in model.psd_blocks]
    problem = cp.Problem(cp.Minimize(affine(data["objective"])), constraints)
    if not problem.is_dcp():
        raise AnalysisError("Conic model is not DCP")
    return BuiltModel(model, problem, vector, indices)
