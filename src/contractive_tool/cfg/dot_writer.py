from __future__ import annotations

from contractive_tool.frontend.ast import format_expr
from contractive_tool.ir.cfg import ProgramCFG


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def cfg_to_dot(cfg: ProgramCFG) -> str:
    lines = ["digraph pcfg {", "  rankdir=LR;", '  node [shape=box, fontname="monospace"];']
    for location in cfg.locations.values():
        shape = "doublecircle" if location.id in {cfg.normal_terminal, cfg.failure_terminal} else "box"
        label = f"{location.id}\\n{location.kind}\\nI: {format_expr(location.invariant)}"
        lines.append(f'  "{_escape(location.id)}" [shape={shape}, label="{_escape(label)}"];')
    lines.append(f'  start [shape=point, label=""];')
    lines.append(f'  start -> "{_escape(cfg.initial_location)}";')
    for group in cfg.transitions:
        for branch_index, branch in enumerate(group.branches, start=1):
            updates = ", ".join(
                f"{name}:={format_expr(expr)}" for name, expr in sorted(branch.update.assignments.items())
            ) or "id"
            samples = ", ".join(
                f"{sample.symbol}~{format_expr(sample.distribution)}" for sample in branch.update.samples
            )
            if samples:
                updates = f"{updates}; {samples}"
            label = (
                f"{group.id}.{branch_index}\\n"
                f"g: {format_expr(group.guard)}\\n"
                f"p: {format_expr(branch.probability)}\\n{updates}"
            )
            lines.append(
                f'  "{_escape(group.source)}" -> "{_escape(branch.destination)}" '
                f'[label="{_escape(label)}"];'
            )
    lines.append("}")
    return "\n".join(lines) + "\n"

