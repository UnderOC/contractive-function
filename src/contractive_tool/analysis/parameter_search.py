"""Bounded rational bisection; explicit grids retained for reproducible runs."""
from dataclasses import dataclass
import sympy as sp
from contractive_tool.errors import AnalysisError


class ContractionBisection:
    """Search a monotone feasibility oracle without evaluating c=0 or c=1.

Only verified feasibility tightens the upper endpoint. An infeasible response
is a solver/encoding observation, not a proof of polynomial nonexistence.
An inconclusive response stops this degree without discarding prior witnesses.
"""

    def __init__(self, max_steps=10):
        if type(max_steps) is not int or max_steps <= 0:
            raise AnalysisError('max_c_steps must be a positive integer')
        self.max_steps = max_steps
        self.lower, self.upper = sp.Rational(0), sp.Rational(1)
        self.best_verified = None
        self.history = []
        self.stop_reason = None
        self.pending = None

    def candidates(self):
        for _ in range(self.max_steps):
            if self.stop_reason:
                return
            self.pending = (self.lower+self.upper)/2
            yield self.pending
            if self.pending is not None:
                raise AnalysisError('Bisection requires feedback before the next candidate')

    def observe(self, status):
        if self.pending is None:
            raise AnalysisError('No pending contraction candidate')
        if status not in ('proved','infeasible','unknown'):
            raise AnalysisError('Invalid bisection oracle status')
        c = self.pending
        before = [str(self.lower),str(self.upper)]
        if status == 'proved':
            self.upper = self.best_verified = c
        elif status == 'infeasible':
            self.lower = c
        else:
            self.stop_reason = 'oracle_inconclusive'
        self.history.append({'iteration':len(self.history)+1,'c':str(c),'status':status,
                             'interval_before':before,
                             'interval_after':[str(self.lower),str(self.upper)]})
        self.pending = None
        if len(self.history) == self.max_steps and self.stop_reason is None:
            self.stop_reason = 'max_c_steps'

    def to_data(self):
        return {'method':'bisection','max_steps':self.max_steps,
                'interval':[str(self.lower),str(self.upper)],
                'best_verified_c':str(self.best_verified) if self.best_verified is not None else None,
                'stop_reason':self.stop_reason,'steps':self.history,
                'lower_endpoint_is_nonexistence_proof':False,
                'upper_endpoint_verified':self.best_verified is not None}


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
