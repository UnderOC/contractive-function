from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from contractive_tool.frontend.ast import DistributionExpr, Expr, SourceSpan
from contractive_tool.ir.program import ProgramSymbols


@dataclass(frozen=True)
class Location:
    id: str
    kind: str
    span: SourceSpan | None
    invariant: Expr


@dataclass(frozen=True)
class RandomSample:
    symbol: str
    distribution: DistributionExpr
    fresh: bool = True


@dataclass(frozen=True)
class Update:
    assignments: Mapping[str, Expr]
    samples: tuple[RandomSample, ...] = ()


@dataclass(frozen=True)
class Branch:
    destination: str
    probability: Expr
    update: Update


@dataclass(frozen=True)
class TransitionGroup:
    id: str
    source: str
    guard: Expr
    branches: tuple[Branch, ...]
    origin: SourceSpan | None


@dataclass(frozen=True)
class ProgramCFG:
    locations: Mapping[str, Location]
    transitions: tuple[TransitionGroup, ...]
    symbols: ProgramSymbols
    initial_location: str
    normal_terminal: str
    failure_terminal: str | None
    source_file: str

    def outgoing(self, location: str) -> tuple[TransitionGroup, ...]:
        return tuple(group for group in self.transitions if group.source == location)

