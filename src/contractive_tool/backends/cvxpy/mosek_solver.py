from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
import logging
import math
import time


def solve(built, *, time_limit=60, verbose=False):
    import cvxpy as cp
    output = StringIO()
    started = time.monotonic()
    result = {"solver": "MOSEK", "status": "solver_failed", "raw_status": None}
    params = {"MSK_IPAR_NUM_THREADS": 1, "MSK_DPAR_OPTIMIZER_MAX_TIME": float(time_limit),
              "MSK_DPAR_INTPNT_CO_TOL_PFEAS": 1e-9,
              "MSK_DPAR_INTPNT_CO_TOL_DFEAS": 1e-9,
              "MSK_DPAR_INTPNT_CO_TOL_REL_GAP": 1e-9}
    result["mosek_params"] = params
    logger = cp.settings.LOGGER
    old_handlers, old_propagate = logger.handlers[:], logger.propagate
    capture = logging.StreamHandler(output)
    capture.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    try:
        if "MOSEK" not in cp.installed_solvers():
            raise RuntimeError("MOSEK Python interface is unavailable")
        with redirect_stdout(output), redirect_stderr(output):
            logger.handlers = [capture]
            logger.propagate = False
            built.problem.solve(solver=cp.MOSEK, verbose=verbose, mosek_params=params,
                                accept_unknown=False)
        result["raw_status"] = built.problem.status
        result["status"] = "numerical_issue"
        if built.problem.status in {cp.OPTIMAL, cp.OPTIMAL_INACCURATE}:
            values = built.vector.value
            if values is not None and all(math.isfinite(float(x)) for x in values):
                result["values"] = {name: float(values[index]) for name, index in built.indices.items()}
                result["objective"] = float(built.problem.value)
                result["status"] = "solved_unverified"
            else:
                result["status"] = "verification_failed"
        elif built.problem.status == cp.INFEASIBLE:
            result["status"] = "infeasible"
        elif built.problem.status == cp.UNBOUNDED:
            result["status"] = "unbounded"
        stats = built.problem.solver_stats
        result["stats"] = {"solve_time": stats.solve_time, "num_iters": stats.num_iters}
    except Exception as error:
        if isinstance(error, cp.error.SolverError):
            result["status"] = "numerical_issue"
        result["diagnostic"] = f"{type(error).__name__}: {error}"
    finally:
        logger.handlers = old_handlers
        logger.propagate = old_propagate
    if not verbose:
        output.write(f"solver=MOSEK raw_status={result['raw_status']} proof_status={result['status']}\n")
        if "diagnostic" in result:
            output.write(result["diagnostic"] + "\n")
    result["elapsed_seconds"] = time.monotonic() - started
    result["log"] = output.getvalue()
    return result
