from __future__ import annotations

from dataclasses import dataclass

from contractive_tool.frontend.ast import DistributionExpr, Program


@dataclass(frozen=True)
class ProgramSymbols:
    program_variables: tuple[str, ...]
    declared_random_variables: tuple[str, ...]


@dataclass(frozen=True)
class ProgramIR:
    ast: Program
    symbols: ProgramSymbols
    random_distributions: dict[str, DistributionExpr]
    sampling_semantics: str = "fresh_on_each_transition"
    independence_assumption: str = "all samples are mutually independent"

