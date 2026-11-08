#!/usr/bin/env python3
"""Exact rational verification of the five supplied Kelly proof witnesses.

This is a certificate checker for the explicitly encoded transition algebra,
not a general .pp parser, SOS synthesizer, or proof-assistant kernel. All
inequalities are proved on entire domains; no sampling or floating arithmetic
is used. A source digest ties each certificate to its supplied .pp file.
"""

from fractions import Fraction as F
from hashlib import sha256
from math import comb
from pathlib import Path
import json
import sys


ROOT = Path(__file__).resolve().parent
EVIDENCE = []


def require(condition, message):
    if not condition:
        raise ValueError(message)


def poly(*coefficients):
    result = [F(c) for c in coefficients]
    while len(result) > 1 and result[-1] == 0:
        result.pop()
    return tuple(result or [F(0)])


def add(a, b):
    return poly(*( (a[i] if i < len(a) else F(0))
                 + (b[i] if i < len(b) else F(0))
                 for i in range(max(len(a), len(b))) ))


def scale(a, c):
    return poly(*(F(c) * x for x in a))


def sub(a, b):
    return add(a, scale(b, -1))


def mul(a, b):
    result = [F(0)] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            result[i+j] += x*y
    return poly(*result)


def expectation(branches, square=False):
    result = poly(0)
    for probability, transition in branches:
        result = add(result, scale(mul(transition, transition)
                                  if square else transition, probability))
    return result


def identity(left, right, label):
    require(poly(*left) == poly(*right), label)
    EVIDENCE.append({'kind': 'polynomial_identity', 'label': label})


def nonnegative_interval(p, lower, upper, label):
    """Prove p>=0 using exact nonnegative Bernstein coefficients on [l,u].

    For t=(w-l)/(u-l), p(w)=sum b_j*C(n,j)*t^j*(1-t)^(n-j).
    Every basis term is nonnegative for 0<=t<=1. Thus b_j>=0 proves
    the inequality for every real point of the interval.
    """
    lower, upper = F(lower), F(upper)
    require(lower < upper, label + ': bad interval')
    degree = len(p) - 1
    power = [sum((p[j] * comb(j, i) * lower**(j-i)
                  * (upper-lower)**i for j in range(i, degree+1)), F(0))
             for i in range(degree+1)]
    bernstein = [sum((power[i] * F(comb(j, i), comb(degree, i))
                      for i in range(j+1)), F(0))
                 for j in range(degree+1)]
    require(all(b >= 0 for b in bernstein), label + ': negative coefficient')
    EVIDENCE.append({'kind': 'nonnegative_bernstein', 'label': label,
                     'interval': [str(lower), str(upper)],
                     'coefficients': [str(b) for b in bernstein]})


W = poly(0, 1)
W2 = mul(W, W)


def interval_program(record, branches, guard, invariant):
    lower, upper = map(F, guard)
    inv_lower, inv_upper = map(F, invariant)
    initial = F(record['initial']['wealth'])
    require(inv_lower <= initial <= inv_upper, record['id'] + ': initial invariant')
    require(lower <= initial < upper, record['id'] + ': initial active')
    require(sum(p for p, _ in branches) == 1, record['id'] + ': probabilities')
    require(all(p > 0 for p, _ in branches), record['id'] + ': positive probabilities')
    for i, (_, update) in enumerate(branches):
        nonnegative_interval(sub(update, poly(inv_lower)), lower, upper,
                             record['id'] + ': branch ' + str(i) + ' lower invariant')
        nonnegative_interval(sub(poly(inv_upper), update), lower, upper,
                             record['id'] + ': branch ' + str(i) + ' upper invariant')
    if record['mode'] == 'positive':
        nonnegative_interval(W, inv_lower, inv_upper,
                             record['id'] + ': eta nonnegative on invariant')
        nonnegative_interval(sub(W, poly(record['a'])), lower, upper,
                             record['id'] + ': eta>=a in loop')
        nonnegative_interval(sub(scale(W, record['c']), expectation(branches)),
                             lower, upper, record['id'] + ': first-moment contraction')
        require(0 < F(record['c']) < 1, record['id'] + ': c range')
        require(F(record['q_certified']) == F(record['c']), record['id'] + ': q=c')
        require(F(record['prefactor']) == initial/F(record['a']),
                record['id'] + ': positive prefactor')
    else:
        require(lower > 0, record['id'] + ': eta positive in loop')
        nonnegative_interval(sub(poly(record['b']), W), lower, upper,
                             record['id'] + ': eta<=b in loop')
        c, second, support = (F(record[key]) for key in ['c', 'D', 'r0'])
        require(c > 1 and 0 < support < c and second >= c*c,
                record['id'] + ': moment scalar assumptions')
        nonnegative_interval(sub(expectation(branches), scale(W, c)), lower, upper,
                             record['id'] + ': first-moment growth')
        nonnegative_interval(sub(scale(W2, second), expectation(branches, square=True)),
                             lower, upper, record['id'] + ': second-moment upper bound')
        for i, (_, update) in enumerate(branches):
            nonnegative_interval(sub(update, scale(W, support)), lower, upper,
                                 record['id'] + ': branch ' + str(i) + ' support')
        p_star = (second-c*c)/(second-2*support*c+support*support)
        z_star = (second-support*c)/(c-support)
        require(F(record['p_star']) == p_star, record['id'] + ': p_star')
        require(F(record['z_star']) == z_star, record['id'] + ': z_star')
        require(0 <= p_star < 1 and z_star >= c > support,
                record['id'] + ': extremal support')
        require(p_star*support + (1-p_star)*z_star == c,
                record['id'] + ': extremal mean')
        require(p_star*support**2 + (1-p_star)*z_star**2 == second,
                record['id'] + ': extremal second moment')
        if record['k'] == '1':
            q = p_star/support + (1-p_star)/z_star
            require(q == F(record['q_mom']) == F(record['q_certified']),
                    record['id'] + ': rational negative moment')
            require(0 < q < 1, record['id'] + ': strict negative contraction')
            require(F(record['prefactor']) == F(record['b'])/initial,
                    record['id'] + ': reciprocal prefactor')


def check_k1(record):
    branches = [(F(2, 5), poly(0, 1, F(1, 8))),
                (F(3, 5), poly(0, 1, F(-1, 8)))]
    interval_program(record, branches, ('1/2', '2'), ('15/32', '5/2'))
    identity(sub(scale(W, F(79, 80)), expectation(branches)),
             scale(mul(W, poly(F(-1, 2), 1)), F(1, 40)),
             'K1: explicit contraction witness')


def check_k2(record):
    # Every linear form is checked on the nonnegative (x,y) cone.
    branches = [(F(1, 2), (F(6, 5), F(7, 10))),
                (F(1, 2), (F(7, 10), F(6, 5)))]
    lower, upper = F(1, 2), F(4)
    minimum, maximum = F(7, 10), F(6, 5)
    c = F(record['c'])
    require(0 < c < 1 and c == F(record['q_certified']), 'K2: contraction scalar')
    for j in range(2):
        require(sum(p*coefficients[j] for p, coefficients in branches) == c,
                'K2: expected coefficient')
    for _, (u, v) in branches:
        for coefficients in [(u, F(1)), (u, v)]:
            require(all(minimum <= coefficient <= maximum for coefficient in coefficients),
                    'K2: sequential nonnegative coefficient bounds')
    # Stronger branch-specific annotations make each local Hoare implication
    # valid even when the frontend treats annotations as independent cutpoints.
    for branch_index, (_, (u, v)) in enumerate(branches):
        intermediate_lower = min(u, F(1))*lower
        intermediate_upper = max(u, F(1))*upper
        require(min(F(1), v)*intermediate_lower >= F(7, 20),
                'K2: local second assignment lower implication')
        require(max(F(1), v)*intermediate_upper <= F(24, 5),
                'K2: local second assignment upper implication')
        expected_intermediate = [(F(1, 2), F(24, 5)), (F(7, 20), F(4))][branch_index]
        require((intermediate_lower, intermediate_upper) == expected_intermediate,
                'K2: branch-specific intermediate annotation')
        EVIDENCE.append({'kind': 'local_annotation_implication',
                         'label': 'K2: branch ' + str(branch_index) + ' sequential assignment',
                         'intermediate_total_range': [str(intermediate_lower), str(intermediate_upper)]})
    require(minimum*lower == F(7, 20), 'K2: lower invariant')
    require(maximum*upper == F(24, 5), 'K2: upper invariant')
    initial = sum(F(value) for value in record['initial'].values())
    require(lower <= initial < upper, 'K2: initial active')
    require(F(record['a']) == lower, 'K2: normalization threshold')
    require(F(record['prefactor']) == initial/lower, 'K2: prefactor')
    EVIDENCE.append({'kind': 'nonnegative_cone_linear_identity',
                     'label': 'K2: expected total coefficient 19/20; all sequential coefficients in [7/10,6/5]'})


def check_k3(record):
    branches = [(F(4, 5), poly(0, F(8, 5))),
                (F(1, 5), poly(0, F(2, 5)))]
    interval_program(record, branches, ('1/4', '4'), ('1/10', '32/5'))
    probability, r, z = F(record['p_star']), F(record['r0']), F(record['z_star'])
    require(record['k'] == '1/2' and z == 4*r, 'K3: fractional-power algebra')
    # sqrt(z)=2*sqrt(r), so q=(p+(1-p)/2)/sqrt(r).
    q_squared = (probability+(1-probability)/2)**2/r
    require(q_squared == F(9, 10) == F(record['q_mom_squared']),
            'K3: exact q_mom squared')
    q_upper = F(record['q_certified'])
    require(0 < q_upper < 1 and q_squared <= q_upper*q_upper,
            'K3: rigorous rational upper bound')
    require(probability/r + (1-probability)/z == 1, 'K3: k=1 failure')
    for _, update in branches:
        successor = sum(update)  # evaluation at wealth=1
        require(F(1, 4) <= successor < 4, 'K3: both successors continue at wealth=1')
    require(F(record['prefactor'])**2 == F(record['b'])/F(record['eta0']),
            'K3: exact square-root prefactor')
    EVIDENCE.append({'kind': 'exact_algebraic_comparison',
                     'label': 'K3: q_mom(1/2)^2=9/10 < (19/20)^2; rho_-(1)=1'})


def check_k4(record):
    branches = [(F(4, 5), poly(F(1, 8), F(5, 4))),
                (F(1, 5), poly(F(1, 8), F(7, 8)))]
    interval_program(record, branches, ('1', '4'), ('1', '41/8'))
    identity(sub(expectation(branches), scale(W, F(193, 160))),
             scale(poly(4, -1), F(1, 32)), 'K4: explicit mean witness')
    identity(sub(scale(W2, F(137, 80)), expectation(branches, square=True)),
             scale(mul(poly(-1, 1), poly(5, 99)), F(1, 320)),
             'K4: explicit second-moment witness')


def check_k5(record):
    branches = [(F(9, 10), poly(0, F(9, 8), F(1, 16))),
                (F(1, 10), poly(0, F(7, 8), F(-1, 16)))]
    interval_program(record, branches, ('1', '2'), ('13/16', '5/2'))
    identity(sub(expectation(branches), scale(W, F(23, 20))),
             scale(mul(W, poly(-1, 1)), F(1, 20)), 'K5: explicit mean witness')
    identity(sub(scale(W2, F(117, 80)), expectation(branches, square=True)),
             scale(mul(mul(W2, poly(2, -1)), poly(158, 5)), F(1, 1280)),
             'K5: explicit second-moment witness')
    residual = sub(scale(W2, F(117, 80)), expectation(branches, square=True))
    lower_guard, upper_guard = poly(-1, 1), poly(2, -1)
    range_polynomial = mul(lower_guard, upper_guard)
    nonnegative_interval(range_polynomial, 1, 2,
                         'K5: redundant range polynomial on active domain only')
    w_lower, w_upper = mul(W, lower_guard), mul(W, upper_guard)
    degree_five = scale(add(
        mul(add(scale(W2, 163), scale(mul(w_lower, w_lower), 5)), upper_guard),
        mul(scale(mul(w_upper, w_upper), 5), lower_guard)), F(1, 1280))
    identity(residual, degree_five,
             'K5: degree-four multipliers with degree-five product cancellation')
    degree_four = scale(add(scale(mul(w_upper, w_upper), 163),
                            scale(mul(W2, range_polynomial), 168)), F(1, 1280))
    identity(residual, degree_four,
             'K5: degree-four Markov-Lukacs range-polynomial witness')


def main():
    records = json.loads((ROOT/'certificates.json').read_text(encoding='utf-8'))
    require([record['id'] for record in records] == ['K1', 'K2', 'K3', 'K4', 'K5'],
            'Unexpected certificate list')
    functions = {'K1': check_k1, 'K2': check_k2, 'K3': check_k3,
                 'K4': check_k4, 'K5': check_k5}
    reports = []
    for record in records:
        actual = sha256((ROOT/record['file']).read_bytes()).hexdigest()
        require(actual == record['source_sha256'], record['id'] + ': source digest mismatch')
        start = len(EVIDENCE)
        functions[record['id']](record)
        reports.append({'id': record['id'], 'status': 'PASS',
                        'mode': record['mode'], 'q_certified': record['q_certified'],
                        'evidence': EVIDENCE[start:]})
    if '--json' in sys.argv:
        print(json.dumps({'arithmetic': 'exact rational', 'reports': reports}, indent=2))
    else:
        for report in reports:
            print(report['id'] + ' PASS: ' + report['mode']
                  + ', q=' + report['q_certified']
                  + ', ' + str(len(report['evidence'])) + ' exact proof records')
        print('All 5 Kelly certificates verified on their entire annotated domains.')


if __name__ == '__main__':
    main()
