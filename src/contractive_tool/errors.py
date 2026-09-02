from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Diagnostic:
    message: str
    file: str
    line: int
    column: int

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}: {self.message}"


class FrontendError(Exception):
    """Base class for source-facing frontend failures."""

    def __init__(self, diagnostics: list[Diagnostic] | tuple[Diagnostic, ...]):
        self.diagnostics = tuple(diagnostics)
        super().__init__("\n".join(map(str, self.diagnostics)))


class ParseError(FrontendError):
    pass


class SemanticError(FrontendError):
    pass


class CFGValidationError(FrontendError):
    pass


class AnalysisError(ValueError):
    """A typed analysis request cannot be soundly constructed."""
