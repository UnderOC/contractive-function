"""Certificate-family extension boundary. Fractional powers require a separate theory."""
from contractive_tool.errors import AnalysisError
from contractive_tool.analysis.goals import make_problem


class PolynomialFamily:
    available = True
    instantiate = staticmethod(make_problem)


class FractionalPowerFamily:
    available = False

    def instantiate(self, *args, **kwargs):
        raise AnalysisError('fractional_k_not_implemented')


def get_family(name):
    if name == 'polynomial':
        return PolynomialFamily()
    if name == 'fractional_power':
        raise AnalysisError('fractional_k_not_implemented')
    raise AnalysisError(f'Unknown certificate family {name!r}')
