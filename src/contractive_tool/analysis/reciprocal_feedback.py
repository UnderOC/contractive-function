"""Bounded local parameter proposals for reciprocal denominator synthesis.

Every proposal is independently certified by the matrix/state models. Search
failures only shrink a local step; they never establish an infeasible interval.
"""
import math
import sympy as sp

from contractive_tool.errors import AnalysisError
from contractive_tool.probability.fractional_moments import rational


DIRECTIONS = ('growth', 'variance', 'support')


def propose_parameters(parent, direction, step):
    step = rational(step)
    if direction not in DIRECTIONS or not 0 < step <= sp.Rational(1, 2):
        raise AnalysisError('Invalid feedback direction/step')
    c, D, r = (rational(parent['constants'][key]) for key in ('c', 'D', 'r0'))
    b = rational(parent['b'])
    if not (b >= 1 and c > 1 and D >= c*c and r > 0):
        raise AnalysisError('Feedback requires a verified positive moment certificate')
    r = min(r, c/2) if r >= c else r
    if direction == 'growth':
        new_c, new_r = 1+(c-1)*(1+step), r*(1-step)
        new_D = 1+(D-1)*(1+step)
    elif direction == 'variance':
        new_c, new_r = 1+(c-1)*(1-step), r*(1-step)
        new_D = 1+(D-1)*(1-step)
    else:
        new_c = 1+(c-1)*(1-step)
        new_r = min(r+(c-r)*step, (r+new_c)/2)
        new_D = 1+(D-1)*(1+step)
    # Rational quantization bounds coefficient size and introduces no guessed
    # proof: the eventual constraints use exactly these quantized parameters.
    scale = sp.Integer(10**6)
    new_c = sp.floor(new_c*scale)/scale
    new_r = min(sp.floor(new_r*scale)/scale, new_c-sp.Rational(1, scale))
    new_D = sp.ceiling(max(new_D, new_c**2)*scale)/scale
    cap = sp.ceiling(b*(1+step)*scale)/scale
    if not (new_c > 1 and new_r > 0):
        raise AnalysisError('Feedback precision exhausted')
    return {'seed_c': str(new_c), 'seed_r0': str(new_r), 'seed_D': str(new_D), 'b_cap': str(cap)}


def candidate_value(candidate, n):
    return rational(candidate['prefactor_upper'])*rational(candidate['decay_upper'])**n


def choose_parent(result, n):
    """Prefer the best certified full tail; try no-contraction moments if needed."""
    if result['candidates']:
        best = min(result['candidates'], key=lambda c: candidate_value(c, n))
        return best['attempt']
    ranked = []
    for i, attempt in enumerate(result['attempts']):
        if attempt['status'] != 'no_contraction':
            continue
        c, D, r = (rational(attempt['constants'][key]) for key in ('c', 'D', 'r0'))
        if not (c > 1 and D >= c*c and r > 0):
            continue
        # Numerical score is only for choosing which certified state model to
        # revisit, not evidence of contraction or impossibility.
        b = float(rational(attempt['b']))
        scores = [float(rational(row['k']))*math.log(b)+n*math.log(float(rational(row['q_upper'])))
                  for row in attempt.get('exponent_history', ()) if 'q_upper' in row]
        if scores:
            ranked.append((min(scores), i))
    return min(ranked)[1] if ranked else None


def feedback_search(result, attempt_point, options, deadline, clock):
    n = max(options.target_ns)
    steps = dict.fromkeys(DIRECTIONS, rational(options.feedback_step))
    seen = {(a.get('seed_c'), a.get('seed_r0'), a.get('seed_D'), a.get('b_cap'))
            for a in result['attempts']}
    history = result.setdefault('feedback_history', [])
    for iteration in range(options.feedback_points):
        if clock() >= deadline:
            result['feedback_stop_reason'] = 'time_budget'
            break
        parent_index = choose_parent(result, n)
        if parent_index is None:
            result['feedback_stop_reason'] = 'no_verified_moment_parent'
            break
        direction = DIRECTIONS[iteration % len(DIRECTIONS)]
        step = steps[direction]
        try:
            proposal = propose_parameters(result['attempts'][parent_index], direction, step)
        except AnalysisError:
            steps[direction] /= 2
            history.append({'iteration': iteration, 'status': 'precision_exhausted', 'direction': direction})
            continue
        key = tuple(proposal[k] for k in ('seed_c', 'seed_r0', 'seed_D', 'b_cap'))
        if key in seen:
            steps[direction] /= 2
            history.append({'iteration': iteration, 'status': 'duplicate_skipped', 'direction': direction})
            continue
        seen.add(key)
        old_best = min((candidate_value(c, n) for c in result['candidates']), default=None)
        index = len(result['attempts'])
        attempt = attempt_point(*(rational(proposal[k]) for k in ('seed_c', 'seed_r0', 'seed_D')),
            b_cap=rational(proposal['b_cap']), origin='feedback', point_deadline=deadline)
        attempt['feedback'] = {'parent': parent_index, 'direction': direction, 'step': str(step), 'target_n': n}
        new_best = min((candidate_value(c, n) for c in result['candidates']), default=None)
        improved = bool(new_best is not None and (old_best is None or new_best < old_best))
        history.append({'iteration': iteration, 'attempt': index, 'parent': parent_index,
                        'direction': direction, 'step': str(step), 'target_n': n,
                        'status': attempt['status'], 'improved': improved})
        if not improved:
            steps[direction] /= 2
    else:
        result['feedback_stop_reason'] = 'point_budget'
