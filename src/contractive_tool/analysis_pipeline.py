from __future__ import annotations

import hashlib
import json
import platform
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

import sympy as sp

from contractive_tool import __version__
from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.analysis.goals import (
    AssertionViolationGoal,
    AssertionViolationGoalSpec,
    TailBoundGoal,
    TailBoundGoalSpec,
)
from contractive_tool.analysis.ir import InitialConfig, PolynomialObligationModel, ScalarMomentModel
from contractive_tool.analysis.templates import PolynomialTemplateFactory
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.ast import (
    Binary,
    BoolBinary,
    BoolUnary,
    Compare,
    Expr,
    Number,
    Sequence,
    Unary,
    Variable,
    format_expr,
)
from contractive_tool.frontend.parser import parse_file, parse_text
from contractive_tool.frontend.semantic import check_program
from contractive_tool.ir.cfg import ProgramCFG
from contractive_tool.pipeline import compile_to_cfg


@dataclass(frozen=True)
class AnalysisRequest:
    goal: str
    certificate: str
    analysis_id: str
    initial: Mapping[str, sp.Expr]
    initial_location: str | None = None
    event: str | None = None
    horizon: int | None = None
    event_mode: str = "at_horizon"
    degree: int = 1
    rho: sp.Expr | None = None
    normalization_scale: sp.Expr = sp.Integer(1)
    positivity_margin: sp.Expr = sp.Integer(0)
    base_variable: str | None = None
    lambda_value: sp.Expr | None = None
    threshold: sp.Expr | None = None
    factor_q: sp.Expr | None = None
    k: int = 1


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _walk_expr(expr: Expr):
    yield expr
    if isinstance(expr, (Unary, BoolUnary)):
        yield from _walk_expr(expr.operand)
    elif isinstance(expr, (Binary, BoolBinary, Compare)):
        yield from _walk_expr(expr.left)
        yield from _walk_expr(expr.right)


def parse_event(text: str, cfg: ProgramCFG) -> Expr:
    parsed = parse_text(f"assume {text};", "<command-line-event>")
    statement = parsed.body.statements[0]
    event = statement.condition
    if not isinstance(event, (Compare, BoolBinary, BoolUnary)):
        raise AnalysisError("tail event must be a boolean polynomial predicate")
    unknown = {
        item.name
        for item in _walk_expr(event)
        if isinstance(item, Variable) and item.name not in cfg.symbols.program_variables
    }
    if unknown:
        raise AnalysisError(f"tail event contains unknown variables: {sorted(unknown)}")
    return event


def _multiplicative_gain(rhs: Expr, base_variable: str) -> sp.Expr | None:
    if not isinstance(rhs, Binary) or rhs.operator != "*":
        return None
    if isinstance(rhs.left, Variable) and rhs.left.name == base_variable and isinstance(rhs.right, Number):
        return arithmetic_to_symbolic(rhs.right)
    if isinstance(rhs.right, Variable) and rhs.right.name == base_variable and isinstance(rhs.left, Number):
        return arithmetic_to_symbolic(rhs.left)
    return None


def infer_iid_multiplicative_gains(
    cfg: ProgramCFG, base_variable: str
) -> tuple[tuple[sp.Expr, sp.Expr], ...]:
    """Recognize a grouped probability choice whose destinations multiply one base variable."""
    candidates: list[tuple[tuple[sp.Expr, sp.Expr], ...]] = []
    for group in cfg.transitions:
        if len(group.branches) < 2:
            continue
        gains: list[tuple[sp.Expr, sp.Expr]] = []
        for branch in group.branches:
            outgoing = cfg.outgoing(branch.destination)
            if len(outgoing) != 1 or len(outgoing[0].branches) != 1:
                break
            assignment = outgoing[0].branches[0].update.assignments.get(base_variable)
            if assignment is None:
                break
            gain = _multiplicative_gain(assignment, base_variable)
            if gain is None:
                break
            gains.append((arithmetic_to_symbolic(branch.probability), gain))
        else:
            candidates.append(tuple(gains))
    unique = []
    for candidate in candidates:
        if candidate not in unique:
            unique.append(candidate)
    if len(unique) != 1:
        raise AnalysisError(
            f"expected one iid multiplicative gain choice for '{base_variable}', found {len(unique)}"
        )
    return unique[0]


def _obligations_text(model: PolynomialObligationModel) -> str:
    lines = [
        f"analysis: {model.analysis_id}",
        f"goal: {model.goal_kind}",
        f"objective: {model.objective.sense} {sp.sstr(model.objective.expression)}",
        "",
    ]
    for item in model.obligations:
        domain = " and ".join(item.domain.predicates)
        lines.extend(
            [
                f"[{item.id}] tags={','.join(sorted(item.tags))}",
                f"  domain: {domain}",
                f"  prove: {item.relation.left} {item.relation.relation} {item.relation.right}",
            ]
        )
    return "\n".join(lines) + "\n"


def _goal_initial_location(cfg: ProgramCFG, request: AnalysisRequest) -> str:
    if request.initial_location:
        return request.initial_location
    if request.certificate == "kelly":
        loops = [location.id for location in cfg.locations.values() if location.kind == "while"]
        if len(loops) == 1:
            return loops[0]
    return cfg.initial_location


def generate_analysis(
    source: str | Path, out_dir: str | Path, request: AnalysisRequest
) -> dict[str, object]:
    source_path = Path(source).resolve()
    output_path = Path(out_dir).resolve()
    shared_path = output_path / "shared"
    compile_to_cfg(source_path, shared_path)
    program = check_program(parse_file(source_path))
    cfg = build_cfg(program)
    initial = InitialConfig(_goal_initial_location(cfg, request), request.initial)
    analysis_path = output_path / "analyses" / request.analysis_id
    certificate_path = analysis_path / "certificates" / request.certificate
    certificate_path.mkdir(parents=True, exist_ok=True)

    template_data: dict[str, object] | None = None
    if request.goal == "tail_bound":
        if request.event is None or request.horizon is None:
            raise AnalysisError("tail_bound requires --event and --horizon")
        event = parse_event(request.event, cfg)
        spec = TailBoundGoalSpec(
            request.analysis_id,
            event,
            request.horizon,
            request.event_mode,
            initial,
            request.normalization_scale,
            request.rho if request.rho is not None else sp.Integer(1),
        )
        goal = TailBoundGoal()
        if request.certificate == "kelly":
            if request.base_variable is None or request.lambda_value is None or request.threshold is None:
                raise AnalysisError("kelly certificate requires --base, --lambda and --threshold")
            gains = infer_iid_multiplicative_gains(cfg, request.base_variable)
            model: PolynomialObligationModel | ScalarMomentModel = goal.kelly_scalar_model(
                cfg,
                spec,
                base_variable=request.base_variable,
                lambda_value=request.lambda_value,
                gains=gains,
                threshold=request.threshold,
                rho=request.rho,
            )
            model_file = "scalar_model.json"
            status = "proved"
            backend_route = "exact_scalar_moment"
        elif request.certificate == "polynomial-eta":
            template = PolynomialTemplateFactory().instantiate(
                cfg, degree=request.degree, prefix="eta"
            )
            template_data = template.metadata()
            model = goal.polynomial_obligations(
                cfg, spec, template, positivity_margin=request.positivity_margin
            )
            model_file = "polynomial_model.json"
            status = "not_solved"
            backend_route = "affine_polynomial_obligations"
        else:
            raise AnalysisError("tail_bound supports certificates: kelly, polynomial-eta")
        goal_data = {
            "kind": "tail_bound",
            "analysis_id": request.analysis_id,
            "event": format_expr(event),
            "event_mode": request.event_mode,
            "horizon": request.horizon,
            "initial_location": initial.location,
            "initial_valuation": {name: sp.sstr(value) for name, value in sorted(initial.valuation.items())},
            "normalization": "certificate_geq_one_on_event",
        }
    elif request.goal == "assertion_violation":
        if cfg.failure_terminal is None:
            raise AnalysisError("assertion_violation requires an assert/refute failure location")
        spec = AssertionViolationGoalSpec(
            request.analysis_id,
            initial,
            frozenset({cfg.failure_terminal}),
            cfg.normal_terminal,
        )
        goal = AssertionViolationGoal()
        ordinary = set(cfg.locations) - {cfg.normal_terminal, cfg.failure_terminal}
        if request.certificate not in {"direct-theta", "factorized"}:
            raise AnalysisError(
                "assertion_violation supports certificates: direct-theta, factorized"
            )
        prefix = "theta" if request.certificate == "direct-theta" else "eta"
        template = PolynomialTemplateFactory().instantiate(
            cfg, degree=request.degree, prefix=prefix, locations=sorted(ordinary)
        )
        template_data = template.metadata()
        factors = None
        if request.certificate == "factorized":
            fixed_q = request.factor_q if request.factor_q is not None else sp.Integer(1)
            factors = {location: fixed_q for location in ordinary}
        model = goal.obligations(cfg, spec, template, factorization_q=factors, k=request.k)
        model_file = "polynomial_model.json"
        status = "not_solved"
        backend_route = "affine_polynomial_obligations"
        goal_data = {
            "kind": "assertion_violation",
            "analysis_id": request.analysis_id,
            "reachability_mode": "eventual",
            "failure_locations": sorted(spec.failure_locations),
            "normal_terminal": spec.normal_terminal,
            "initial_location": initial.location,
            "initial_valuation": {name: sp.sstr(value) for name, value in sorted(initial.valuation.items())},
        }
    else:
        raise AnalysisError("goal must be tail_bound or assertion_violation")

    _write_json(analysis_path / "goal.json", goal_data)
    if template_data is not None:
        _write_json(certificate_path / "template.json", template_data)
    model_data = model.to_data()
    _write_json(certificate_path / model_file, model_data)
    if isinstance(model, PolynomialObligationModel):
        _write_json(
            certificate_path / "obligations.json",
            {
                "analysis_id": model.analysis_id,
                "goal_kind": model.goal_kind,
                "required_tags": sorted(model.required_tags),
                "decision_coefficients_affine": True,
                "obligations": [item.to_data() for item in model.obligations],
            },
        )
        (certificate_path / "obligations.txt").write_text(
            _obligations_text(model), encoding="utf-8"
        )
    result = {
        "analysis_id": request.analysis_id,
        "goal_kind": request.goal,
        "certificate_id": request.certificate,
        "status": status,
        "backend_route": backend_route,
        "bound": model.objective.to_data(),
        "matlab_invoked": False,
    }
    _write_json(certificate_path / "result.json", result)
    summary = {
        "analysis_id": request.analysis_id,
        "goal_kind": request.goal,
        "results": [result],
        "selection": result if status == "proved" else "pending",
    }
    _write_json(analysis_path / "summary.json", summary)
    _write_json(output_path / "summary.json", {"analyses": [summary]})

    artifact_paths = sorted(path for path in output_path.rglob("*") if path.is_file())
    manifest = {
        "schema_version": 2,
        "tool": {"name": "contractive-tool", "version": __version__},
        "python_version": platform.python_version(),
        "phase": "stages_2_3_obligation_generation",
        "input": {"path": str(source_path), "sha256": _sha256(source_path)},
        "analysis": goal_data,
        "certificate": {
            "kind": request.certificate,
            "degree": request.degree if template_data is not None else None,
            "k": request.k,
            "lambda": sp.sstr(request.lambda_value) if request.lambda_value is not None else None,
            "fixed_factor_q": sp.sstr(request.factor_q) if request.factor_q is not None else None,
        },
        "semantics": {
            "updates": "simultaneous",
            "random_sampling": program.sampling_semantics,
            "random_independence": program.independence_assumption,
            "arithmetic": "exact rational/symbolic until numeric display",
        },
        "backend": {"route": backend_route, "matlab_invoked": False},
        "artifacts": {
            str(path.relative_to(output_path)): _sha256(path) for path in artifact_paths
        },
    }
    _write_json(output_path / "manifest.json", manifest)
    return {
        "source": str(source_path),
        "out_dir": str(output_path),
        "analysis_id": request.analysis_id,
        "goal_kind": request.goal,
        "certificate_id": request.certificate,
        "status": status,
        "backend_route": backend_route,
        "model": str((certificate_path / model_file).resolve()),
    }
