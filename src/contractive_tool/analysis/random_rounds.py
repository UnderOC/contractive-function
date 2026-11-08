"""Compose a finite-random loop round before taking any expectation.

Initial scope: deterministic initialization, acyclic bodies with straight-line
assignments, independent finite samples and constant probabilistic branches.
State-dependent body guards are compiled to covering regions with complete raw
successor distributions. Unused samples on probabilistic paths may be drawn in
advance because all laws are constant. Fresh-sample guards remain subject to
the symbolic kernel's existing support checks.
"""
from dataclasses import dataclass
from hashlib import sha256
from itertools import product, combinations_with_replacement
from pathlib import Path

import sympy as sp

from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.analysis.semantics import prepare_program, require_nonnegative, prove_nonnegative, intersect
from contractive_tool.analysis.symbolic_rounds import prepare_symbolic_round_kernel
from contractive_tool.analysis.guard_regions import GuardRegion, guard_regions
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.ast import BooleanConstant
from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.semantic import check_program
from contractive_tool.probability.distributions import distribution_from_ast, BernoulliDistribution, FiniteDiscreteDistribution
from contractive_tool.probability.fractional_moments import FiniteLaw, rational
from contractive_tool.positivity.ir import BasicSet
from contractive_tool.positivity.domains import eliminate_fixed_equalities


def _invariant_prover(domain, expression, label):
    try:
        return require_nonnegative(domain, expression, label)
    except AnalysisError:
        reduced, h = eliminate_fixed_equalities(domain, sp.expand(expression))
        # Positive coefficients after translating certified coordinate lower
        # bounds give a direct exact product identity, avoiding a degenerate LP.
        lower = {}
        for v in reduced.variables:
            candidates = []
            for g in reduced.generators:
                if g.free_symbols == {v} and sp.degree(g, v) == 1:
                    a, b = sp.diff(g, v), g.subs(v, 0)
                    if a.is_Rational and b.is_Rational and a > 0:
                        candidates.append(-b/a)
            if candidates:
                lower[v] = max(candidates)
        if h.free_symbols <= set(lower) and h.free_symbols:
            variables = tuple(sorted(h.free_symbols, key=str))
            shifted = sp.Poly(h.subs({v: v+lower[v] for v in variables}, simultaneous=True), *variables)
            if all(c.is_Rational and c >= 0 for c in shifted.coeffs()):
                identity = sum(c*sp.prod((v-lower[v])**p for v, p in zip(variables, powers))
                               for powers, c in shifted.terms())
                if sp.expand(identity-h) == 0:
                    return {'method': 'exact_shifted_nonnegative_monomials',
                        'conclusion': str(expression), 'reduced_conclusion': str(h),
                        'reduced_domain': reduced.to_data(),
                        'lower_bounds': {str(v): str(lower[v]) for v in variables},
                        'identity': str(identity)}
        degree = int(sp.Poly(h, *reduced.variables).total_degree()) if reduced.variables else 0
        products = list(reduced.generators)
        witnesses = [[i] for i in range(len(products))]
        for size in range(2, min(degree, 4)+1):
            for indices in combinations_with_replacement(range(len(reduced.generators)), size):
                if len(products) >= 512:
                    raise AnalysisError('Cauchy invariant product budget exceeded')
                p = sp.expand(sp.prod(reduced.generators[i] for i in indices))
                products.append(p)
                witnesses.append(list(indices))
        proof = prove_nonnegative(BasicSet(reduced.variables, tuple(products), reduced.equalities), h)
        if proof is None:
            raise AnalysisError(f'Cannot certify {label} with bounded exact generator products')
        return {'method': 'exact_nonnegative_generator_products', 'conclusion': str(expression),
                'reduced_conclusion': str(h), 'reduced_domain': reduced.to_data(),
                'product_indices': witnesses, 'proof': proof}


@dataclass
class RoundPiece:
    domain: BasicSet
    guard: GuardRegion
    update: dict

    def to_data(self):
        return {'domain': self.domain.to_data(), 'guard': self.guard.to_data(),
                'update': {str(k): str(v) for k, v in self.update.items()}}


@dataclass
class RoundRandomRepresentation:
    variables: tuple
    domains: tuple
    update: dict
    initial: dict
    law: FiniteLaw
    initial_active: bool
    evidence: dict
    pieces: tuple = ()

    def to_data(self):
        data = {'variables': list(map(str, self.variables)),
                'domains': [d.to_data() for d in self.domains],
                'update': {str(k): str(v) for k, v in self.update.items()},
                'initial': {str(k): str(v) for k, v in self.initial.items()},
                'law': self.law.to_data(), 'initial_active': self.initial_active,
                'evidence': self.evidence}
        if self.pieces:
            data['pieces'] = [p.to_data() for p in self.pieces]
        return data

    def domain_updates(self):
        return (tuple((p.domain, p.update) for p in self.pieces) if self.pieces
                else tuple((d, self.update) for d in self.domains))

    def resolve_basis(self, eta, basis=None):
        if basis is not None:
            return tuple(basis)
        if self.pieces:
            # A categorical law has a compact exact indicator basis; expanding
            # into monomials would produce large cancelling coefficients.
            return _indicators(self.law.symbols[0], len(self.law.atoms))
        return self.decompose(eta)[2]

    def decompositions(self, eta, basis=None):
        basis = self.resolve_basis(eta, basis)
        return tuple((domain, *self._decompose(eta, update, basis))
                     for domain, update in self.domain_updates())

    def decompose(self, eta, basis=None):
        if self.pieces:
            raise AnalysisError('Piecewise rounds require region-wise decompositions')
        return self._decompose(eta, self.update, basis)

    def _decompose(self, eta, update, basis):
        numerator = sp.expand(eta.subs(update, simultaneous=True))
        randoms = self.law.symbols
        if self.pieces:
            # Interpolate eta(F) on the *finite support*, rather than requiring
            # high-degree products of indicator polynomials off that support.
            numerator = sp.expand(sum(weight*numerator.subs(dict(zip(randoms, values)), simultaneous=True)
                for weight, (values, _) in zip(_indicators(randoms[0], len(self.law.atoms)), self.law.atoms)))
        if basis is None:
            basis = (tuple(sp.prod(r**e for r, e in zip(randoms, powers))
                           for powers, _ in sp.Poly(numerator, *randoms).terms())
                     if randoms else (sp.Integer(1),))
        basis = tuple(sp.expand(sp.sympify(b)) for b in basis)
        if not basis or any(b.free_symbols-set(randoms) for b in basis):
            raise AnalysisError('Basis must consist of polynomials in random symbols only')
        # Match in random variables, with state/template coefficients untouched.
        if not randoms:
            if len(basis) != 1 or basis[0] == 0:
                raise AnalysisError('Deterministic rounds need one nonzero constant basis element')
            q = (sp.expand(numerator/rational(basis[0])),)
        else:
            polys = [sp.Poly(b, *randoms) for b in basis]
            target = sp.Poly(numerator, *randoms)
            powers = sorted(set(target.monoms()).union(*(set(p.monoms()) for p in polys)))
            matrix = sp.Matrix([[rational(p.coeff_monomial(m)) for p in polys] for m in powers])
            values = sp.Matrix([target.coeff_monomial(m) for m in powers])
            try:
                solution, parameters = matrix.gauss_jordan_solve(values)
            except ValueError as error:
                raise AnalysisError('Random basis does not span the successor polynomial') from error
            if parameters.rows:
                raise AnalysisError('Random basis must be linearly independent')
            q = tuple(map(sp.expand, solution))
        if sp.expand(numerator-sum(a*b for a, b in zip(q, basis))) != 0:
            raise AnalysisError('Random decomposition identity failed')
        return numerator, q, basis


def _indicators(symbol, count):
    return tuple(sp.expand(sp.prod((symbol-j)/sp.Integer(i-j)
                                  for j in range(count) if j != i)) for i in range(count))


def _piecewise_updates(kernel, evidence, max_atoms, max_nodes, max_cases):
    """Compose distributions before expectation, refining random siblings.

    A case is a covering guard plus a *whole* conditional distribution, never
    one probabilistic path. Overlapping Boolean DNF covers are not added.
    Strict predicates are pulled back before proof-domain closure.
    """
    cfg, variables = kernel.cfg, kernel.variables
    whole = GuardRegion(variables)
    identity = tuple(variables)
    cache, visits = {}, 0

    def compact(outcomes):
        merged = {}
        for probability, update in outcomes:
            if probability:
                merged[update] = merged.get(update, sp.Integer(0))+probability
        if len(merged) > max_atoms:
            raise AnalysisError('Piecewise random support exceeds atom budget')
        return tuple((p, update) for update, p in merged.items())

    def branch_updates(branch):
        draws = [(sp.Integer(1), {})]
        for sample in branch.update.samples:
            distribution = distribution_from_ast(sample.distribution)
            if isinstance(distribution, BernoulliDistribution):
                atoms = ((0, 1-distribution.probability), (1, distribution.probability))
            elif isinstance(distribution, FiniteDiscreteDistribution):
                atoms = tuple(zip(distribution.values, distribution.probabilities))
            else:
                raise AnalysisError('Cauchy search currently requires finite discrete samples')
            if len(draws)*len(atoms) > max_atoms:
                raise AnalysisError('Piecewise random support exceeds atom budget')
            draws = [(p*rational(weight), {**sub, sp.Symbol(sample.symbol): rational(value)})
                     for p, sub in draws for value, weight in atoms if weight]
        for probability, sub in draws:
            yield probability, {sp.Symbol(name): sp.expand(arithmetic_to_symbolic(expr).subs(sub, simultaneous=True))
                                for name, expr in branch.update.assignments.items()}

    def group_cases(group):
        branches = [(b, rational(arithmetic_to_symbolic(b.probability))) for b in group.branches]
        if any(p < 0 for _, p in branches) or sum(p for _, p in branches) != 1:
            raise AnalysisError('Branch probabilities must be constant nonnegative rationals summing to one')
        combined = [(whole, ())]
        for branch, probability in branches:
            if not probability:
                continue
            children = node_cases(branch.destination)
            for sample_p, updates in branch_updates(branch):
                pulled = []
                for guard, outcomes in children:
                    region = guard.substitute(updates)
                    if region is not None:
                        pulled.append((region, tuple((probability*sample_p*p,
                            tuple(sp.expand(v.subs(updates, simultaneous=True)) for v in update))
                            for p, update in outcomes)))
                if len(combined)*len(pulled) > max_cases:
                    raise AnalysisError('Piecewise random round case budget exceeded')
                combined = list(dict.fromkeys((region, compact(a_out+b_out))
                    for a, a_out in combined for b, b_out in pulled
                    if (region := a.intersect(b)) is not None))
        guards = guard_regions(group.guard, variables, max_regions=max_cases)
        if len(guards)*len(combined) > max_cases:
            raise AnalysisError('Piecewise random round guard budget exceeded')
        return list(dict.fromkeys((region, outcomes) for g in guards for d, outcomes in combined
                                 if (region := g.intersect(d)) is not None))

    def node_cases(location):
        nonlocal visits
        visits += 1
        if visits > max_nodes:
            raise AnalysisError('Piecewise random round graph budget exceeded')
        if location == kernel.header:
            return [(whole, ((sp.Integer(1), identity),))]
        if location not in cache:
            cases = [case for group in cfg.outgoing(location) for case in group_cases(group)]
            if len(cases) > max_cases:
                raise AnalysisError('Piecewise random round case budget exceeded')
            cache[location] = cases
        return cache[location]

    cases = group_cases(kernel.entry)
    if not cases:
        raise AnalysisError('No active piecewise round regions')
    # Couple regional finite laws by the union of their rational CDF breakpoints.
    # This preserves every marginal exactly without a product over regions.
    cuts = {sp.Integer(0), sp.Integer(1)}
    for _, outcomes in cases:
        cumulative = sp.Integer(0)
        for probability, _ in outcomes:
            cumulative += probability
            cuts.add(cumulative)
        if cumulative != 1:
            raise AnalysisError('Regional probabilities must sum exactly to one')
    cuts = sorted(cuts)
    if len(cuts)-1 > max_atoms:
        raise AnalysisError('Common piecewise random support exceeds atom budget')
    name = '__cauchy_region_r'
    used = set(cfg.symbols.program_variables) | set(cfg.symbols.declared_random_variables)
    while name in used:
        name += '_'
    symbol = sp.Symbol(name)
    atoms = tuple(((sp.Integer(i),), right-left) for i, (left, right) in enumerate(zip(cuts, cuts[1:])))
    law = FiniteLaw((symbol,), atoms).validate()
    indicators = _indicators(symbol, len(atoms))
    pieces = []
    for guard, outcomes in cases:
        assigned = []
        for left, right in zip(cuts, cuts[1:]):
            midpoint, cumulative = (left+right)/2, sp.Integer(0)
            for probability, update in outcomes:
                cumulative += probability
                if midpoint < cumulative:
                    assigned.append(update)
                    break
        update = {v: sp.expand(sum(weight*values[i] for weight, values in zip(indicators, assigned)))
                  for i, v in enumerate(variables)}
        for invariant in evidence.domains[kernel.header]:
            pieces.append(RoundPiece(intersect(invariant, guard.closure()), guard, update))
    if len(pieces) > max_cases:
        raise AnalysisError('Piecewise invariant cover exceeds case budget')
    return tuple(pieces), law


def prepare_random_round(source, *, max_atoms=256, max_nodes=4096, max_cases=256):
    source = Path(source).resolve()
    cfg = build_cfg(check_program(parse_file(source)))
    if cfg.failure_terminal is None:
        raise AnalysisError('Source needs assert/refute; append refute true for loop survival')
    evidence = prepare_program(cfg, invariant_prover=_invariant_prover)
    if evidence.initial_random_model.symbols:
        raise AnalysisError('Cauchy search currently requires deterministic initialization')
    kernel = prepare_symbolic_round_kernel(cfg, evidence, max_nodes=max_nodes, max_cases=max_cases)
    variables = kernel.variables
    used_names = set(cfg.symbols.program_variables) | set(cfg.symbols.declared_random_variables)
    draws, visits = [], 0

    def fresh(atoms):
        index = len(draws)
        while f'__cauchy_r_{index}' in used_names:
            index += 1
        symbol = sp.Symbol(f'__cauchy_r_{index}')
        used_names.add(str(symbol))
        atoms = tuple((rational(v), rational(p)) for v, p in atoms if p != 0)
        FiniteLaw((symbol,), tuple(((v,), p) for v, p in atoms)).validate()
        if sp.prod(len(a) for _, a in draws)*len(atoms) > max_atoms:
            raise AnalysisError('Finite joint support exceeds atom budget')
        draws.append((symbol, atoms))
        return symbol

    def group_update(group, state, seen, *, entry=False):
        nonlocal visits
        visits += 1
        if visits > max_nodes:
            raise AnalysisError('Random round composition exceeds graph budget')
        if not entry and not (isinstance(group.guard, BooleanConstant) and group.guard.value):
            raise AnalysisError('Cauchy random rounds do not yet support conditional body guards')
        branches = [(b, rational(arithmetic_to_symbolic(b.probability))) for b in group.branches]
        if any(p < 0 for _, p in branches) or sum(p for _, p in branches) != 1:
            raise AnalysisError('Branch probabilities must be constant nonnegative rationals summing to one')
        branches = [(b, p) for b, p in branches if p]
        selector = fresh(tuple((sp.Integer(i), p) for i, (_, p) in enumerate(branches))) if len(branches)>1 else None
        outcomes = []
        for branch, probability in branches:
            replacements = {}
            for sample in branch.update.samples:
                distribution = distribution_from_ast(sample.distribution)
                if isinstance(distribution, BernoulliDistribution):
                    atoms = ((0, 1-distribution.probability), (1, distribution.probability))
                elif isinstance(distribution, FiniteDiscreteDistribution):
                    atoms = tuple(zip(distribution.values, distribution.probabilities))
                else:
                    raise AnalysisError('Cauchy search currently requires finite discrete samples')
                replacements[sp.Symbol(sample.symbol)] = fresh(atoms)
            updated = dict(state)
            updated.update({sp.Symbol(name): sp.expand(arithmetic_to_symbolic(expr)
                .subs(replacements, simultaneous=True).subs(state, simultaneous=True))
                for name, expr in branch.update.assignments.items()})
            location = branch.destination
            if location != kernel.header:
                if location in seen:
                    raise AnalysisError('Cyclic random round body')
                groups = cfg.outgoing(location)
                if len(groups) != 1:
                    raise AnalysisError('Cauchy random rounds do not yet support conditional body guards')
                updated = group_update(groups[0], updated, seen | {location})
            outcomes.append(updated)
        if selector is None:
            return outcomes[0]
        indicators = [sp.prod((selector-j)/sp.Integer(i-j) for j in range(len(outcomes)) if j != i)
                      for i in range(len(outcomes))]
        return {x: sp.expand(sum(w*outcome[x] for w, outcome in zip(indicators, outcomes))) for x in variables}

    # Retain the old representation/basis for already supported programs.
    seen = set()
    def has_conditionals(group):
        if group.id in seen:
            return False
        seen.add(group.id)
        for branch in group.branches:
            if arithmetic_to_symbolic(branch.probability) == 0 or branch.destination == kernel.header:
                continue
            children = cfg.outgoing(branch.destination)
            if len(children) != 1 or any(not isinstance(g.guard, BooleanConstant) or not g.guard.value for g in children):
                return True
            if has_conditionals(children[0]):
                return True
        return False
    pieces = ()
    if has_conditionals(kernel.entry):
        pieces, law = _piecewise_updates(kernel, evidence, max_atoms, max_nodes, max_cases)
        update = {}
    else:
        update = group_update(kernel.entry, dict(zip(variables, variables)), set(), entry=True)
        atoms = []
        for choices in product(*(a for _, a in draws)):
            atoms.append((tuple(v for v, _ in choices), sp.prod(p for _, p in choices)))
        law = FiniteLaw(tuple(r for r, _ in draws), tuple(atoms)).validate()
    active_regions = guard_regions(kernel.entry.guard, variables)
    active = any(all(p.subs(evidence.initial) >= 0 for p in d.generators)
                 and all(p.subs(evidence.initial) == 0 for p in d.equalities)
                 and all(p.subs(evidence.initial) > 0 for p in d.strict) for d in active_regions)
    return RoundRandomRepresentation(variables, tuple(evidence.group_domains[kernel.entry.id]),
        update, evidence.initial, law, bool(active),
        {'source': str(source), 'source_sha256': sha256(source.read_bytes()).hexdigest(),
         'domain_evidence': evidence.to_data(), 'round_evidence': kernel.to_data(),
         'composition': ('piecewise raw distributions; rational CDF coupling; exact guards before closure' if pieces
                         else 'polynomial updates before expectation; fresh constant-law draws'),
         'contraction': 'raw successor moment dominates killed survival moment'}, pieces)
