"""Finite exact contraction grid, independent of the polynomial degree policy."""
from dataclasses import dataclass
import sympy as sp
from contractive_tool.errors import AnalysisError


@dataclass(frozen=True)
class FixedContractionGrid:
    values: tuple[str, ...] = ('1/2', '9/10', '99/100')

    def candidates(self):
        try:
            result = tuple(dict.fromkeys(sp.Rational(value) for value in self.values))
        except (TypeError, ValueError) as error:
            raise AnalysisError('c candidates must be exact rational numbers') from error
        if not result or any(not 0 < c < 1 for c in result):
            raise AnalysisError('All c candidates must lie strictly in (0,1)')
        return result
