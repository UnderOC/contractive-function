"""Rebuild reciprocal obligations from source evidence, without a solver."""
import sympy as sp

from contractive_tool.analysis.cauchy import EtaTemplate
from contractive_tool.analysis.cauchy_expressions import parse_expression
from contractive_tool.analysis.reciprocal import (
    ReciprocalOptions, build_denominator_model, build_moment_model,
    exact_substitution, exponent_candidates)
from contractive_tool.analysis.reciprocal_feedback import propose_parameters
from contractive_tool.backends.cvxpy.verification import check_conic_values
from contractive_tool.errors import AnalysisError
from contractive_tool.positivity.base import EncodingLimits
from contractive_tool.probability.fractional_moments import rational


def verify_result(round_, result):
    try:
        if (result['schema_version'] not in (1, 2) or result['method'] != 'reciprocal_low_order_moments'
                or result['round'] != round_.to_data() or result['status'] != 'proved'):
            raise AnalysisError('Source evidence, method or status mismatch')
        if result.get('special_case') == 'initially_exited':
            if round_.initial_active or result['candidates'] or result['attempts']:
                raise AnalysisError('Incorrect initial-exit certificate')
            return {'status': 'proved', 'method': 'source_replay_initially_exited'}
        if not round_.initial_active or result.get('special_case') is not None:
            raise AnalysisError('Incorrect active-state certificate')
        settings = dict(result['options'])
        settings.setdefault('feedback_points', 0)
        if result['schema_version'] == 1:
            settings.setdefault('adaptive_k', False)
        settings['limits'] = EncodingLimits(**settings['limits'])
        options = ReciprocalOptions(**settings)
        options.validate()
        inputs = result['input']
        coefficients = tuple(map(sp.Symbol, inputs['coefficients']))
        template = EtaTemplate(parse_expression(inputs['eta'], round_.variables+coefficients), coefficients)
        expected = []
        stage_count = 0
        verified_parents = set()
        if sum(a.get('origin') == 'feedback' for a in result['attempts']) > options.feedback_points:
            raise AnalysisError('Feedback point budget exceeded')

        def check(stage, model, kind):
            nonlocal stage_count
            if stage['kind'] != kind or stage['status'] != 'proved' or stage['model'] != model.to_data():
                raise AnalysisError('Rebuilt reciprocal model differs from artifact')
            if not check_conic_values(model, stage['verification']['exact_values']):
                raise AnalysisError('Exact reciprocal conic verification failed')
            sub = exact_substitution(stage)
            if rational(stage['verification']['bound_exact']) != model.objective.xreplace(sub):
                raise AnalysisError('Incorrect conic objective')
            stage_count += 1
            return sub

        for index, attempt in enumerate(result['attempts']):
            if attempt['status'] not in ('proved', 'no_contraction'):
                continue
            c_seed, r_seed = attempt['seed_c'], attempt['seed_r0']
            D_seed = None if attempt.get('seed_D') is None else rational(attempt['seed_D'])
            b_cap = None if attempt.get('b_cap') is None else rational(attempt['b_cap'])
            origin = attempt.get('origin', 'grid')
            if origin == 'feedback':
                metadata = attempt['feedback']
                parent = metadata['parent']
                if (not coefficients or parent not in verified_parents or parent >= index
                        or metadata['target_n'] != max(options.target_ns) or D_seed is None):
                    raise AnalysisError('Invalid feedback parent/target')
                proposal = propose_parameters(result['attempts'][parent], metadata['direction'], metadata['step'])
                if any(attempt[key] != value for key, value in proposal.items()):
                    raise AnalysisError('Feedback parameters differ from parent proposal')
                c_seed, r_seed = rational(c_seed), rational(r_seed)
            elif origin != 'grid':
                raise AnalysisError('Unknown reciprocal attempt origin')
            elif coefficients:
                c_seed, r_seed = rational(c_seed), rational(r_seed)
                if (c_seed not in map(rational, options.growth_values)
                        or r_seed not in map(rational, options.support_values) or r_seed >= c_seed):
                    raise AnalysisError('Unlisted synthesis parameters')
                if D_seed is not None and D_seed not in map(rational, options.moment_values):
                    raise AnalysisError('Unlisted second-moment parameter')
            elif c_seed is not None or r_seed is not None:
                raise AnalysisError('Fixed denominator must not have synthesis parameters')
            if (b_cap is not None and origin != 'feedback') or (not coefficients and D_seed is not None):
                raise AnalysisError('Unexpected seed/bound cap')
            stages = attempt['stages']
            if len(stages) != 4:
                raise AnalysisError('Incomplete reciprocal proof chain')
            model, eta, b_symbol = build_denominator_model(round_, template, options, c_seed, r_seed, D_seed, b_cap)
            sub = check(stages[0], model, 'denominator')
            eta, b = sp.expand(eta.xreplace(sub)), rational(b_symbol.xreplace(sub))
            constants = {} if D_seed is None else {'c': c_seed, 'r0': r_seed, 'D': D_seed}
            for stage, kind in zip(stages[1:], ('c', 'r0', 'D')):
                if stage['kind'] != kind:
                    raise AnalysisError('Incorrect moment stage order')
                if stage['status'] != 'proved' and D_seed is not None:
                    continue
                model, parameter = build_moment_model(round_, eta, kind, options, c=constants.get('c'))
                sub = check(stage, model, kind)
                value = rational(parameter.xreplace(sub))
                if kind in constants:
                    value = (min if kind == 'D' else max)(value, constants[kind])
                constants[kind] = value
            if (attempt['eta'] != str(eta) or attempt['b'] != str(b)
                    or attempt['constants'] != {k: str(v) for k, v in constants.items()}):
                raise AnalysisError('Denominator/moment metadata differs from proof')
            verified_parents.add(index)
            candidates, history = exponent_candidates(eta, b, **constants, options=options)
            if attempt['exponent_history'] != history or (attempt['status'] == 'proved') != bool(candidates):
                raise AnalysisError('Incorrect exponent search history')
            for candidate in candidates:
                candidate['attempt'] = index
            expected.extend(candidates)
        if not expected or result['candidates'] != expected:
            raise AnalysisError('Tail formula/power witnesses differ from verified obligations')
        return {'status': 'proved', 'conic_certificates': stage_count,
                'tail_certificates': len(expected),
                'method': 'source_replay_exact_conic_and_outward_rational_powers'}
    except (AnalysisError, ValueError, TypeError, KeyError, IndexError, sp.PolynomialError) as error:
        return {'status': 'verification_failed', 'reason': str(error)}
