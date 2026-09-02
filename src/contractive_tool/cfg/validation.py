from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from contractive_tool.errors import CFGValidationError, Diagnostic
from contractive_tool.frontend.ast import Binary, Number, format_expr
from contractive_tool.ir.cfg import ProgramCFG, TransitionGroup


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    probability_obligations: tuple[str, ...]
    checked_locations: int
    checked_transition_groups: int


def _probability_status(group: TransitionGroup) -> tuple[bool, str | None]:
    probabilities = [branch.probability for branch in group.branches]
    if all(isinstance(item, Number) for item in probabilities):
        total = sum((item.decimal for item in probabilities), Decimal(0))
        return total == 1, None
    if len(probabilities) == 2:
        first, second = probabilities
        if (
            isinstance(second, Binary)
            and second.operator == "-"
            and isinstance(second.left, Number)
            and second.left.decimal == 1
            and second.right == first
        ):
            if isinstance(first, Number):
                return Decimal(0) <= first.decimal <= Decimal(1), None
            return True, f"{group.id}: prove 0 <= {format_expr(first)} <= 1"
    expression = " + ".join(format_expr(item) for item in probabilities)
    return True, f"{group.id}: prove 0 <= p_j <= 1 and {expression} = 1"


def validate_cfg(cfg: ProgramCFG, *, require_failure: bool = False) -> ValidationReport:
    diagnostics: list[Diagnostic] = []
    obligations: list[str] = []
    synthetic_file = cfg.source_file

    def error(message: str) -> None:
        diagnostics.append(Diagnostic(message, synthetic_file, 1, 1))

    if cfg.initial_location not in cfg.locations:
        error("initial location does not exist")
    if cfg.normal_terminal not in cfg.locations:
        error("normal terminal does not exist")
    if require_failure and (cfg.failure_terminal is None or cfg.failure_terminal not in cfg.locations):
        error("failure terminal is required but missing")

    outgoing = {location_id: cfg.outgoing(location_id) for location_id in cfg.locations}
    for location_id, groups in outgoing.items():
        if not groups:
            error(f"location '{location_id}' has no outgoing transition")

    program_variables = set(cfg.symbols.program_variables)
    for group in cfg.transitions:
        if group.source not in cfg.locations:
            error(f"transition '{group.id}' has unknown source '{group.source}'")
        if not group.branches:
            error(f"transition '{group.id}' has no branches")
        probability_valid, obligation = _probability_status(group)
        if not probability_valid:
            error(f"probabilities in transition '{group.id}' do not sum to one")
        if obligation:
            obligations.append(obligation)
        for branch in group.branches:
            if branch.destination not in cfg.locations:
                error(
                    f"transition '{group.id}' has unknown destination '{branch.destination}'"
                )
            unknown_targets = set(branch.update.assignments) - program_variables
            if unknown_targets:
                error(
                    f"transition '{group.id}' updates unknown variables: "
                    + ", ".join(sorted(unknown_targets))
                )
            for sample in branch.update.samples:
                if sample.distribution.name not in {"Uniform", "Normal", "Bernoulli"}:
                    error(
                        f"transition '{group.id}' has unsupported sample distribution "
                        f"'{sample.distribution.name}'"
                    )

    for terminal in filter(None, (cfg.normal_terminal, cfg.failure_terminal)):
        groups = outgoing.get(terminal, ())
        absorbs = any(
            len(group.branches) == 1 and group.branches[0].destination == terminal
            for group in groups
        )
        if not absorbs:
            error(f"terminal '{terminal}' is not absorbing")

    if diagnostics:
        raise CFGValidationError(diagnostics)
    return ValidationReport(True, tuple(obligations), len(cfg.locations), len(cfg.transitions))
