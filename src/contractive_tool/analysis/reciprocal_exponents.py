"""Numerical derivative bisection proposes k; exact power checks certify it.

The derivative of log(q) and of k*log(b)+n*log(q) is monotone.
Floating/high-precision signs guide search only, never establish a tail bound
or a mathematical impossibility result. Legacy grid candidates are retained.
"""
import mpmath as mp
import sympy as sp

from contractive_tool.probability.fractional_moments import rational


def propose_exponents(b, c, D, r0, options):
    values = list(dict.fromkeys(map(rational, options.k_values)))
    if not options.adaptive_k:
        return values, []
    b, c, D, r0 = map(rational, (b, c, D, r0))
    p = (D-c*c)/(D-2*r0*c+r0*r0)
    z = (D-r0*c)/(c-r0)
    upper = rational(options.k_upper)
    # Keep both numerator and denominator within the exact-power budget.
    denominator = min(options.k_denominator, int(2048/sp.ceiling(upper)))
    audit = []

    def add_neighbours(value):
        center = int(sp.floor(value*denominator))
        for i in (center-1, center, center+1):
            k = sp.Rational(i, denominator)
            if 0 < k <= upper and k not in values:
                values.append(k)

    def number(value):
        return mp.mpf(int(value.p))/int(value.q)

    with mp.workdps(60):
        lr, lz, lb = mp.log(number(r0)), mp.log(number(z)), mp.log(number(b))
        probability = number(p)

        def slope(k):
            if p == 0:
                return -lz
            weight = 1/(1+(1-probability)/probability*mp.exp(number(k)*(lr-lz)))
            return -weight*lr-(1-weight)*lz

        for n in (None, *dict.fromkeys(options.target_ns)):
            def derivative(k):
                return slope(k) if n is None else lb+n*slope(k)

            label = 'decay' if n is None else f'tail_n_{n}'
            left, right = sp.Integer(0), min(sp.Integer(1), upper)
            if derivative(left) >= 0:
                # A numerical diagnostic, not a certified no-contraction claim.
                audit.append({'objective': label, 'status': 'nonnegative_initial_derivative',
                              'signs': 'numerical_proposals_only'})
                add_neighbours(sp.Rational(1, denominator))
                continue
            while right < upper and derivative(right) < 0:
                left, right = right, min(2*right, upper)
            if derivative(right) <= 0:
                audit.append({'objective': label, 'status': 'upper_boundary', 'k': str(upper),
                              'signs': 'numerical_proposals_only'})
                add_neighbours(upper)
                continue
            for _ in range(options.k_steps):
                midpoint = (left+right)/2
                if derivative(midpoint) < 0:
                    left = midpoint
                else:
                    right = midpoint
            audit.append({'objective': label, 'status': 'bracketed',
                          'lower': str(left), 'upper': str(right),
                          'signs': 'numerical_proposals_only'})
            add_neighbours((left+right)/2)
    return values, audit
