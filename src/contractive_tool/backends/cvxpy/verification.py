from __future__ import annotations

import math
from fractions import Fraction
import sympy as sp


def exact_psd(matrix):
    """Exact rational Schur complement test including singular PSD blocks."""
    matrix = sp.Matrix(matrix)
    if matrix != matrix.T:
        return False
    while matrix.rows:
        if any(matrix[i, i] < 0 for i in range(matrix.rows)):
            return False
        positive = next((i for i in range(matrix.rows) if matrix[i, i] > 0), None)
        if positive is None:
            return matrix == sp.zeros(matrix.rows)
        rest = [i for i in range(matrix.rows) if i != positive]
        column = matrix.extract(rest, [positive])
        matrix = matrix.extract(rest, rest) - column * column.T / matrix[positive, positive]
    return True


def _reconstruct(model, values, equalities, *, denominators):
    """Recover a rational point on the exact coefficient-equality affine space."""
    names = model.decisions
    if set(names) != set(values) or not all(math.isfinite(v) for v in values.values()):
        return {"status": "verification_failed", "reason": "Missing or nonfinite decision values"}
    symbols = [sp.Symbol(x) for x in names]
    index = {x: i for i, x in enumerate(symbols)}
    # Sparse rational row elimination avoids a huge dense symbolic RREF.
    rows = {}
    for expr in equalities:
        coeffs = {index[x]: sp.diff(expr, x) for x in expr.free_symbols}
        constant = expr.xreplace(dict.fromkeys(expr.free_symbols, sp.Integer(0)))
        row = {i: c for i, c in coeffs.items() if c != 0}
        rhs = -constant
        while row:
            pivot = min(row)
            if pivot not in rows:
                lead = row[pivot]
                rows[pivot] = ({i: c / lead for i, c in row.items()}, rhs / lead)
                break
            known, value = rows[pivot]
            factor = row[pivot]
            rhs -= factor * value
            for i, c in known.items():
                updated = row.get(i, 0) - factor * c
                if updated == 0:
                    row.pop(i, None)
                else:
                    row[i] = updated
        if not row and rhs != 0:
            return {"status": "verification_failed", "reason": "Inconsistent exact coefficient equalities"}
    attempts = []
    for denominator in denominators:
        candidate = [sp.Rational(Fraction(0 if abs(values[name]) < 1e-9 else values[name])
                                 .limit_denominator(denominator)) for name in names]
        for pivot in sorted(rows, reverse=True):
            row, rhs = rows[pivot]
            candidate[pivot] = rhs - sum(c * candidate[i] for i, c in row.items() if i != pivot)
        substitution = dict(zip(symbols, candidate))
        negative = [name for name in model.nonnegative if substitution[sp.Symbol(name)] < 0]
        nonpsd = [block["id"] for block in model.psd_blocks if not exact_psd(
            [[substitution[sp.Symbol(name)] for name in row] for row in block["matrix"]])]
        equality_ok = all(expr.xreplace(substitution) == 0 for expr in model.equalities)
        attempts.append({"denominator": denominator, "negative_coefficient_count": len(negative),
                         "nonpsd_count": len(nonpsd), "equalities_exact": equality_ok})
        if not negative and not nonpsd and equality_ok:
            bound = model.objective.xreplace(substitution)
            return {"status": "proved", "method": "rational_affine_reconstruction_exact_psd",
                    "bound_exact": str(bound), "bound_numeric": float(bound),
                    "exact_values": {name: str(value) for name, value in zip(names, candidate)},
                    "coverage": model.coverage, "attempts": attempts}
    return {"status": "solved_unverified", "method": "rational_affine_reconstruction_exact_psd",
            "reason": "No exactly feasible rational reconstruction found", "attempts": attempts}


def reconstruct(model, values, *, denominators=(1000, 1000000, 1000000000)):
    """Try numerical cone faces, then verify the recovered rational point exactly.

    A PSD matrix with a zero diagonal has an identically zero corresponding row.
    Numerical guesses only add equations: acceptance still requires every original
    equality, nonnegative scalar and PSD constraint over exact rationals.
    """
    if set(model.decisions) != set(values) or not all(math.isfinite(v) for v in values.values()):
        return {"status":"verification_failed", "reason":"Missing or nonfinite decision values"}
    zero_names = {name for name in model.nonnegative if abs(values[name]) < 1e-8}
    for block in model.psd_blocks:
        matrix = block['matrix']
        for i,row in enumerate(matrix):
            if abs(values[row[i]]) < 1e-8:
                zero_names.update(row)
    if zero_names:
        face = _reconstruct(model, values,
                            [sp.Symbol(name) for name in sorted(zero_names)]+model.equalities,
                            denominators=denominators)
        if face['status']=='proved':
            face['recovered_zero_face'] = sorted(zero_names)
            return face
    return _reconstruct(model, values, model.equalities, denominators=denominators)
