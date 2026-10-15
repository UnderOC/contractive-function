"""Source-derived initialization and exact, conservative invariant evidence."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import sympy as sp
from sympy.solvers.simplex import lpmin, InfeasibleLPError, UnboundedLPError

from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.ast import BooleanConstant, BoolBinary, BoolUnary, Compare
from contractive_tool.positivity.domains import eliminate_fixed_equalities, predicate_regions
from contractive_tool.positivity.ir import BasicSet
from contractive_tool.probability import IndependentRandomModel, distribution_from_ast


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
    variables = tuple(dict.fromkeys(a.variables + b.variables))
    return BasicSet(variables, a.generators+b.generators, a.equalities+b.equalities)


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
    original = sp.expand(h)
    reduced_domain, reduced = eliminate_fixed_equalities(domain, original)
    proof = prove_nonnegative(reduced_domain, reduced)
    if proof is None:
        # A certified contradiction makes the implication vacuous.
        empty = prove_nonnegative(reduced_domain, sp.Integer(-1))
        if empty is not None:
            return {'method':'empty_domain', 'contradiction':empty}
        raise AnalysisError(f'Cannot certify {label}; supply stronger source invariants or use a supported domain')
    if domain.equalities:
        return {'method':'exact_affine_equality_elimination', 'conclusion':str(original),
                'reduced_conclusion':str(reduced), 'reduced_domain':reduced_domain.to_data(),
                'proof':proof}
    return proof


def _support_product(domains, symbol, distribution, *, max_regions=128):
    regions = distribution.support(symbol)
    if len(domains) * len(regions) > max_regions:
        raise AnalysisError('Random support DNF exceeds region budget')
    result = []
    for domain in domains:
        if symbol in domain.variables:
            raise AnalysisError(f'Duplicate fresh random symbol {symbol}')
        variables = domain.variables + (symbol,)
        for region in regions:
            result.append(BasicSet(variables, domain.generators + region.generators,
                                   domain.equalities + region.equalities))
    return result


def _predicate_requirements(predicate, variables):
    return predicate_regions(predicate, variables)


def _certify_initialized_predicate(predicate, values, support_domains, variables, label):
    """Prove a source predicate for every supported symbolic initialization state."""
    if all(not domain.variables for domain in support_domains):
        if not evaluate_predicate(predicate, values):
            raise AnalysisError(f'{label} is false')
        return [{'method':'exact_evaluation'}]
    targets = _predicate_requirements(predicate, variables)
    evidence = []
    for source_index, source in enumerate(support_domains):
        accepted = None
        for target_index, target in enumerate(targets):
            requirements = target.generators + tuple(
                value for equality in target.equalities for value in (equality, -equality))
            checks = []
            try:
                for requirement in requirements:
                    conclusion = sp.expand(requirement.subs(values, simultaneous=True))
                    unknown = conclusion.free_symbols - set(source.variables)
                    if unknown:
                        names = ', '.join(sorted(str(item) for item in unknown))
                        raise AnalysisError(
                            f'Initialization reads a variable without a source-defined value: {names}')
                    checks.append(require_nonnegative(source, conclusion, label))
            except AnalysisError:
                continue
            accepted = {'support_region':source_index, 'predicate_region':target_index,
                        'support_domain':source.to_data(), 'proofs':checks}
            break
        if accepted is None:
            raise AnalysisError(f'Cannot certify {label} on the initialization support')
        evidence.append(accepted)
    return evidence


def _branch_support_domains(domain, branch):
    domains = [domain]
    sample_names = set()
    for sample in branch.update.samples:
        if sample.symbol in sample_names:
            raise AnalysisError(f'Duplicate fresh random symbol {sample.symbol}')
        sample_names.add(sample.symbol)
        domains = _support_product(domains, sp.Symbol(sample.symbol),
                                   distribution_from_ast(sample.distribution))
    return domains


@dataclass
class ProgramEvidence:
    start: str
    initial: dict
    prefix: list
    locations: tuple[str,...]
    domains: dict
    group_domains: dict
    proofs: list
    initial_random_model: IndependentRandomModel
    initial_support: tuple[BasicSet,...]

    def to_data(self):
        return {'status':'proved', 'method':'exact_initialization_and_inductive_domain_certificates',
                'initial_location':self.start, 'initial':{str(k):str(v) for k,v in self.initial.items()},
                'initialization_steps':len(self.prefix), 'initialization_trace':self.prefix,
                'initial_random_symbols':list(self.initial_random_model.symbols),
                'initial_support':[domain.to_data() for domain in self.initial_support],
                'locations':list(self.locations), 'domains':{l:[d.to_data() for d in ds] for l,ds in self.domains.items()},
                'strict_invariant_policy':'inductive_closed_overapproximation', 'proofs':self.proofs}


def prepare_program(cfg):
    variables = tuple(sp.Symbol(name) for name in cfg.symbols.program_variables)
    terminals = {cfg.normal_terminal, cfg.failure_terminal}
    values, trace, seen = {}, [], set()
    initialization_domains = [BasicSet(())]
    initialization_distributions = {}
    initialization_sample_count = 0
    initialization_symbol_names = (
        set(cfg.symbols.program_variables) | set(cfg.symbols.declared_random_variables))
    proofs = []
    current = cfg.initial_location
    # Execute a straight-line initialization prefix symbolically. Each sample occurrence
    # receives a distinct symbol, including repeated uses of a declared random variable.
    while cfg.locations[current].kind in {'assign','sample','skip'}:
        if current in seen:
            raise AnalysisError('Cyclic initialization is unsupported')
        seen.add(current)
        invariant_proof = _certify_initialized_predicate(
            cfg.locations[current].invariant, values, initialization_domains, variables,
            f'initialization invariant at {current}')
        proofs.append({'location':current, 'kind':'initialization_invariant',
                       'proofs':invariant_proof})
        groups = cfg.outgoing(current)
        if len(groups)!=1 or len(groups[0].branches)!=1:
            raise AnalysisError('Initialization control flow must be straight-line')
        group, branch = groups[0], groups[0].branches[0]
        if sp.expand(arithmetic_to_symbolic(branch.probability)-1)!=0:
            raise AnalysisError('Initialization control flow must have probability one')
        guard_proof = _certify_initialized_predicate(
            group.guard, values, initialization_domains, variables,
            f'initialization guard of {group.id}')
        proofs.append({'transition':group.id, 'kind':'initialization_guard',
                       'proofs':guard_proof})
        sample_replacements = {}
        sample_rows = []
        for sample in branch.update.samples:
            if sp.Symbol(sample.symbol) in sample_replacements:
                raise AnalysisError(f'Duplicate fresh random symbol {sample.symbol}')
            while True:
                initialization_sample_count += 1
                fresh = sp.Symbol(f'__initial_sample_{initialization_sample_count}')
                if fresh.name not in initialization_symbol_names:
                    break
            initialization_symbol_names.add(fresh.name)
            distribution = distribution_from_ast(sample.distribution)
            sample_replacements[sp.Symbol(sample.symbol)] = fresh
            initialization_distributions[fresh.name] = distribution
            initialization_domains = _support_product(
                initialization_domains, fresh, distribution)
            sample_rows.append({'source_symbol':sample.symbol, 'fresh_symbol':fresh.name,
                                'distribution':sample.distribution.name,
                                'arguments':[str(arithmetic_to_symbolic(argument))
                                             for argument in sample.distribution.arguments]})
        update = {}
        for name, expr in branch.update.assignments.items():
            value = arithmetic_to_symbolic(expr).subs(sample_replacements, simultaneous=True)
            value = sp.expand(value.subs(values, simultaneous=True))
            unresolved = value.free_symbols & set(variables)
            if unresolved:
                names = ', '.join(sorted(str(item) for item in unresolved))
                raise AnalysisError(
                    f'Initialization reads a variable without a source-defined value: {names}')
            update[sp.Symbol(name)] = value
        values.update(update)
        trace.append({'location':current, 'transition':group.id, 'destination':branch.destination,
                      'samples':sample_rows,
                      'values':{str(k):str(v) for k,v in values.items()},
                      'support_regions':len(initialization_domains)})
        current = branch.destination
    if set(values)!=set(variables):
        missing = sorted(str(x) for x in set(variables)-set(values))
        raise AnalysisError(f'Program must initialize all state variables before control flow; missing {missing}')
    initial_invariant_proof = _certify_initialized_predicate(
        cfg.locations[current].invariant, values, initialization_domains, variables,
        f'Initial control location invariant at {current}')
    proofs.append({'location':current, 'kind':'initial_control_invariant',
                   'proofs':initial_invariant_proof})
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
    group_domains = {}
    for location in sorted(reachable-terminals):
        outgoing = cfg.outgoing(location)
        if cfg.locations[location].kind not in {'assign','skip','sample','while','if','branch','probabilistic','conditional','assert','refute'}:
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
                    proof = require_nonnegative(domain, probabilities[bi], f'probability of {group.id}')
                    proofs.append({'transition':group.id,'region':di,'branch':bi,'kind':'probability','proof':proof})
                    update = {sp.Symbol(n):arithmetic_to_symbolic(e) for n,e in branch.update.assignments.items()}
                    targets = domains[branch.destination]
                    support_cases = _branch_support_domains(domain, branch)
                    accepted_cases = []
                    for support_index, support_domain in enumerate(support_cases):
                        # Sufficient disjunctive inclusion: prove containment in one
                        # complete target region for every exact support component.
                        accepted = None
                        for target_index, target in enumerate(targets):
                            requirements = target.generators + tuple(
                                value for equality in target.equalities
                                for value in (equality,-equality))
                            checks = []
                            try:
                                for h in requirements:
                                    checks.append(require_nonnegative(
                                        support_domain, h.subs(update,simultaneous=True),
                                        f'invariant at {branch.destination}'))
                            except AnalysisError:
                                continue
                            accepted = {'support_region':support_index,
                                        'target_region':target_index,
                                        'support_domain':support_domain.to_data(),
                                        'proofs':checks}
                            break
                        if accepted is None:
                            raise AnalysisError(
                                f'Cannot certify inductive invariant across {group.id} '
                                f'to {branch.destination} on random support region {support_index}')
                        accepted_cases.append(accepted)
                    proofs.append({'transition':group.id,'region':di,'branch':bi,
                                   'kind':'invariant_preservation',
                                   'random_samples':[
                                       {'symbol':sample.symbol,
                                        'distribution':sample.distribution.name,
                                        'arguments':[str(arithmetic_to_symbolic(argument))
                                                     for argument in sample.distribution.arguments]}
                                       for sample in branch.update.samples],
                                   'proofs':accepted_cases})
    model = IndependentRandomModel(dict(initialization_distributions))
    return ProgramEvidence(current, values, trace, tuple(sorted(reachable)), domains,
                           group_domains, proofs, model, tuple(initialization_domains))
