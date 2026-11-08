"""Independent Cauchy searches; no change to default family dispatch.

Fixed eta: one scalar norm-bound SDP, then rational exponent search.
Template eta: fixed rational t -> matrix SOS synthesis -> exponent search.
All retained bounds have exact rational state and moment certificates.
"""
from dataclasses import dataclass, field, asdict
import json
import time
from pathlib import Path

import sympy as sp

from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.ir import BasicSet, ConicModel
from contractive_tool.positivity.base import EncodingLimits, new_scalar, match_coefficients
from contractive_tool.positivity.gram import free_polynomial
from contractive_tool.positivity.putinar import lower_sos
from contractive_tool.positivity.matrix_sos import generator_products, lower_matrix_sos
from contractive_tool.probability.fractional_moments import (
    rational, power_enclosure, verify_power, certify_moment, verify_moment)


@dataclass(frozen=True)
class ExponentOptions:
    values: tuple | None = ('1/4', '1/2', '3/4', '1', '3/2', '2', '3', '4')
    interval: tuple | None = None
    coarse_points: int = 9
    refinements: int = 2
    max_candidates: int = 129
    margin: str = '1/100'
    digits: int = 12
    target_n: int | None = None

    def candidates(self):
        margin = rational(self.margin)
        if not 0 < margin < 1:
            raise AnalysisError('Contraction margin must lie in (0,1)')
        if self.target_n is not None and (type(self.target_n) is not int or not 0 <= self.target_n <= 10000):
            raise AnalysisError('target_n must be an integer in [0,10000]')
        if (type(self.digits) is not int or not 1 <= self.digits <= 50
                or type(self.max_candidates) is not int or self.max_candidates < 1):
            raise AnalysisError('Invalid exponent arithmetic/candidate budget')
        result = []
        if self.interval is not None:
            lo, hi = map(rational, self.interval)
            if (not 0 < lo < hi or type(self.coarse_points) is not int or self.coarse_points < 2
                    or type(self.refinements) is not int or not 0 <= self.refinements <= 8):
                raise AnalysisError('Invalid exponent interval/refinement settings')
            # Bounded dyadic refinement covers the whole interval, including k<1.
            for level in range(self.refinements+1):
                count = (self.coarse_points-1)*2**level
                for i in range(count+1):
                    k = lo+(hi-lo)*i/count
                    if max(k.p, k.q) > 2048:
                        raise AnalysisError('Exponent interval grid exceeds arithmetic budget')
                    if k not in result:
                        result.append(k)
                    if len(result) >= self.max_candidates:
                        return tuple(result)
        else:
            result = list(dict.fromkeys(rational(k) for k in (self.values or ())))
        if not result or any(k <= 0 or max(k.p, k.q) > 2048 for k in result):
            raise AnalysisError('Supply positive rational exponents within arithmetic budget')
        if len(result) > self.max_candidates:
            raise AnalysisError('Explicit exponent grid exceeds budget')
        return tuple(result)


@dataclass(frozen=True)
class CauchyOptions:
    scalar_order: int = 2
    scalar_strategy: str = 'constant_sos'
    matrix_multiplier_degree: int = 0
    product_depth: int = 2
    limits: EncodingLimits = field(default_factory=EncodingLimits)
    solver_seconds: float = 30
    total_seconds: float = 300
    repair_seconds: float = 20
    repair_relative_gap: float = 0.05
    repair_max_solves: int = 2
    max_t_points: int = 32
    exponents: ExponentOptions = field(default_factory=ExponentOptions)

    def validate(self):
        import math
        self.exponents.candidates()
        if self.scalar_strategy not in ('constant_sos', 'sos'):
            raise AnalysisError('Unknown scalar Cauchy positivity encoding')
        if (type(self.scalar_order) is not int or not 1 <= self.scalar_order <= 8
                or type(self.matrix_multiplier_degree) is not int or not 0 <= self.matrix_multiplier_degree <= 4
                or type(self.product_depth) is not int or self.product_depth < 1
                or type(self.repair_max_solves) is not int or not 0 <= self.repair_max_solves <= 2
                or type(self.max_t_points) is not int or self.max_t_points < 1):
            raise AnalysisError('Invalid Cauchy encoding/search budget')
        if any(not math.isfinite(v) or v <= 0 for v in (self.solver_seconds, self.total_seconds)):
            raise AnalysisError('Time budgets must be positive and finite')
        if any(not math.isfinite(v) or v < 0 for v in (self.repair_seconds, self.repair_relative_gap)):
            raise AnalysisError('Repair budgets must be nonnegative and finite')
        if any(type(v) is not int or v < 1 for v in asdict(self.limits).values()):
            raise AnalysisError('Encoding limits must be positive integers')


@dataclass(frozen=True)
class EtaTemplate:
    expression: sp.Expr
    coefficients: tuple
    nonnegative: tuple = ()  # affine expressions in coefficients
    equalities: tuple = ()


def _validate_eta(round_, eta, coefficients=()):
    eta = sp.expand(sp.sympify(eta))
    coefficients = tuple(coefficients)
    if (len(set(coefficients)) != len(coefficients)
            or not all(isinstance(c, sp.Symbol) for c in coefficients)
            or set(coefficients) & (set(round_.variables) | set(round_.law.symbols))):
        raise AnalysisError('Template coefficients must be distinct from state/random symbols')
    allowed = set(round_.variables) | set(coefficients)
    if eta.free_symbols - allowed:
        raise AnalysisError('Eta contains undeclared symbols')
    symbols = tuple(round_.variables)+coefficients
    polynomial = sp.Poly(eta, *symbols) if symbols else None
    if polynomial is not None:
        for powers, value in polynomial.terms():
            rational(value)
            if coefficients and sum(powers[-len(coefficients):]) > 1:
                raise AnalysisError('Eta must be affine in template coefficients')
    return eta


def _namespace(round_, coefficients):
    prefix = '__cauchy'
    names = [str(x) for x in (*round_.variables, *round_.law.symbols, *coefficients)]
    while any(name.startswith(prefix) for name in names):
        prefix += '_'
    return prefix


def _project(domain, expressions, decisions):
    """Drop irrelevant constraints, a safe domain overapproximation (not projection equality)."""
    needed = set().union(*(e.free_symbols for e in expressions))-set(map(sp.Symbol, decisions))
    if needed-set(domain.variables):
        raise AnalysisError('Undeclared state symbols in obligation')
    return BasicSet(tuple(v for v in domain.variables if v in needed),
        tuple(dict.fromkeys(g for g in domain.generators if g.free_symbols <= needed and g != 0)),
        tuple(dict.fromkeys(e for e in domain.equalities if e.free_symbols <= needed and e != 0)))


def _scalar(domain, expression, model, name, options):
    expression = sp.expand(expression)
    if expression == 0:
        return
    # A common even monomial is globally nonnegative. Certifying the quotient
    # is sufficient, and avoids unnecessary variables in homogeneous examples.
    factor = sp.Integer(1)
    if domain.variables:
        powers = sp.Poly(expression, *domain.variables).monoms()
        factor = sp.prod(v**(2*(min(p[i] for p in powers)//2)) for i, v in enumerate(domain.variables))
    reduced = sp.cancel(expression/factor).expand()
    projected = _project(domain, [reduced], model.decisions)
    products = generator_products(projected, options.product_depth, options.limits)
    if options.scalar_strategy == 'sos':
        lower_sos(projected, reduced, model, name, options.scalar_order, options.limits, products)
    else:
        # Constant SOS multipliers are a valid inexpensive subfamily, also on
        # unbounded domains. No compactness/completeness theorem is assumed.
        if len(model.decisions)+len(products)+1 > options.limits.max_decisions:
            raise AnalysisError('Constant SOS decision budget exceeded')
        rhs = sum(new_scalar(model, f'{name}_a{i}', nonnegative=True)*g
                  for i, g in enumerate([sp.Integer(1), *products]))
        for i, equality in enumerate(projected.equalities):
            rhs += equality*free_polynomial(projected.variables, 2*options.scalar_order,
                                            model, f'{name}_h{i}', options.limits)
        match_coefficients(reduced-rhs, projected.variables, model)
    model.coverage.setdefault('scalar', []).append({'id': name, 'domain': domain.to_data(),
        'conclusion': str(expression), 'nonnegative_factor': str(factor),
        'sufficient_quotient': str(reduced), 'proof_domain': projected.to_data()})


class StateModelBudgetExceeded(AnalysisError):
    pass


def _check_state_budget(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise StateModelBudgetExceeded('Cauchy state-model construction time budget exceeded')


def _common(round_, eta, decompositions, model, prefix, options, deadline=None):
    for i, (domain, numerator, _, _) in enumerate(decompositions):
        _check_state_budget(deadline)
        _scalar(domain, eta-1, model, f'{prefix}_normalization_{i}', options)
        for j, (values, probability) in enumerate(round_.law.atoms):
            _check_state_budget(deadline)
            if probability == 0:
                continue
            successor = sp.expand(numerator.subs(dict(zip(round_.law.symbols, values)), simultaneous=True))
            _scalar(domain, successor, model, f'{prefix}_successor_{i}_{j}', options)


def build_fixed_model(round_, eta, *, basis=None, options=None, deadline=None):
    options = options or CauchyOptions()
    options.validate()
    eta = _validate_eta(round_, eta)
    _check_state_budget(deadline)
    decompositions = round_.decompositions(eta, basis)
    basis = decompositions[0][3]
    q = (tuple(v for _, _, coefficients, _ in decompositions for v in coefficients)
         if round_.pieces else decompositions[0][2])
    prefix = _namespace(round_, ())
    B = sp.Symbol(prefix+'_B')
    model = ConicModel([str(B)], B, nonnegative=[str(B)])
    _common(round_, eta, decompositions, model, prefix, options, deadline)
    for i, (domain, _, coefficients, _) in enumerate(decompositions):
        _check_state_budget(deadline)
        _scalar(domain, B*eta**2-sum(v**2 for v in coefficients), model, f'{prefix}_norm_{i}', options)
    model.to_data(check_budget=lambda: _check_state_budget(deadline))
    return model, {'eta': eta, 'q': q, 'basis': basis, 'B_symbol': B}


def build_template_model(round_, template, t, *, basis=None, options=None, deadline=None):
    options = options or CauchyOptions()
    options.validate()
    t = rational(t)
    if t <= 0:
        raise AnalysisError('Template search requires t > 0; fixed eta handles B=0')
    coefficients = tuple(template.coefficients)
    eta = _validate_eta(round_, template.expression, coefficients)
    _check_state_budget(deadline)
    decompositions = round_.decompositions(eta, basis)
    basis = decompositions[0][3]
    q = (tuple(v for _, _, coefficients, _ in decompositions for v in coefficients)
         if round_.pieces else decompositions[0][2])
    prefix = _namespace(round_, coefficients)
    objective = sp.expand(eta.subs(round_.initial, simultaneous=True))
    model = ConicModel(list(map(str, coefficients)), objective)
    for i, expression in enumerate(template.nonnegative):
        slack = new_scalar(model, f'{prefix}_coefficient_slack_{i}', nonnegative=True)
        model.equalities.append(sp.expand(sp.sympify(expression)-slack))
    model.equalities.extend(map(sp.sympify, template.equalities))
    # Validate coefficient restrictions before the state SOS variables are added.
    model.to_data(check_budget=lambda: _check_state_budget(deadline))
    _common(round_, eta, decompositions, model, prefix, options, deadline)
    for i, (domain, _, coefficients, _) in enumerate(decompositions):
        _check_state_budget(deadline)
        matrix = sp.eye(len(coefficients)+1)*t*eta
        for j, value in enumerate(coefficients, 1):
            matrix[0, j] = matrix[j, 0] = value
        projected = _project(domain, list(matrix), model.decisions)
        products = generator_products(projected, options.product_depth, options.limits)
        lower_matrix_sos(projected, matrix, model, f'{prefix}_matrix_{i}',
                         options.matrix_multiplier_degree, options.limits, products,
                         check_budget=lambda: _check_state_budget(deadline))
        model.coverage.setdefault('matrix', []).append({'domain': domain.to_data(),
            'proof_domain': projected.to_data(), 'matrix': [[str(v) for v in row] for row in matrix.tolist()]})
    model.to_data(check_budget=lambda: _check_state_budget(deadline))
    return model, {'eta': eta, 'q': q, 'basis': basis, 't': t}


def _solve(model, options, deadline):
    from contractive_tool.backends.cvxpy.builder import build
    from contractive_tool.backends.cvxpy.mosek_solver import solve
    from contractive_tool.backends.cvxpy.verification import reconstruct
    from contractive_tool.backends.cvxpy.repair import repair, RepairOptions
    if time.monotonic() >= deadline:
        return {'status': 'unknown', 'reason': 'time_budget'}
    solved = solve(build(model), time_limit=min(options.solver_seconds, deadline-time.monotonic()))
    result = {'status': 'unknown', 'solver': solved}
    if solved.get('values') is None:
        result['reason'] = solved['status']
        return result
    verified = reconstruct(model, solved['values'], deadline=deadline)
    if verified['status'] != 'proved' and options.repair_seconds and options.repair_max_solves and time.monotonic() < deadline:
        repaired, audit = repair(model, solved['values'], deadline=deadline,
            options=RepairOptions(options.repair_seconds, options.repair_relative_gap, options.repair_max_solves),
            solver_seconds=options.solver_seconds)
        result['repair'] = audit
        if repaired['status'] == 'proved':
            verified = repaired
    result['verification'] = verified
    if verified['status'] == 'proved':
        result['status'] = 'proved'
    else:
        result['reason'] = verified.get('reason', 'exact_verification_failed')
    return result


def search_exponents(norm_atoms, B, initial, options=None):
    options = options or ExponentOptions()
    B, initial = rational(B), rational(initial)
    if B <= 0 or initial < 1:
        raise AnalysisError('Exponent search requires B > 0 and active initial eta >= 1')
    candidates, history = [], []
    for k in options.candidates():
        moment = certify_moment(norm_atoms, k, options.digits)
        norm_power = power_enclosure(B, k/2, options.digits)
        initial_power = power_enclosure(initial, k, options.digits)
        rho = sp.Rational(moment['upper'])*sp.Rational(norm_power['upper'])
        row = {'k': str(k), 'rho_upper': str(rho), 'status': 'no_contraction'}
        if rho <= 1-rational(options.margin):
            C = sp.Rational(initial_power['upper'])
            candidate = {'k': str(k), 'B': str(B), 'base_initial': str(initial),
                'prefactor_upper': str(C), 'decay_upper': str(rho),
                'moment': moment, 'norm_power': norm_power, 'initial_power': initial_power,
                'event': 'K > n', 'time_unit': 'completed_loop_iterations',
                'n_domain': 'nonnegative integers', 'expression': f'min(1, ({C})*({rho})**n)'}
            if options.target_n is not None:
                candidate['target_n'] = options.target_n
                candidate['target_upper'] = str(min(sp.Integer(1), C*rho**options.target_n))
            if not verify_exponent(candidate, norm_atoms):
                raise AnalysisError('Internal fractional certificate verification failed')
            candidates.append(candidate)
            row['status'] = 'proved'
        history.append(row)
    return candidates, history


def verify_exponent(candidate, norm_atoms):
    try:
        k, B, A, C, rho = (rational(candidate[key]) for key in
                           ('k', 'B', 'base_initial', 'prefactor_upper', 'decay_upper'))
        moment, norm, initial = (candidate[key] for key in ('moment', 'norm_power', 'initial_power'))
        return bool(k > 0 and B > 0 and A >= 1 and 0 <= rho < 1
            and rational(moment['k']) == k and verify_moment(moment, norm_atoms)
            and rational(norm['base']) == B and rational(norm['exponent']) == k/2 and verify_power(norm)
            and rational(initial['base']) == A and rational(initial['exponent']) == k and verify_power(initial)
            and C == rational(initial['upper'])
            and rho == rational(moment['upper'])*rational(norm['upper']))
    except (KeyError, ValueError, TypeError, AnalysisError):
        return False


def _new_result(round_, mode, options):
    return {'schema_version': 1, 'mode': mode, 'status': 'no_certificate_found',
        'round': round_.to_data(), 'options': asdict(options), 'attempts': [], 'candidates': [],
        'selection': None, 'optimality': 'bounded search; no global optimality claim',
        'budget_policy': 'cooperative symbolic/verification checks; solver optimizer time limit'}


def _finish(result, out_dir, started):
    candidates = result['candidates']
    if candidates:
        result['status'] = 'proved'
        n = result['options']['exponents']['target_n']
        if n is not None:
            result['selection'] = min(range(len(candidates)), key=lambda i:
                rational(candidates[i]['prefactor_upper'])*rational(candidates[i]['decay_upper'])**n)
    result['elapsed_seconds'] = time.monotonic()-started
    if out_dir is not None:
        path = Path(out_dir)
        if path.exists() and any(path.iterdir()):
            raise AnalysisError('Use a new or empty Cauchy artifact directory')
        path.mkdir(parents=True, exist_ok=True)
        (path/'result.json').write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False)+'\n')
    return result


def search_fixed_eta(round_, eta, *, basis=None, options=None, out_dir=None):
    options = options or CauchyOptions()
    options.validate()
    started = time.monotonic()
    result = _new_result(round_, 'fixed_eta', options)
    result['input'] = {'eta': str(eta), 'basis': None if basis is None else list(map(str, basis))}
    if not round_.initial_active:
        result.update(status='proved', special_case='initially_exited', tail='Pr(K>n)=0 for n>=0')
        return _finish(result, out_dir, started)
    try:
        model, data = build_fixed_model(round_, eta, basis=basis, options=options,
                                       deadline=started+options.total_seconds)
    except StateModelBudgetExceeded as error:
        result['attempts'].append({'status': 'unknown', 'reason': 'state_model_time_budget', 'detail': str(error)})
        result['stop_reason'] = 'state_model_time_budget'
        return _finish(result, out_dir, started)
    attempt = _solve(model, options, started+options.total_seconds)
    attempt.update(model=model.to_data(), basis=list(map(str, data['basis'])), q=list(map(str, data['q'])))
    result['attempts'].append(attempt)
    if attempt['status'] == 'proved':
        values = {sp.Symbol(n): rational(v) for n, v in attempt['verification']['exact_values'].items()}
        B = data['B_symbol'].xreplace(values)
        A = rational(data['eta'].subs(round_.initial, simultaneous=True))
        attempt.update(B=str(B), eta=str(data['eta']), base_initial=str(A))
        if B == 0:
            result.update(status='proved', special_case='one_step_termination',
                          tail='Pr(K>0)<=1; Pr(K>n)=0 for n>=1')
        else:
            candidates, history = search_exponents(round_.law.norm_atoms(data['basis']), B, A, options.exponents)
            attempt['exponent_history'] = history
            result['candidates'] = [{**c, 'attempt': 0, 'eta': str(data['eta'])} for c in candidates]
    return _finish(result, out_dir, started)


def automatic_t_grid(norm_atoms, exponents, count=8):
    """Conservative admissible endpoints for a finite exponent search, not a global supremum."""
    endpoints = []
    for k in exponents.candidates():
        gamma = rational(certify_moment(norm_atoms, k, exponents.digits)['upper'])
        if gamma == 0:
            raise AnalysisError('Zero random norm: use fixed-eta degenerate path or explicit t values')
        cap = power_enclosure((1-rational(exponents.margin))/gamma, 1/k, exponents.digits)
        endpoints.append(rational(cap['lower']))
    upper = max(endpoints)
    return tuple(upper*i/count for i in range(1, count+1) if upper*i/count > 0)


def search_template_eta(round_, template, *, t_values=None, basis=None, options=None, out_dir=None):
    options = options or CauchyOptions()
    options.validate()
    started = time.monotonic()
    result = _new_result(round_, 'template_eta', options)
    eta = _validate_eta(round_, template.expression, template.coefficients)
    basis = round_.resolve_basis(eta, basis)
    result['input'] = {'eta': str(eta), 'coefficients': list(map(str, template.coefficients)),
        'nonnegative': list(map(str, template.nonnegative)), 'equalities': list(map(str, template.equalities)),
        'basis': list(map(str, basis))}
    if not round_.initial_active:
        result.update(status='proved', special_case='initially_exited', tail='Pr(K>n)=0 for n>=0')
        return _finish(result, out_dir, started)
    norms = round_.law.norm_atoms(basis)
    grid = (automatic_t_grid(norms, options.exponents, min(8, options.max_t_points))
            if t_values is None else tuple(dict.fromkeys(map(rational, t_values))))
    if not grid or len(grid)>options.max_t_points or any(t <= 0 for t in grid):
        raise AnalysisError('Supply positive t values within the parameter budget')
    result['input']['t_values'] = list(map(str, grid))
    for t in grid:
        if time.monotonic()-started >= options.total_seconds:
            result['stop_reason'] = 'time_budget'
            break
        try:
            model, data = build_template_model(round_, template, t, basis=basis, options=options,
                                              deadline=started+options.total_seconds)
        except StateModelBudgetExceeded as error:
            result['attempts'].append({'t': str(t), 'status': 'unknown',
                                      'reason': 'state_model_time_budget', 'detail': str(error)})
            result['stop_reason'] = 'state_model_time_budget'
            break
        attempt = _solve(model, options, started+options.total_seconds)
        attempt.update(t=str(t), model=model.to_data(), basis=list(map(str, basis)), q=list(map(str, data['q'])))
        result['attempts'].append(attempt)
        if attempt['status'] != 'proved':
            continue
        values = {sp.Symbol(n): rational(v) for n, v in attempt['verification']['exact_values'].items()}
        concrete = sp.expand(eta.xreplace(values))
        A = rational(concrete.subs(round_.initial, simultaneous=True))
        attempt.update(eta=str(concrete), base_initial=str(A), B=str(t*t))
        candidates, history = search_exponents(norms, t*t, A, options.exponents)
        attempt['exponent_history'] = history
        result['candidates'].extend({**c, 'attempt': len(result['attempts'])-1,
                                    'eta': str(concrete), 't': str(t)} for c in candidates)
    return _finish(result, out_dir, started)


def evaluate(result, n):
    if type(n) is not int or not 0 <= n <= 10000:
        raise AnalysisError('Evaluation n must be an integer in [0,10000]')
    if result['status'] != 'proved':
        raise AnalysisError('No proved Cauchy certificate')
    if result.get('special_case') == 'initially_exited':
        return {'n': n, 'upper_bound_exact': '0', 'candidate': None}
    if result.get('special_case') == 'one_step_termination':
        return {'n': n, 'upper_bound_exact': '1' if n == 0 else '0', 'candidate': None}
    values = [min(sp.Integer(1), rational(c['prefactor_upper'])*rational(c['decay_upper'])**n)
              for c in result['candidates']]
    best = min(range(len(values)), key=values.__getitem__)
    return {'n': n, 'upper_bound_exact': str(values[best]), 'upper_bound_numeric': float(values[best]),
            'numeric_is_display_only': True, 'candidate': best}
