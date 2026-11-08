"""Exact invariant certificates with bounded SOS synthesis and solver-free replay."""
from itertools import combinations_with_replacement
import json
import time

import sympy as sp

from contractive_tool.analysis.semantics import prepare_program, require_nonnegative, prove_nonnegative
from contractive_tool.backends.cvxpy.verification import exact_psd, check_conic_values
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.base import EncodingLimits
from contractive_tool.positivity.domains import eliminate_fixed_equalities
from contractive_tool.positivity.ir import BasicSet, ConicModel
from contractive_tool.positivity.putinar import lower_sos


def elementary_proof(domain, expression, label):
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


METHOD = 'exact_invariant_sos'
LIMITS = EncodingLimits(max_products=32, max_psd_dimension=28, max_decisions=1500)


def _key(domain, h):
    return json.dumps([domain.to_data(), str(sp.expand(h))], sort_keys=True)


def quadratic_matrix(variables, h):
    """Unique rational matrix for h = [1,x]^T Q [1,x], including affine terms."""
    h = sp.expand(h)
    if h.free_symbols - set(variables):
        return None
    if variables:
        poly = sp.Poly(h, *variables)
        if poly.total_degree() > 2 or any(c.is_Rational is not True for c in poly.coeffs()):
            return None
    elif h.is_Rational is not True:
        return None
    zero = dict.fromkeys(variables, 0)
    matrix = sp.zeros(len(variables)+1)
    matrix[0, 0] = h.subs(zero)
    for i, x in enumerate(variables, 1):
        matrix[0, i] = matrix[i, 0] = sp.diff(h, x).subs(zero)/2
        for j, y in enumerate(variables, 1):
            matrix[i, j] = sp.diff(h, x, y)/2
    basis = sp.Matrix([1, *variables])
    if sp.expand((basis.T*matrix*basis)[0]-h) != 0:
        return None
    return matrix


def _quadratic_witness(domain, h):
    # Try a global quadratic, then a quadratic remainder after subtracting one
    # existing generator. Coefficient ratios cover scaled source annotations.
    candidates = [(None, sp.Integer(0))]
    for index, g in enumerate(domain.generators):
        ratios = {sp.Integer(1)}
        if domain.variables and g != 0:
            terms = sp.Poly(h, *domain.variables).as_dict()
            for powers, coefficient in sp.Poly(g, *domain.variables).terms():
                value = terms.get(powers, sp.Integer(0))/coefficient
                if value.is_Rational and value > 0:
                    ratios.add(value)
        candidates.extend((index, value) for value in sorted(ratios))
    for index, weight in candidates:
        remainder = h if index is None else sp.expand(h-weight*domain.generators[index])
        matrix = quadratic_matrix(domain.variables, remainder)
        if matrix is not None and exact_psd(matrix):
            return {'kind': 'quadratic_remainder', 'generator': index, 'weight': str(weight),
                    'matrix': [[str(v) for v in row] for row in matrix.tolist()]}
    return None


def _sos_model(domain, h, order):
    if type(order) is not int or not 1 <= order <= 2 or len(domain.generators) > LIMITS.max_products:
        raise AnalysisError('Invariant SOS encoding budget exceeded')
    # Keep decision symbols distinct from all source state symbols.
    prefix = '__invariant'
    while any(str(v).startswith(prefix) for v in domain.variables):
        prefix += '_'
    model = ConicModel([], sp.Integer(0))
    lower_sos(domain, h, model, prefix, order, LIMITS, domain.generators)
    model.to_data()
    return model


def check_invariant_certificate(domain, expression, certificate):
    """Rebuild from the source obligation; never trust a saved model alone."""
    try:
        original = sp.expand(expression)
        reduced, h = eliminate_fixed_equalities(domain, original)
        if (certificate['method'] != METHOD or certificate['domain'] != domain.to_data()
                or certificate['conclusion'] != str(original)
                or certificate['reduced_domain'] != reduced.to_data()
                or certificate['reduced_conclusion'] != str(h)):
            return False
        witness = certificate['witness']
        if witness['kind'] == 'quadratic_remainder':
            index, weight = witness['generator'], sp.Rational(witness['weight'])
            if weight < 0 or (index is None and weight != 0):
                return False
            if index is not None and (type(index) is not int or not 0 <= index < len(reduced.generators)):
                return False
            remainder = h if index is None else sp.expand(h-weight*reduced.generators[index])
            matrix = quadratic_matrix(reduced.variables, remainder)
            return (matrix is not None and witness['matrix'] ==
                    [[str(v) for v in row] for row in matrix.tolist()] and exact_psd(matrix))
        if witness['kind'] == 'putinar':
            model = _sos_model(reduced, h, witness['order'])
            return model.to_data() == witness['model'] and check_conic_values(model, witness['exact_values'])
        return False
    except (AnalysisError, KeyError, ValueError, TypeError, ZeroDivisionError):
        return False


class InvariantProver:
    """Per-preparation cache/budget. Replay consumes saved exact proofs only."""
    def __init__(self, *, saved_evidence=None, total_seconds=15, solver_seconds=3):
        self.saved_evidence = saved_evidence
        self.deadline = time.monotonic()+total_seconds
        self.solver_seconds = solver_seconds
        self.cache = {}
        self.saved = {}
        if saved_evidence is not None:
            def collect(value):
                if isinstance(value, dict):
                    if value.get('method') == METHOD:
                        key = json.dumps([value.get('domain'), value.get('conclusion')], sort_keys=True)
                        self.saved.setdefault(key, value)
                    else:
                        for item in value.values():
                            collect(item)
                elif isinstance(value, list):
                    for item in value:
                        collect(item)
            collect(saved_evidence)

    def __call__(self, domain, expression, label):
        key = _key(domain, expression)
        if key in self.cache:
            return self.cache[key]
        if key in self.saved:
            proof = self.saved[key]
            if not check_invariant_certificate(domain, expression, proof):
                raise AnalysisError(f'Invalid saved invariant certificate: {label}')
        else:
            try:
                proof = require_nonnegative(domain, expression, label)
            except AnalysisError:
                # Do the cheap quadratic check before the potentially large
                # generator-product LP. Old certificates still replay through
                # the old rule; missing new witnesses are never synthesized.
                reduced, h = eliminate_fixed_equalities(domain, sp.expand(expression))
                witness = None if self.saved_evidence is not None else _quadratic_witness(reduced, h)
                if witness is not None:
                    proof = self._certificate(domain, expression, reduced, h, witness, label)
                else:
                    try:
                        proof = elementary_proof(domain, expression, label)
                    except AnalysisError:
                        if self.saved_evidence is not None:
                            raise AnalysisError(f'Missing exact invariant certificate: {label}')
                        proof = self._synthesize(domain, expression, label)
        self.cache[key] = proof
        return proof

    def _synthesize(self, domain, expression, label):
        original = sp.expand(expression)
        reduced, h = eliminate_fixed_equalities(domain, original)
        witness = _quadratic_witness(reduced, h)
        failures = []
        if witness is None:
            from contractive_tool.backends.cvxpy.builder import build
            from contractive_tool.backends.cvxpy.mosek_solver import solve
            from contractive_tool.backends.cvxpy.verification import reconstruct
            for order in (1, 2):
                if time.monotonic() >= self.deadline:
                    failures.append('invariant_time_budget')
                    break
                try:
                    model = _sos_model(reduced, h, order)
                    remaining = self.deadline-time.monotonic()
                    if remaining <= 0:
                        failures.append('invariant_time_budget')
                        break
                    numerical = solve(build(model), time_limit=min(self.solver_seconds, remaining))
                    if numerical['status'] != 'solved_unverified':
                        failures.append(numerical.get('diagnostic', numerical['status']))
                        continue
                    exact = reconstruct(model, numerical['values'], deadline=self.deadline)
                    if exact['status'] == 'proved':
                        witness = {'kind': 'putinar', 'order': order, 'model': model.to_data(),
                                   'exact_values': exact['exact_values']}
                        break
                    failures.append(exact.get('reason', exact['status']))
                except (AnalysisError, ImportError, ValueError) as error:
                    failures.append(str(error))
        if witness is None:
            raise AnalysisError(f'Cannot certify {label} with exact invariant SOS: {"; ".join(failures)}')
        return self._certificate(domain, original, reduced, h, witness, label)

    @staticmethod
    def _certificate(domain, original, reduced, h, witness, label):
        proof = {'method': METHOD, 'domain': domain.to_data(), 'conclusion': str(sp.expand(original)),
                 'reduced_domain': reduced.to_data(), 'reduced_conclusion': str(h), 'witness': witness}
        if not check_invariant_certificate(domain, original, proof):
            raise AnalysisError(f'Invariant certificate failed exact replay: {label}')
        return proof


def prepare_certified_program(cfg, *, saved_evidence=None):
    evidence = prepare_program(cfg, invariant_prover=InvariantProver(saved_evidence=saved_evidence))
    if saved_evidence is not None and evidence.to_data() != saved_evidence:
        raise AnalysisError('Invariant evidence differs from source replay')
    return evidence

