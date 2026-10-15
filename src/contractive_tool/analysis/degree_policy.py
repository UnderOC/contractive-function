from dataclasses import dataclass
from contractive_tool.errors import AnalysisError


@dataclass(frozen=True)
class DegreePolicy:
    initial_degree: int = 1
    max_degree: int = 6
    step: int = 1
    continue_after_success: bool = False

    def degrees(self):
        if not 0 <= self.initial_degree <= self.max_degree <= 10 or self.step <= 0:
            raise AnalysisError('Require 0 <= initial_degree <= max_degree <= 10 and a positive degree step')
        return range(self.initial_degree, self.max_degree+1, self.step)
