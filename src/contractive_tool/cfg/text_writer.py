from __future__ import annotations

from contractive_tool.frontend.ast import format_expr
from contractive_tool.ir.cfg import ProgramCFG


def cfg_to_text(cfg: ProgramCFG) -> str:
    lines = [
        f"source: {cfg.source_file}",
        f"initial: {cfg.initial_location}",
        f"normal_terminal: {cfg.normal_terminal}",
        f"failure_terminal: {cfg.failure_terminal or '-'}",
        f"program_variables: {', '.join(cfg.symbols.program_variables) or '-'}",
        f"declared_random_variables: {', '.join(cfg.symbols.declared_random_variables) or '-'}",
        "",
        "locations:",
    ]
    for location in cfg.locations.values():
        source = (
            f"{location.span.file}:{location.span.start_line}:{location.span.start_column}"
            if location.span
            else "generated"
        )
        lines.append(
            f"  {location.id} [{location.kind}] invariant=({format_expr(location.invariant)}) @ {source}"
        )

    lines.extend(("", "transition groups:"))
    for group in cfg.transitions:
        lines.append(f"  {group.id}: {group.source} guard=({format_expr(group.guard)})")
        for index, branch in enumerate(group.branches, start=1):
            assignments = ", ".join(
                f"{name} := {format_expr(value)}"
                for name, value in sorted(branch.update.assignments.items())
            ) or "identity"
            samples = ", ".join(
                f"{sample.symbol} ~ {format_expr(sample.distribution)} [fresh]"
                for sample in branch.update.samples
            )
            suffix = f"; samples: {samples}" if samples else ""
            lines.append(
                f"    branch {index}: p={format_expr(branch.probability)} -> "
                f"{branch.destination}; update: {assignments}{suffix}"
            )
    return "\n".join(lines) + "\n"

