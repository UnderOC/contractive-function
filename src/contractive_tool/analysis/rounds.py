"""Exact loop-round kernels on a proved Boolean loop-head invariant.

Enumerating a complete inductive state domain is not bounded execution: the
resulting kernel and polynomial obligations apply to arbitrarily many rounds.
Unsupported domains/control flow are rejected, never silently approximated.
"""
from dataclasses import dataclass
from itertools import product
from math import comb

import sympy as sp

from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.analysis.goals import PolynomialProblem
from contractive_tool.analysis.semantics import evaluate_predicate
from contractive_tool.analysis.templates import PolynomialTemplateFactory
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.ir import BasicSet, Implication


@dataclass
class RoundKernel:
    header: str
    variables: tuple
    initial: tuple
    states: dict
    prefix_steps: int

    def to_data(self):
        lengths = {len(p['trace']) for row in self.states.values() if row['active'] for p in row['paths']}
        exit_lengths = {len(p['trace']) for row in self.states.values() if not row['active'] for p in row['paths']}
        clock = {'unit':'completed_loop_iterations', 'prefix_steps':self.prefix_steps,
                 'round_step_counts':sorted(lengths), 'exit_step_counts':sorted(exit_lengths)}
        if len(lengths) == len(exit_lengths) == 1:
            clock['pcfg_relation'] = f'T = {self.prefix_steps} + {next(iter(lengths))}*K + {next(iter(exit_lengths))}'
        return {'status':'proved', 'method':'exhaustive_inductive_boolean_round_kernel',
                'header':self.header, 'variables':[str(v) for v in self.variables],
                'initial':[int(v) for v in self.initial], 'domain':'Boolean states satisfying the original header invariant',
                'strict_guards':'evaluated exactly, without closure', 'clock':clock,
                'states':[{'state':list(s), **row} for s,row in self.states.items()]}


def prepare_round_kernel(cfg, evidence, *, max_states=256, max_paths=4096):
    """Prove coverage, probabilities, finite round length and Boolean closure.

The Boolean invariant is established from initialization and *all* one-round
images, not inferred from a real interval annotation or from variable names.
Sampling and cycles within a round currently need a different kernel compiler.
"""
    header = evidence.start
    if cfg.locations[header].kind != 'while':
        raise AnalysisError('Round compilation requires initialization followed by a loop')
    variables = tuple(sp.Symbol(n) for n in cfg.symbols.program_variables)
    if 2**len(variables) > max_states:
        raise AnalysisError('Boolean round state budget exceeded')
    initial = tuple(evidence.initial[v] for v in variables)
    if any(v not in (0, 1) for v in initial):
        raise AnalysisError('Boolean round compilation requires deterministic Boolean initialization')
    states = {s:{} for s in product((0,1), repeat=len(variables))
              if evaluate_predicate(cfg.locations[header].invariant, dict(zip(variables,s)))}
    if initial not in states:
        raise AnalysisError('Initial state is outside the proposed round invariant')
    terminals = {cfg.normal_terminal, cfg.failure_terminal}
    budget = 0

    def can_return(group):
        pending = [b.destination for b in group.branches]
        visited = set()
        while pending:
            location = pending.pop()
            if location == header:
                return True
            if location in visited or location in terminals:
                continue
            visited.add(location)
            pending.extend(b.destination for g in cfg.outgoing(location) for b in g.branches)
        return False

    # Identify the body's edge by CFG structure, independently of state values.
    # In particular an assertion inside the body must not be mistaken for the
    # loop's false-guard exit just because every enabled path terminates early.
    entries = [g for g in cfg.outgoing(header) if can_return(g)]
    if len(entries) != 1:
        raise AnalysisError('Cannot identify a unique loop-body entry for round compilation')
    entry = entries[0]

    def paths(location, values, probability, trace, seen):
        nonlocal budget
        budget += 1
        if budget > max_paths:
            raise AnalysisError('Round path expansion budget exceeded')
        if trace and (location == header or location in terminals):
            target = tuple(values[v] for v in variables)
            if location == header and target not in states:
                raise AnalysisError('Round update does not preserve the Boolean header invariant')
            return [{'destination':location, 'state':[str(v) for v in target],
                     'probability':str(probability), 'trace':trace}]
        if location in seen:
            raise AnalysisError('Nested/cyclic control flow within a round is unsupported')
        if cfg.locations[location].kind == 'assume':
            raise AnalysisError('Conditional assume is unsupported by round compilation')
        if not evaluate_predicate(cfg.locations[location].invariant, values):
            raise AnalysisError(f'Original invariant fails within round at {location}')
        enabled = [g for g in cfg.outgoing(location) if evaluate_predicate(g.guard, values)]
        if len(enabled) != 1:
            raise AnalysisError('Round guards must cover each state exactly once (no nondeterminism/deadlock)')
        group = enabled[0]
        probabilities = [arithmetic_to_symbolic(b.probability).subs(values, simultaneous=True)
                         for b in group.branches]
        if any(p.is_Rational is not True or p < 0 for p in probabilities) or sum(probabilities) != 1:
            raise AnalysisError('Invalid exact round branch probabilities')
        result = []
        for index, (branch, p) in enumerate(zip(group.branches, probabilities)):
            if p == 0:
                continue
            if branch.update.samples:
                raise AnalysisError('Sampled updates require a separate round kernel compiler')
            updated = dict(values)
            updated.update({sp.Symbol(n):sp.expand(arithmetic_to_symbolic(e).subs(values, simultaneous=True))
                            for n,e in branch.update.assignments.items()})
            edge = {'transition':group.id, 'branch':index, 'source':location,
                    'destination':branch.destination, 'probability':str(p)}
            result.extend(paths(branch.destination, updated, probability*p, trace+[edge], seen|{location}))
        return result

    for state in states:
        rows = paths(header, dict(zip(variables,state)), sp.Integer(1), [], set())
        active = evaluate_predicate(entry.guard, dict(zip(variables,state)))
        returns = {p['destination'] == header for p in rows}
        if returns != {active}:
            raise AnalysisError('Early exits inside a loop body need a killed round compiler')
        if sum(sp.Rational(p['probability']) for p in rows) != 1:
            raise AnalysisError('Round path probabilities do not sum to one')
        states[state] = {'active':active, 'paths':rows}
    return RoundKernel(header, variables, initial, states, len(evidence.prefix))


def make_round_problem(cfg, kernel, degree, c, max_decisions=20000):
    if not 0 < c < 1:
        raise AnalysisError('Contraction factor must be strictly between 0 and 1')
    if comb(len(kernel.variables)+degree,degree) > max_decisions:
        raise AnalysisError('Template coefficient budget exceeded before basis expansion')
    template = PolynomialTemplateFactory().instantiate(cfg, degree=degree, prefix='eta', locations=(kernel.header,))
    eta = template.expressions[kernel.header].expression
    at = {s:sp.expand(eta.subs(dict(zip(kernel.variables,s)), simultaneous=True)) for s in kernel.states}
    obligations = []
    for index,(state,row) in enumerate(kernel.states.items()):
        origin = {'location':kernel.header, 'state':dict(zip(map(str,kernel.variables),state)),
                  'kernel_evidence':'round_evidence.json'}
        def require(label, residual):
            obligations.append(Implication(f'round_{index}_{label}', BasicSet(()), sp.expand(residual),
                                           origin, ('round_survival',label)))
        if row['active']:
            require('normalization', at[state]-1)
            pre = sum((sp.Rational(p['probability'])*at[tuple(sp.Rational(v) for v in p['state'])]
                       for p in row['paths']), sp.Integer(0))
            require('contraction', c*at[state]-pre)
        else:
            require('completed_zero_lower', at[state])
            require('completed_zero_upper', -at[state])
    return PolynomialProblem('tailbound',degree,c,{kernel.header:eta},list(template.decisions),
                             at[kernel.initial],obligations,
                             {'rule':'round_survival', 'clock':kernel.to_data()['clock'],
                              'event':'K > n', 'time_unit':'completed_loop_iterations'})
