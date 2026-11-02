"""Section 2.2: positive raw potentials with full first-moment contraction.

The raw normal-terminal potential is positive, not the zero value of Theta.
All ordinary pCFG transitions are certified, including intermediate failures.
"""
from math import comb

import sympy as sp

from contractive_tool.algebra import PolynomialService
from contractive_tool.analysis.goals import PolynomialProblem
from contractive_tool.analysis.templates import PolynomialTemplateFactory
from contractive_tool.errors import AnalysisError
from contractive_tool.expectation import ExpectationEngine
from contractive_tool.positivity.ir import Implication


def make_assertion_problem(cfg, evidence, degree, c, *, margin='1/1000000',
                           max_decisions=20000):
    c, delta = sp.Rational(c), sp.Rational(margin)
    if not 0 < c < 1:
        raise AnalysisError('Assertion contraction must lie strictly in (0,1)')
    if not 0 < delta <= 1:
        raise AnalysisError('Assertion positivity margin must lie in (0,1]')
    if cfg.failure_terminal is None:
        raise AnalysisError('Source needs assert/refute to define the failure event')
    ordinary = sorted(set(evidence.locations)-{cfg.normal_terminal, cfg.failure_terminal})
    if len(ordinary)*comb(len(cfg.symbols.program_variables)+degree, degree) > max_decisions:
        raise AnalysisError('Template coefficient budget exceeded before basis expansion')
    template = PolynomialTemplateFactory().instantiate(
        cfg, degree=degree, prefix='eta', locations=ordinary)
    expressions = {loc: poly.expression for loc, poly in template.expressions.items()}
    # H=1. With a uniform lower bound delta, these are the least admissible
    # raw terminal values and therefore suffice without terminal unknowns.
    expressions[cfg.failure_terminal] = sp.Integer(1)
    expressions[cfg.normal_terminal] = delta
    obligations = []
    for loc in ordinary:
        for i, domain in enumerate(evidence.domains[loc]):
            obligations.append(Implication(f'{loc}_raw_positive_{i}', domain,
                expressions[loc]-delta, {'location': loc}, ('raw_positive',)))
    expectation, service = ExpectationEngine(), PolynomialService()
    functions = {loc: service.normalize(expr) for loc, expr in expressions.items()}
    for group in cfg.transitions:
        if group.id not in evidence.group_domains:
            continue
        pre, _ = expectation.transition_expectation(functions, group)
        residual = sp.expand(c*expressions[group.source]-pre.expression)
        for i, domain in enumerate(evidence.group_domains[group.id]):
            obligations.append(Implication(f'{group.id}_raw_contraction_{i}', domain, residual,
                {'location': group.source, 'transition': group.id,
                 'line': group.origin.start_line if group.origin else None},
                ('full_first_moment', 'assertion_violation')))
    initialized = expressions[evidence.start].subs(evidence.initial, simultaneous=True)
    objective = expectation.random_expectation(
        service.normalize(initialized), evidence.initial_random_model).expression
    return PolynomialProblem('assertion_violation', degree, c, expressions,
        list(template.decisions), sp.expand(objective), obligations,
        {'rule': 'positive_first_moment', 'H': '1', 'k': '1',
         'positivity_margin': str(delta), 'raw_terminal_values': {'normal': str(delta), 'failure': '1'},
         'theta_terminal_values': {'normal': '0', 'failure': '1'},
         'prefix_steps': len(evidence.prefix), 'termination_assumed': False,
         'initialization': 'expectation_after_straight_line_prefix'})


def assertion_bound(problem, verified):
    a = sp.Rational(verified['bound_exact'])
    if a < 0:
        raise AnalysisError('Verified initial expectation must be nonnegative')
    return {'degree': problem.degree, 'c': str(problem.c), 'A_exact': str(a),
            'A_numeric': float(a), 'upper_bound_exact': str(min(sp.Integer(1), a)),
            'upper_bound_numeric': float(min(sp.Integer(1), a)),
            'event': 'tau_f < infinity', 'expression': f'min(1, ({a}))',
            'rule': 'positive_first_moment', 'k': '1', 'H': '1',
            'prefix_steps': problem.context['prefix_steps'],
            'time_unit': 'pcfg_transition_after_initialization',
            'late_failure_expression': f'min(1, ({a})*({problem.c})**(n+1))',
            'point_failure_expression': f'min(1, ({a})*({problem.c})**n)',
            'termination_assumed': False}


def evaluate_bound(bound, event='eventual', n=None, clock='after_initialization'):
    a, c = sp.Rational(bound['A_exact']), sp.Rational(bound['c'])
    if event not in ('eventual', 'late_failure', 'point_failure'):
        raise AnalysisError('Unknown assertion event')
    if clock not in ('after_initialization', 'program_entry'):
        raise AnalysisError('Unknown assertion clock')
    if event == 'eventual':
        value, label = a, 'tau_f < infinity'
    else:
        if type(n) is not int or not 0 <= n <= 10000:
            raise AnalysisError('n must be an integer in [0,10000]')
        step = n - (bound['prefix_steps'] if clock == 'program_entry' else 0)
        if event == 'late_failure':
            value, label = a*c**max(0, step+1), 'n < tau_f < infinity'
        else:
            value, label = (sp.Integer(0) if step < 0 else a*c**step), 'tau_f == n'
    value = min(sp.Integer(1), value)
    return {'status': 'proved', 'event': label, 'n': n, 'clock': clock,
            'upper_bound_exact': str(value), 'upper_bound_numeric': float(value),
            'numeric_is_display_only': True, 'c': str(c), 'A_exact': str(a)}
