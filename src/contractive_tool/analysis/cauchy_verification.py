"""Replay Cauchy proof obligations and check artifacts without a solver."""
import sympy as sp

from contractive_tool.analysis.cauchy import (
    CauchyOptions, ExponentOptions, EtaTemplate, build_fixed_model,
    build_template_model, verify_exponent)
from contractive_tool.backends.cvxpy.verification import check_conic_values
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.base import EncodingLimits
from contractive_tool.probability.fractional_moments import rational
from contractive_tool.analysis.cauchy_expressions import parse_expression


def verify_result(round_, result):
    """Rebuild state obligations from the supplied (source-replayed) round.

The stored conic model, candidate eta/B/initial value, random basis and moment
witnesses are all bound together. Solver statuses alone are never evidence.
"""
    try:
        if result['schema_version'] != 1 or result['round'] != round_.to_data():
            return {'status': 'verification_failed', 'reason': 'round_evidence_mismatch'}
        if result['status'] != 'proved':
            return {'status': 'verification_failed', 'reason': 'no_proved_result'}
        if result.get('special_case') == 'initially_exited':
            return {'status': 'proved' if not round_.initial_active and not result['candidates'] else 'verification_failed'}
        settings = dict(result['options'])
        settings['limits'] = EncodingLimits(**settings['limits'])
        settings['exponents'] = ExponentOptions(**settings['exponents'])
        options = CauchyOptions(**settings)
        options.validate()
        inputs = result['input']
        basis = None if inputs['basis'] is None else tuple(parse_expression(b, round_.law.symbols) for b in inputs['basis'])
        coefficients = tuple(map(sp.Symbol, inputs.get('coefficients', ())))
        eta = parse_expression(inputs['eta'], round_.variables+coefficients)
        proven = {}
        for index, attempt in enumerate(result['attempts']):
            if attempt['status'] != 'proved':
                continue
            if result['mode'] == 'fixed_eta':
                model, data = build_fixed_model(round_, eta, basis=basis, options=options)
            elif result['mode'] == 'template_eta':
                template = EtaTemplate(eta, coefficients,
                    tuple(parse_expression(e, coefficients) for e in inputs['nonnegative']),
                    tuple(parse_expression(e, coefficients) for e in inputs['equalities']))
                t = rational(attempt['t'])
                if str(t) not in inputs['t_values']:
                    raise AnalysisError('Unlisted t parameter')
                model, data = build_template_model(round_, template, t, basis=basis, options=options)
            else:
                raise AnalysisError('Unknown Cauchy artifact mode')
            if model.to_data() != attempt['model']:
                raise AnalysisError('Conic model differs from rebuilt obligations')
            verification = attempt['verification']
            if not check_conic_values(model, verification['exact_values']):
                raise AnalysisError('Exact conic constraints failed')
            sub = {sp.Symbol(n): rational(v) for n, v in verification['exact_values'].items()}
            if rational(verification['bound_exact']) != model.objective.xreplace(sub):
                raise AnalysisError('Incorrect state objective')
            concrete = sp.expand(data['eta'].xreplace(sub))
            B = data['B_symbol'].xreplace(sub) if result['mode'] == 'fixed_eta' else t*t
            A = rational(concrete.subs(round_.initial, simultaneous=True))
            if (B < 0 or A < 1 or sp.expand(concrete-parse_expression(attempt['eta'], round_.variables)) != 0
                    or rational(attempt['B']) != B or rational(attempt['base_initial']) != A
                    or attempt['basis'] != list(map(str, data['basis']))
                    or attempt['q'] != list(map(str, data['q']))):
                raise AnalysisError('State certificate metadata mismatch')
            proven[index] = (concrete, B, A, round_.law.norm_atoms(data['basis']))
        if result.get('special_case') == 'one_step_termination':
            if result['mode'] != 'fixed_eta' or not any(B == 0 for _, B, _, _ in proven.values()):
                raise AnalysisError('Missing zero norm certificate')
        elif not result['candidates']:
            raise AnalysisError('Missing fractional certificates')
        for c in result['candidates']:
            concrete, B, A, norms = proven[c['attempt']]
            if (sp.expand(parse_expression(c['eta'], round_.variables)-concrete) != 0 or rational(c['B']) != B
                    or rational(c['base_initial']) != A or not verify_exponent(c, norms)
                    or rational(c['k']) not in options.exponents.candidates()
                    or rational(c['decay_upper']) > 1-rational(options.exponents.margin)
                    or c['event'] != 'K > n' or c['time_unit'] != 'completed_loop_iterations'):
                raise AnalysisError('Fractional certificate differs from verified state model')
            if result['mode'] == 'template_eta' and rational(c['t'])**2 != B:
                raise AnalysisError('Incorrect candidate t')
            C, rho = rational(c['prefactor_upper']), rational(c['decay_upper'])
            if (c['expression'] != f'min(1, ({C})*({rho})**n)'
                    or c['n_domain'] != 'nonnegative integers'):
                raise AnalysisError('Incorrect displayed tail formula')
            if 'target_n' in c:
                n = c['target_n']
                if n != options.exponents.target_n or rational(c['target_upper']) != min(
                        sp.Integer(1), rational(c['prefactor_upper'])*rational(c['decay_upper'])**n):
                    raise AnalysisError('Incorrect target evaluation')
        if result['selection'] is not None:
            n = options.exponents.target_n
            if n is None or not result['candidates']:
                raise AnalysisError('Selection without a target/candidate')
            values = [rational(c['prefactor_upper'])*rational(c['decay_upper'])**n for c in result['candidates']]
            if result['selection'] != min(range(len(values)), key=values.__getitem__):
                raise AnalysisError('Incorrect target selection')
        return {'status': 'proved', 'state_certificates': len(proven),
                'fractional_certificates': len(result['candidates']),
                'method': 'source_round_replay_exact_conic_and_rational_power_checks'}
    except (KeyError, TypeError, ValueError, IndexError, AnalysisError, sp.PolynomialError) as error:
        return {'status': 'verification_failed', 'reason': str(error)}
