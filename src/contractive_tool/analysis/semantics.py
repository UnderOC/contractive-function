"""Source-derived initialization and exact, conservative invariant evidence."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import sympy as sp
from sympy.solvers.simplex import lpmin, InfeasibleLPError, UnboundedLPError

from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.ast import BooleanConstant, BoolBinary, BoolUnary, Compare
from contractive_tool.positivity.domains import predicate_regions
from contractive_tool.positivity.ir import BasicSet


def evaluate_predicate(expr, values):
    if isinstance(expr, BooleanConstant):
        return expr.value
    if isinstance(expr, BoolUnary):
        return not evaluate_predicate(expr.operand, values)
    if isinstance(expr, BoolBinary):
        left, right = evaluate_predicate(expr.left, values), evaluate_predicate(expr.right, values)
        return left and right if expr.operator == 'and' else left or right
    if isinstance(expr, Compare):
        a = arithmetic_to_symbolic(expr.left).subs(values, simultaneous=True)
        b = arithmetic_to_symbolic(expr.right).subs(values, simultaneous=True)
        if a.free_symbols or b.free_symbols:
            raise AnalysisError('Initialization reads a variable without a source-defined value')
        return bool({'<': lambda:a<b, '<=':lambda:a<=b, '>':lambda:a>b,
                     '>=':lambda:a>=b, '=':lambda:a==b, '!=':lambda:a!=b}[expr.operator]())
    raise AnalysisError('Unsupported state predicate')


def intersect(a, b):
    return BasicSet(a.variables, a.generators+b.generators, a.equalities+b.equalities)


@lru_cache(maxsize=8192)
def prove_nonnegative(domain, h):
    """Find a rational Farkas identity; independently check every returned coefficient.

    Also accepts polynomial generators when a constant-multiplier identity exists.
    Failure means unknown, never that the original implication is false.
    """
    h = sp.expand(h)
    if h.is_Rational and h >= 0:
        return {'method':'constant', 'value':str(h)}
    generators = (sp.Integer(1),)+domain.generators
    free = domain.equalities
    weights = tuple(sp.Dummy(f'f{i}') for i in range(len(generators)+len(free)))
    rhs = sum((w*g for w,g in zip(weights, generators+free)), sp.Integer(0))
    difference = sp.expand(h-rhs)
    coeffs = sp.Poly(difference, *domain.variables).coeffs() if domain.variables else [difference]
    constraints = [sp.Eq(c,0) for c in coeffs]
    constraints += [w>=0 for w in weights[:len(generators)]]
    if any(c is sp.false for c in constraints):
        return None
    constraints = [c for c in constraints if c is not sp.true]
    try:
        _, solution = lpmin(sp.Integer(0), constraints)
    except (InfeasibleLPError, UnboundedLPError, ValueError):
        return None
    values = {w:sp.sympify(solution.get(w,sp.Integer(0))) for w in weights}
    if any(v.is_Rational is not True for v in values.values()):
        return None
    if any(values[w]<0 for w in weights[:len(generators)]):
        return None
    if sp.expand(difference.xreplace(values)) != 0:
        return None
    return {'method':'exact_farkas_identity', 'conclusion':str(h),
            'domain':domain.to_data(), 'nonnegative_weights':[str(values[w]) for w in weights[:len(generators)]],
            'equality_weights':[str(values[w]) for w in weights[len(generators):]]}


def require_nonnegative(domain, h, label):
    proof = prove_nonnegative(domain, sp.expand(h))
    if proof is None:
        # A certified contradiction makes the implication vacuous.
        empty = prove_nonnegative(domain, sp.Integer(-1))
        if empty is not None:
            return {'method':'empty_domain', 'contradiction':empty}
        raise AnalysisError(f'Cannot certify {label}; supply stronger source invariants or use a supported domain')
    return proof


@dataclass
class ProgramEvidence:
    start: str
    initial: dict
    prefix: list
    locations: tuple[str,...]
    domains: dict
    group_domains: dict
    proofs: list

    def to_data(self):
        return {'status':'proved', 'method':'exact_initialization_and_inductive_domain_certificates',
                'initial_location':self.start, 'initial':{str(k):str(v) for k,v in self.initial.items()},
                'initialization_steps':len(self.prefix), 'initialization_trace':self.prefix,
                'locations':list(self.locations), 'domains':{l:[d.to_data() for d in ds] for l,ds in self.domains.items()},
                'strict_invariant_policy':'inductive_closed_overapproximation', 'proofs':self.proofs}


def prepare_program(cfg):
    variables = tuple(sp.Symbol(name) for name in cfg.symbols.program_variables)
    terminals = {cfg.normal_terminal, cfg.failure_terminal}
    values, trace, seen = {}, [], set()
    current = cfg.initial_location
    # Only straight-line deterministic initialization is executed. No file-name recognition.
    while cfg.locations[current].kind in {'assign','skip'}:
        if current in seen:
            raise AnalysisError('Cyclic initialization is unsupported')
        seen.add(current)
        if not evaluate_predicate(cfg.locations[current].invariant, values):
            raise AnalysisError(f'Initialization violates invariant at {current}')
        groups = cfg.outgoing(current)
        if len(groups)!=1 or len(groups[0].branches)!=1:
            raise AnalysisError('Initialization must be deterministic')
        group, branch = groups[0], groups[0].branches[0]
        if branch.update.samples or arithmetic_to_symbolic(branch.probability)!=1:
            raise AnalysisError('Random initialization is not implemented')
        if not evaluate_predicate(group.guard,values):
            raise AnalysisError('Initialization is blocked')
        update = {sp.Symbol(name):arithmetic_to_symbolic(expr).subs(values,simultaneous=True)
                  for name,expr in branch.update.assignments.items()}
        if any(v.is_Rational is not True for v in update.values()):
            raise AnalysisError('Source must initialize variables with exact deterministic values')
        values.update(update)
        trace.append({'location':current, 'transition':group.id, 'destination':branch.destination,
                      'values':{str(k):str(v) for k,v in values.items()}})
        current = branch.destination
    if set(values)!=set(variables):
        missing = sorted(str(x) for x in set(variables)-set(values))
        raise AnalysisError(f'Program must initialize all state variables before control flow; missing {missing}')
    if not evaluate_predicate(cfg.locations[current].invariant,values):
        raise AnalysisError(f'Initial control location invariant is false at {current}')
    reachable, pending = set(), [current]
    while pending:
        location = pending.pop()
        if location in reachable:
            continue
        reachable.add(location)
        if location not in terminals:
            pending.extend(b.destination for g in cfg.outgoing(location) for b in g.branches)
    if any(cfg.locations[l].kind=='assume' for l in reachable):
        raise AnalysisError('Blocked/conditional assume semantics is not implemented by this solver')
    domains = {l:predicate_regions(cfg.locations[l].invariant, variables) for l in sorted(reachable)}
    group_domains, proofs = {}, []
    for location in sorted(reachable-terminals):
        outgoing = cfg.outgoing(location)
        if cfg.locations[location].kind not in {'assign','skip','sample','while','if','probabilistic','conditional','assert','refute'}:
            raise AnalysisError(f'Unsupported control-flow kind {cfg.locations[location].kind}')
        if not outgoing:
            raise AnalysisError('Nonterminal deadlock is unsupported')
        for group in outgoing:
            ds = [intersect(a,b) for a in domains[location] for b in predicate_regions(group.guard,variables)]
            group_domains[group.id] = ds
            for di,domain in enumerate(ds):
                probabilities = [arithmetic_to_symbolic(b.probability) for b in group.branches]
                if sp.expand(sum(probabilities)-1)!=0:
                    raise AnalysisError('Grouped probabilities do not sum identically to one')
                for bi,branch in enumerate(group.branches):
                    if branch.update.samples:
                        raise AnalysisError('Random assignments require support-invariance certificates; not implemented')
                    proof = require_nonnegative(domain, probabilities[bi], f'probability of {group.id}')
                    proofs.append({'transition':group.id,'region':di,'branch':bi,'kind':'probability','proof':proof})
                    update = {sp.Symbol(n):arithmetic_to_symbolic(e) for n,e in branch.update.assignments.items()}
                    targets = domains[branch.destination]
                    # Sufficient disjunctive inclusion: prove containment in one complete target region.
                    accepted = None
                    for target in targets:
                        requirements = target.generators + tuple(v for e in target.equalities for v in (e,-e))
                        checks = []
                        try:
                            for h in requirements:
                                checks.append(require_nonnegative(domain, h.subs(update,simultaneous=True),
                                                                  f'invariant at {branch.destination}'))
                        except AnalysisError:
                            continue
                        accepted = checks
                        break
                    if accepted is None:
                        raise AnalysisError(f'Cannot certify inductive invariant across {group.id} to {branch.destination}')
                    proofs.append({'transition':group.id,'region':di,'branch':bi,'kind':'invariant_preservation','proofs':accepted})
    return ProgramEvidence(current, values, trace, tuple(sorted(reachable)), domains, group_domains, proofs)
