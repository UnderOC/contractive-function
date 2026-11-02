"""Bounded numerical certificate repair; only exact original-model checks prove.

Cone faces inferred from floating point are guesses, never proof assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import math
import time

import sympy as sp

from .builder import build, BuiltModel
from . import mosek_solver
from .verification import reconstruct, _reconstruct


@dataclass(frozen=True)
class RepairOptions:
    seconds: float = 20
    relative_gap: float = 0.05
    max_solves: int = 2


def gram_diagnostics(model, values):
    import numpy as np
    return [{"id": block['id'], "eigenvalues": np.linalg.eigvalsh(
        [[values[name] for name in row] for row in block['matrix']]).tolist()}
        for block in model.psd_blocks]


def infer_faces(model, values, *, threshold=1e-7, denominator=10000):
    """Use pivot columns to rationalize a kernel basis (not eigenvector phases)."""
    import numpy as np
    from scipy.linalg import qr
    equations, projectors, records = [], {}, []
    for block in model.psd_blocks:
        names = block['matrix']
        q = np.array([[values[name] for name in row] for row in names])
        eigenvalues = np.linalg.eigvalsh(q)
        cutoff = threshold * max(1., float(np.max(np.abs(eigenvalues))))
        rank = int(np.count_nonzero(eigenvalues > cutoff))
        if rank == len(q) or eigenvalues[0] < -cutoff:
            continue
        pivots = list(map(int, qr(q, pivoting=True)[2][:rank])) if rank else []
        free = [i for i in range(len(q)) if i not in pivots]
        kernel = sp.zeros(len(q), len(free))
        if rank:
            try:
                relation = np.linalg.solve(q[np.ix_(pivots, pivots)], q[np.ix_(pivots, free)])
            except np.linalg.LinAlgError:
                continue
            for i, pivot in enumerate(pivots):
                for j in range(len(free)):
                    kernel[pivot, j] = -sp.Rational(Fraction(float(relation[i, j])).limit_denominator(denominator))
        for j, index in enumerate(free):
            kernel[index, j] = 1
        symbolic = sp.Matrix([[sp.Symbol(name) for name in row] for row in names])
        equations.extend(sp.expand(expr) for expr in symbolic * kernel if expr != 0)
        support = kernel.T.nullspace()
        if support:
            basis = sp.Matrix.hstack(*support)
            projector = basis * (basis.T * basis).inv() * basis.T
        else:
            projector = sp.zeros(len(q))
        projectors[block['id']] = projector
        records.append({"id": block['id'], "rank_guess": rank,
                        "kernel": [[str(v) for v in row] for row in kernel.tolist()],
                        "threshold": threshold, "denominator": denominator})
    # Zero scalar multipliers also describe cone faces. These are extra
    # equations only: an incorrect guess may fail but cannot create a proof.
    zeros = [name for name in model.nonnegative if abs(values[name]) <= threshold]
    equations.extend(sp.Symbol(name) for name in zeros)
    return equations, projectors, {"blocks": records, "zero_scalars": zeros}


def build_margin_model(model, cap, *, equations=(), projectors=None):
    """Keep original constraints; seek PSD margin, optionally in a guessed face."""
    import cvxpy as cp
    import numpy as np
    built = build(model)
    vector, indices = built.vector, built.indices

    def affine(expr):
        free = expr.free_symbols
        return float(expr.xreplace(dict.fromkeys(free, sp.Integer(0)))) + sum(
            float(sp.diff(expr, x)) * vector[indices[str(x)]] for x in free)

    constraints = list(built.problem.constraints)
    constraints.append(affine(model.objective) <= float(cap))
    constraints.extend(affine(expr) == 0 for expr in equations)
    margin = cp.Variable(name='certificate_margin')
    constraints.extend([margin >= 0, margin <= 1])
    for block in model.psd_blocks:
        names = block['matrix']
        projector = (projectors or {}).get(block['id'], sp.eye(len(names)))
        if projector == sp.zeros(len(names)):
            continue
        q = cp.bmat([[vector[indices[name]] for name in row] for row in names])
        constraints.append(q - margin * np.array(projector).astype(float) >> 0)
    # LP-only certificates can use the same module.
    if not model.psd_blocks:
        constraints.extend(vector[indices[name]] >= margin for name in model.nonnegative)
    problem = cp.Problem(cp.Maximize(margin), constraints)
    return BuiltModel(model, problem, vector, indices)


def repair(model, values, *, options=None, deadline=None, solver_seconds=30, verbose=False):
    """Return (verification, audit). Deadlines are cooperative between stages."""
    options = options or RepairOptions()
    started = time.monotonic()
    deadline = min(deadline if deadline is not None else math.inf, started + options.seconds)
    audit = {"status": "solved_unverified", "attempts": [], "max_solves": options.max_solves}
    failure = {"status": "solved_unverified", "reason": "Certificate repair exhausted"}
    if set(values) != set(model.decisions) or not all(math.isfinite(v) for v in values.values()):
        return failure, {**audit, "reason": "Missing or nonfinite decision values"}
    if time.monotonic() >= deadline or options.max_solves <= 0:
        return failure, {**audit, "reason": "repair_disabled_or_time_budget"}
    numerical_objective = float(model.objective.xreplace({sp.Symbol(k): v for k,v in values.items()}))
    cap = sp.Rational(str(numerical_objective + max(1e-4, abs(numerical_objective)*options.relative_gap)))
    audit.update(objective_cap=str(cap), initial_gram=gram_diagnostics(model, values))
    solves = 0

    def accept(result, stage):
        if result['status'] == 'proved' and sp.Rational(result['bound_exact']) <= cap:
            result['repair_stage'] = stage
            result['repair_objective_cap'] = str(cap)
            audit.update(status='proved', elapsed_seconds=time.monotonic()-started, solver_calls=solves)
            return True
        if result['status'] == 'proved':
            result.update(status='solved_unverified', reason='Reconstructed objective exceeds repair cap')
        return False

    # At most one margin solve and one face solve, plus two finite kernel guesses.
    for stage, threshold, denominator in [('margin', None, None),
                                          ('face', 1e-7, 1000), ('face', 1e-6, 1000000)]:
        if time.monotonic() >= deadline:
            break
        row = {'stage': stage}
        audit['attempts'].append(row)
        equations, projectors = [], {}
        if stage == 'face':
            equations, projectors, guesses = infer_faces(model, values, threshold=threshold, denominator=denominator)
            row['face_guess'] = guesses
            if not equations:
                row['status'] = 'no_face_detected'
                continue
            candidate = _reconstruct(model, values, list(equations)+model.equalities,
                                     denominators=(1000, 1000000, 1000000000), deadline=deadline)
            row['direct_reconstruction'] = candidate
            if accept(candidate, 'kernel_reconstruction'):
                row['status'] = 'proved'
                return candidate, audit
        if solves >= options.max_solves or time.monotonic() >= deadline:
            row['status'] = 'repair_budget'
            continue
        built = build_margin_model(model, cap, equations=equations, projectors=projectors)
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            row['status'] = 'repair_time_budget'
            break
        solves += 1
        solved = mosek_solver.solve(built, time_limit=min(solver_seconds, remaining), verbose=verbose)
        solved['objective_kind'] = 'psd_margin'
        row['solver'] = solved
        row['status'] = solved['status']
        if solved.get('values') is None:
            continue
        new_values = solved['values']
        row['original_objective_numeric'] = float(model.objective.xreplace(
            {sp.Symbol(name): value for name, value in new_values.items()}))
        row['gram'] = gram_diagnostics(model, new_values)
        # Keep kernel equations during reconstruction, but acceptance always
        # checks every original equality and cone over exact rationals.
        candidate = (_reconstruct(model, new_values, list(equations)+model.equalities,
                                 denominators=(1000,1000000,1000000000), deadline=deadline)
                     if equations else reconstruct(model, new_values, deadline=deadline))
        row['verification'] = candidate
        row['status'] = candidate['status']
        if accept(candidate, stage+'_solve'):
            return candidate, audit
        row['status'] = candidate['status']
        # Keep the original solution for kernel estimation: a zero-margin solve
        # need not preserve its useful near-optimal low-rank structure.
    audit.update(elapsed_seconds=time.monotonic()-started, solver_calls=solves)
    return failure, audit
