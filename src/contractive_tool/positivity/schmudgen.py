from __future__ import annotations

from itertools import combinations
import sympy as sp
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.putinar import lower_sos


class SchmudgenStrategy:
    id = "schmudgen"

    def supports(self, domain):
        return True

    def lower(self, domain, h, model, namespace, degree, limits):
        if 2**len(domain.generators) > limits.max_products:
            raise AnalysisError("Schmudgen product count exceeds encoding budget")
        products = [sp.expand(sp.prod(items)) for size in range(1, len(domain.generators)+1)
                    for items in combinations(domain.generators, size)]
        lower_sos(domain, h, model, namespace, degree, limits, products)
