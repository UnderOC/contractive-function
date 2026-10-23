"""Bounded rational bisection; explicit grids retained for reproducible runs."""
from dataclasses import dataclass
import sympy as sp
from contractive_tool.errors import AnalysisError


class ContractionBisection:
    """Search a monotone feasibility oracle without evaluating c=0 or c=1.

Only verified feasibility tightens the upper endpoint. An infeasible response
is a solver/encoding observation, not a proof of polynomial nonexistence.
An inconclusive response leaves both endpoints unchanged and probes toward the
upper endpoint. Previously inconclusive points are skipped, not treated as
infeasible. Every probe counts against the same per-degree budget.
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
        self.next_probe = None
        self.tested = set()
        self.pending_reason = None

    def candidates(self):
        for _ in range(self.max_steps):
            if self.stop_reason:
                return
            candidate = self.next_probe if self.next_probe is not None else (self.lower+self.upper)/2
            reason = 'unknown_upper_probe' if self.next_probe is not None else 'interval_bisection'
            self.next_probe = None
            # A midpoint can revisit an unknown after either endpoint changes.
            # Explore the open gap on its upper side without moving the lower
            # endpoint or asserting anything about the skipped point.
            while candidate in self.tested:
                candidate = (candidate+self.upper)/2
                reason = 'skip_tested_point'
            self.pending = candidate
            self.pending_reason = reason
            yield self.pending
            if self.pending is not None:
                raise AnalysisError('Bisection requires feedback before the next candidate')

    def observe(self, status):
        if self.pending is None:
            raise AnalysisError('No pending contraction candidate')
        if status not in ('proved','infeasible','unknown'):
            raise AnalysisError('Invalid bisection oracle status')
        c = self.pending
        self.tested.add(c)
        before = [str(self.lower),str(self.upper)]
        if status == 'proved':
            self.upper = self.best_verified = c
        elif status == 'infeasible':
            self.lower = c
        else:
            self.next_probe = (c+self.upper)/2
        self.history.append({'iteration':len(self.history)+1,'c':str(c),'status':status,
                             'proposal':self.pending_reason,
                             'interval_before':before,
                             'interval_after':[str(self.lower),str(self.upper)]})
        self.pending = None
        if len(self.history) == self.max_steps and self.stop_reason is None:
            self.stop_reason = 'max_c_steps'

    def to_data(self):
        return {'method':'bisection','max_steps':self.max_steps,
                'unknown_policy':'preserve_interval_probe_upper_skip_tested',
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
