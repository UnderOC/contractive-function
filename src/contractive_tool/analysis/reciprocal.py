"""Standalone Section 3 reciprocal-potential synthesis.

Synthesize a polynomial denominator using growth/support and optional fixed-D
matrix constraints, tighten its moments, and optimize rational exponents.
Bounded feedback revisits denominator coefficients using the full tail bound.
Only exact conic certificates and outward rational power bounds are retained.
No positive-power or Cauchy search is invoked; their scalar encoding/solver
utilities are shared. The stronger eta >= epsilon restriction is intentional.
"""
from dataclasses import asdict, dataclass, field
from math import comb, isfinite
import time

import sympy as sp

from contractive_tool.analysis.cauchy import EtaTemplate, _scalar, _solve, _validate_eta, _project
from contractive_tool.analysis.templates import select_variables, total_degree_exponents
from contractive_tool.analysis.reciprocal_exponents import propose_exponents
from contractive_tool.analysis.reciprocal_feedback import feedback_search
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.base import EncodingLimits
from contractive_tool.positivity.ir import ConicModel
from contractive_tool.positivity.matrix_sos import generator_products, lower_matrix_sos
from contractive_tool.probability.fractional_moments import power_enclosure, rational


@dataclass(frozen=True)
class ReciprocalOptions:
    degree: int = 1
    variables: tuple | None = None
    growth_values: tuple = ('3/2', '5/4', '9/8', '17/16', '33/32', '65/64', '129/128')
    support_values: tuple = ('1/2',)
    moment_values: tuple = ()
    matrix_multiplier_degree: int = 0
    epsilon: str = '1/1000'
    k_values: tuple = ('1/16', '1/8', '1/4', '1/2', '3/4', '1', '3/2', '2', '4')
    adaptive_k: bool = True
    k_upper: str = '8'
    k_steps: int = 24
    k_denominator: int = 256
    target_ns: tuple = (20, 100, 1000)
    feedback_points: int = 12
    feedback_seconds: float = 60
    feedback_step: str = '1/4'
    digits: int = 12
    scalar_order: int = 2
    scalar_strategy: str = 'constant_sos'
    product_depth: int = 2
    limits: EncodingLimits = field(default_factory=EncodingLimits)
    solver_seconds: float = 30
    total_seconds: float = 120
    repair_seconds: float = 10
    repair_relative_gap: float = 0.05
    repair_max_solves: int = 2

    def validate(self):
        if type(self.degree) is not int or not 0 <= self.degree <= 8:
            raise AnalysisError('Reciprocal degree must be in [0,8]')
        if not 0 < rational(self.epsilon) <= 1:
            raise AnalysisError('epsilon must lie in (0,1] (eta(initial) is normalized to 1)')
        if not self.growth_values or any(rational(c) <= 1 for c in self.growth_values):
            raise AnalysisError('Growth grid requires c > 1')
        if not self.support_values or any(rational(r) <= 0 for r in self.support_values):
            raise AnalysisError('Support grid requires r0 > 0')
        if len(self.growth_values)*len(self.support_values) > 64:
            raise AnalysisError('At most 64 synthesis parameter pairs are supported')
        if (len(self.moment_values) > 16 or any(rational(D) <= 1 for D in self.moment_values)
                or len(self.growth_values)*len(self.support_values)*max(1, len(self.moment_values)) > 128
                or type(self.matrix_multiplier_degree) is not int or not 0 <= self.matrix_multiplier_degree <= 4):
            raise AnalysisError('Invalid fixed-D matrix search settings')
        if not self.k_values or len(self.k_values) > 129 or any(
                rational(k) <= 0 or max(rational(k).p, rational(k).q) > 2048 for k in self.k_values):
            raise AnalysisError('Supply at most 129 positive rational exponents within arithmetic budget')
        if type(self.digits) is not int or not 1 <= self.digits <= 50:
            raise AnalysisError('digits must lie in [1,50]')
        if (type(self.feedback_points) is not int or not 0 <= self.feedback_points <= 128
                or not isfinite(self.feedback_seconds) or self.feedback_seconds < 0
                or not 0 < rational(self.feedback_step) <= sp.Rational(1, 2)):
            raise AnalysisError('Invalid reciprocal feedback budget')
        if (type(self.adaptive_k) is not bool or not 1 <= rational(self.k_upper) <= 64
                or type(self.k_steps) is not int or not 1 <= self.k_steps <= 64
                or type(self.k_denominator) is not int or not 2 <= self.k_denominator <= 2048
                or not self.target_ns or len(self.target_ns) > 8
                or any(type(n) is not int or not 1 <= n <= 10000 for n in self.target_ns)):
            raise AnalysisError('Invalid adaptive exponent search settings')
        if self.scalar_strategy not in ('constant_sos', 'sos'):
            raise AnalysisError('Unknown scalar positivity encoding')
        if (type(self.scalar_order) is not int or not 1 <= self.scalar_order <= 8
                or type(self.product_depth) is not int or not 1 <= self.product_depth <= 8
                or type(self.repair_max_solves) is not int or not 0 <= self.repair_max_solves <= 2):
            raise AnalysisError('Invalid positivity/repair budget')
        if any(not isfinite(v) or v <= 0 for v in (self.solver_seconds, self.total_seconds)):
            raise AnalysisError('Time budgets must be positive and finite')
        if any(not isfinite(v) or v < 0 for v in (self.repair_seconds, self.repair_relative_gap)):
            raise AnalysisError('Repair budgets must be nonnegative and finite')
        if any(type(v) is not int or v < 1 for v in asdict(self.limits).values()):
            raise AnalysisError('Encoding limits must be positive integers')


def _prefix(round_, coefficients=()):
    prefix = '__reciprocal'
    names = map(str, (*round_.variables, *round_.law.symbols, *coefficients))
    names = tuple(names)
    while any(n.startswith(prefix) for n in names):
        prefix += '_'
    return prefix


def polynomial_template(round_, options):
    names = select_variables(round_.variables, options.variables)
    if comb(len(names)+options.degree, options.degree) > options.limits.max_decisions:
        raise AnalysisError('Reciprocal template exceeds coefficient budget')
    basis = total_degree_exponents(len(names), options.degree)
    prefix = _prefix(round_)
    coefficients = tuple(sp.Symbol(f'{prefix}_eta_{i}') for i in range(len(basis)))
    expression = sum(a*sp.prod(sp.Symbol(v)**p for v, p in zip(names, powers))
                     for a, powers in zip(coefficients, basis))
    return EtaTemplate(expression, coefficients)


def successors(round_, eta, update=None):
    """Raw successors, including exits, as required by Eq. (3.7)."""
    if update is None:
        if round_.pieces:
            raise AnalysisError('Piecewise rounds require regional successors')
        update = round_.update
    numerator = sp.expand(eta.subs(update, simultaneous=True))
    return tuple((sp.expand(numerator.subs(dict(zip(round_.law.symbols, values)), simultaneous=True)), p)
                 for values, p in round_.law.atoms if p)


def build_denominator_model(round_, template, options, c=None, r0=None, D=None, b_cap=None):
    if c is not None:
        c, r0 = rational(c), rational(r0)
        if not (c > 1 and 0 < r0 < c):
            raise AnalysisError('Denominator seeds require c>1 and 0<r0<c')
    if D is not None:
        D = rational(D)
        if c is None or D < c*c:
            raise AnalysisError('Fixed D requires growth/support seeds and D>=c^2')
    if b_cap is not None and rational(b_cap) < 1:
        raise AnalysisError('Normalized denominator requires b_cap>=1')
    coefficients = template.coefficients
    eta = _validate_eta(round_, template.expression, coefficients)
    prefix = _prefix(round_, coefficients)
    b = sp.Symbol(prefix+'_b')
    model = ConicModel([*map(str, coefficients), str(b)], b, nonnegative=[str(b)])
    model.equalities.append(sp.expand(eta.subs(round_.initial, simultaneous=True)-1))
    # This standalone API uses the unconstrained polynomial template; fixed eta
    # is represented by an empty coefficient set after initial normalization.
    if template.nonnegative or template.equalities:
        raise AnalysisError('Use an unconstrained polynomial template or a fixed eta')
    for i, (domain, update) in enumerate(round_.domain_updates()):
        outcomes = successors(round_, eta, update)
        mean = sp.expand(sum(p*value for value, p in outcomes))
        matrix = None if D is None else second_moment_matrix(eta, outcomes, D)
        _scalar(domain, eta-rational(options.epsilon), model, f'{prefix}_positive_{i}', options)
        _scalar(domain, b-eta, model, f'{prefix}_bounded_{i}', options)
        if b_cap is not None:
            _scalar(domain, rational(b_cap)-b, model, f'{prefix}_bcap_{i}', options)
        if c is not None:
            _scalar(domain, mean-c*eta, model, f'{prefix}_growth_{i}', options)
            for j, (value, _) in enumerate(outcomes):
                _scalar(domain, value-r0*eta, model, f'{prefix}_support_{i}_{j}', options)
        if matrix is not None:
            projected = _project(domain, list(matrix), model.decisions)
            products = generator_products(projected, options.product_depth, options.limits)
            lower_matrix_sos(projected, matrix, model, f'{prefix}_second_{i}',
                             options.matrix_multiplier_degree, options.limits, products)
            model.coverage.setdefault('matrix', []).append({'domain': domain.to_data(),
                'proof_domain': projected.to_data(), 'D': str(D),
                'matrix': [[str(v) for v in row] for row in matrix.tolist()],
                'conclusion': 'E[eta_next^2] <= D*eta^2; eta>0 separately certified'})
    model.to_data()
    return model, eta, b


def second_moment_matrix(eta, outcomes, D):
    """Rational Schur matrix: no square roots of branch probabilities.

The lower block eta*diag(p) is positive definite for eta>0, p>0;
its Schur complement times eta equals D*eta^2-sum(p*eta_next^2).
"""
    matrix = sp.zeros(len(outcomes)+1)
    matrix[0, 0] = D*eta
    for j, (value, probability) in enumerate(outcomes, 1):
        matrix[j, j] = probability*eta
        matrix[0, j] = matrix[j, 0] = probability*value
    return matrix


def build_moment_model(round_, eta, kind, options, *, c=None):
    """Fixed denominator makes every moment obligation affine in its constant."""
    eta = _validate_eta(round_, eta)
    prefix = _prefix(round_)
    parameter = sp.Symbol(prefix+'_'+kind)
    model = ConicModel([str(parameter)], parameter if kind == 'D' else -parameter,
                       nonnegative=[str(parameter)])
    for i, (domain, update) in enumerate(round_.domain_updates()):
        outcomes = successors(round_, eta, update)
        mean = sp.expand(sum(p*v for v, p in outcomes))
        second = sp.expand(sum(p*v*v for v, p in outcomes))
        if kind == 'c':
            expressions = (mean-parameter*eta,)
        elif kind == 'D':
            expressions = (parameter*eta**2-second, parameter-rational(c)**2)
        elif kind == 'r0':
            expressions = tuple(v-parameter*eta for v, _ in outcomes)
        else:
            raise AnalysisError('Unknown moment constant')
        for j, expression in enumerate(expressions):
            _scalar(domain, expression, model, f'{prefix}_{kind}_{i}_{j}', options)
    model.to_data()
    return model, parameter


def moment_bound(c, D, r0, k, digits=12):
    """Eq. (3.8)--(3.11), with exact outward enclosures of negative powers."""
    c, D, r0, k = map(rational, (c, D, r0, k))
    if not (c > 1 and 0 < r0 < c and D >= c*c and k > 0):
        raise AnalysisError('Moment certificate requires c>1, 0<r0<c, D>=c^2, k>0')
    p = (D-c*c)/(D-2*r0*c+r0*r0)
    z = (D-r0*c)/(c-r0)
    low = power_enclosure(1/r0, k, digits)
    high = power_enclosure(1/z, k, digits)
    q = p*rational(low['upper'])+(1-p)*rational(high['upper'])
    return {'c': str(c), 'D': str(D), 'r0': str(r0), 'k': str(k),
            'p_star': str(p), 'z_star': str(z), 'r0_power': low, 'z_power': high,
            'decay_upper': str(q)}


def exponent_candidates(eta, b, c, D, r0, options):
    # A deterministic ratio can give r0=c. Weakening the certified support
    # bound handles this case without dividing by zero; p_star is then zero.
    r0 = r0 if r0 < c else c/2
    candidates, history = [], []
    if not (b >= 1 and c > 1 and r0 > 0 and r0 < c and D >= c*c):
        return [], [{'status': 'invalid_moment_constants'}]
    values, _ = propose_exponents(b, c, D, r0, options)
    for k in values:
        moment = moment_bound(c, D, r0, k, options.digits)
        q = rational(moment['decay_upper'])
        history.append({'k': str(k), 'q_upper': str(q),
                        'status': 'proved' if 0 < q < 1 else 'no_contraction'})
        if 0 < q < 1:
            initial = power_enclosure(b, k, options.digits)
            A = initial['upper']
            candidates.append({'eta': str(eta), 'eta_initial': '1', 'b': str(b), 'k': str(k),
                'moment': moment, 'initial_power': initial,
                'prefactor_upper': A, 'decay_upper': str(q),
                'event': 'K > n', 'time_unit': 'completed_loop_iterations',
                'n_domain': 'nonnegative integers',
                'expression': f'min(1, ({A})*({q})**n)'})
    return candidates, history


def exact_substitution(stage):
    return {sp.Symbol(n): rational(v) for n, v in stage['verification']['exact_values'].items()}


def search_reciprocal(round_, *, options=None, eta=None, template=None):
    """Independent staged synthesis; no call into any existing analysis route."""
    options = options or ReciprocalOptions()
    options.validate()
    started = time.monotonic()
    deadline = started+options.total_seconds
    if eta is not None and template is not None:
        raise AnalysisError('Choose fixed eta or a template')
    if eta is not None:
        eta = _validate_eta(round_, eta)
        initial = rational(eta.subs(round_.initial, simultaneous=True))
        if initial <= 0 and round_.initial_active:
            raise AnalysisError('Fixed eta must be positive at the initial state')
        template = EtaTemplate(sp.expand(eta/initial) if initial > 0 else eta, ())
    else:
        template = template or polynomial_template(round_, options)
    result = {'schema_version': 2, 'method': 'reciprocal_low_order_moments',
        'status': 'no_certificate_found', 'round': round_.to_data(), 'options': asdict(options),
        'input': {'eta': str(template.expression), 'coefficients': list(map(str, template.coefficients))},
        'attempts': [], 'candidates': [],
        'scope': 'Section 3.2 raw moments, including terminating successors; finite random rounds',
        'optimality': 'staged bounded search, not joint/global optimization',
        'budget_policy': 'cooperative symbolic checks and solver optimizer time limits'}
    if not round_.initial_active:
        result.update(status='proved', special_case='initially_exited')
    else:
        def attempt_point(c_seed, r_seed, D_seed=None, *, b_cap=None, origin='grid', point_deadline=None):
            active_deadline = min(deadline, point_deadline if point_deadline is not None else deadline)
            attempt = {'seed_c': None if c_seed is None else str(c_seed),
                       'seed_r0': None if r_seed is None else str(r_seed),
                       'seed_D': None if D_seed is None else str(D_seed),
                       'b_cap': None if b_cap is None else str(b_cap),
                       'origin': origin, 'stages': [], 'status': 'unknown'}
            result['attempts'].append(attempt)

            def solve_stage(kind, model):
                stage = {'kind': kind, 'model': model.to_data(), **_solve(model, options, active_deadline)}
                attempt['stages'].append(stage)
                return exact_substitution(stage) if stage['status'] == 'proved' else None

            try:
                model, expression, b_symbol = build_denominator_model(
                    round_, template, options, c_seed, r_seed, D_seed, b_cap)
            except AnalysisError as error:
                attempt['reason'] = str(error)
                return attempt
            sub = solve_stage('denominator', model)
            if sub is None:
                return attempt
            concrete, b = sp.expand(expression.xreplace(sub)), rational(b_symbol.xreplace(sub))
            # The matrix stage already certifies every seed constant. Numerical
            # failure while tightening must not destroy this valid certificate.
            constants = {} if D_seed is None else {'c': c_seed, 'r0': r_seed, 'D': D_seed}
            for kind in ('c', 'r0', 'D'):
                try:
                    if time.monotonic() >= active_deadline:
                        raise AnalysisError('time_budget')
                    model, parameter = build_moment_model(round_, concrete, kind, options, c=constants.get('c'))
                    sub = solve_stage(kind, model)
                except AnalysisError as error:
                    attempt['stages'].append({'kind': kind, 'status': 'unknown', 'reason': str(error)})
                    sub = None
                if sub is None:
                    if D_seed is None:
                        break
                    continue
                value = rational(parameter.xreplace(sub))
                if kind in constants:
                    value = (min if kind == 'D' else max)(value, constants[kind])
                constants[kind] = value
            if len(constants) != 3:
                return attempt
            attempt.update(eta=str(concrete), b=str(b), constants={k: str(v) for k, v in constants.items()})
            candidates, history = exponent_candidates(concrete, b, **constants, options=options)
            attempt['exponent_history'] = history
            if constants['c'] > 1 and constants['r0'] > 0 and constants['D'] >= constants['c']**2:
                support = constants['r0'] if constants['r0'] < constants['c'] else constants['c']/2
                _, attempt['exponent_search'] = propose_exponents(
                    b, constants['c'], constants['D'], support, options)
            attempt['status'] = 'proved' if candidates else 'no_contraction'
            for candidate in candidates:
                candidate['attempt'] = len(result['attempts'])-1
            result['candidates'].extend(candidates)
            return attempt

        points = [(None, None, None)] if not template.coefficients else [
            (rational(c), rational(r), None if D is None else rational(D))
            for c in options.growth_values for r in options.support_values
            for D in (options.moment_values or (None,))
            if rational(r) < rational(c) and (D is None or rational(D) >= rational(c)**2)]
        for c_seed, r_seed, D_seed in points:
            if time.monotonic() >= deadline:
                result['stop_reason'] = 'time_budget'
                break
            attempt_point(c_seed, r_seed, D_seed)
        if template.coefficients and options.feedback_points and options.feedback_seconds:
            feedback_search(result, attempt_point, options,
                min(deadline, time.monotonic()+options.feedback_seconds), time.monotonic)
        if result['candidates']:
            result['status'] = 'proved'
    result['elapsed_seconds'] = time.monotonic()-started
    return result


def evaluate(result, n):
    """Evaluate the envelope; CLI replays certificates before calling this API."""
    if type(n) is not int or not 0 <= n <= 10000:
        raise AnalysisError('n must be an integer in [0,10000]')
    if result['status'] != 'proved':
        raise AnalysisError('No proved reciprocal tail bound')
    if result.get('special_case') == 'initially_exited':
        return {'n': n, 'upper_bound_exact': '0', 'upper_bound_approx': 0.0}
    values = [min(sp.Integer(1), rational(c['prefactor_upper'])*rational(c['decay_upper'])**n)
              for c in result['candidates']]
    index = min(range(len(values)), key=values.__getitem__)
    # Keep a rational upper bound without serializing enormous integers (which
    # also hits Python's decimal-conversion limit at ordinary horizons like 500).
    scale = 10**result['options']['digits']
    rounded = sp.ceiling(values[index]*scale)/scale
    candidate = result['candidates'][index]
    return {'n': n, 'candidate': index, 'upper_bound_exact': str(rounded),
            'upper_bound_approx': float(rounded),
            'rounding': f'upward to multiples of 1/{scale}',
            'exact_expression': (f"min(1, ({candidate['prefactor_upper']})*"
                                 f"({candidate['decay_upper']})**{n})")}
