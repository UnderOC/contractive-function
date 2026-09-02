from __future__ import annotations

from contractive_tool.frontend.ast import (
    Annotation,
    Assert,
    Assign,
    Assume,
    If,
    Program,
    Refute,
    Sequence,
    Skip,
    While,
    format_expr,
)


def _sequence_lines(sequence: Sequence, indent: int) -> list[str]:
    prefix = " " * indent
    lines: list[str] = []
    for stmt in sequence.statements:
        if isinstance(stmt, Annotation):
            lines.append(f"{prefix}{{{format_expr(stmt.predicate)}}}")
        elif isinstance(stmt, Skip):
            lines.append(f"{prefix}skip;")
        elif isinstance(stmt, Assign):
            lines.append(f"{prefix}{stmt.target} := {format_expr(stmt.value)};")
        elif isinstance(stmt, Assert):
            lines.append(f"{prefix}assert {format_expr(stmt.condition)};")
        elif isinstance(stmt, Refute):
            lines.append(f"{prefix}refute {format_expr(stmt.condition)};")
        elif isinstance(stmt, Assume):
            lines.append(f"{prefix}assume {format_expr(stmt.condition)};")
        elif isinstance(stmt, If):
            lines.append(f"{prefix}if {format_expr(stmt.condition)} then")
            lines.extend(_sequence_lines(stmt.then_branch, indent + 2))
            lines.append(f"{prefix}else")
            lines.extend(_sequence_lines(stmt.else_branch, indent + 2))
            lines.append(f"{prefix}fi;")
        elif isinstance(stmt, While):
            invariant = (
                f" invariant {format_expr(stmt.invariant)}" if stmt.invariant is not None else ""
            )
            lines.append(f"{prefix}while {format_expr(stmt.guard)}{invariant} do")
            lines.extend(_sequence_lines(stmt.body, indent + 2))
            lines.append(f"{prefix}od;")
        else:
            raise TypeError(type(stmt).__name__)
    return lines


def format_program(program: Program) -> str:
    lines = [
        f"random {item.name} ~ {format_expr(item.distribution)};"
        for item in program.declarations
    ]
    if lines and program.body.statements:
        lines.append("")
    lines.extend(_sequence_lines(program.body, 0))
    return "\n".join(lines) + "\n"

