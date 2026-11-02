"""Exact independent probability enclosure for kelly_double_bound.pp.

This experiment is not part of the certificate synthesis pipeline. At round n,
wealth is (6**wins * 4**(n-wins))/5**n and path weights have denominator 5**n.
Only paths still in [1/2,2) are propagated. Failure-so-far is a lower bound;
adding all surviving mass is an upper bound without any termination assumption.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def enclose(rounds):
    if type(rounds) is not int or not 0 <= rounds <= 2000:
        raise ValueError('rounds must be in [0,2000]')
    active, lower_exit, upper_exit, denominator = {0: 1}, 0, 0, 1
    for n in range(1, rounds+1):
        denominator *= 5
        lower_exit *= 5
        upper_exit *= 5
        following = {}
        for wins, weight in active.items():
            for new_wins, weighted in ((wins+1, 3*weight), (wins, 2*weight)):
                numerator = 6**new_wins * 4**(n-new_wins)
                if 2*numerator < denominator:
                    lower_exit += weighted
                elif numerator >= 2*denominator:
                    upper_exit += weighted
                else:
                    following[new_wins] = following.get(new_wins, 0)+weighted
        active = following
        assert lower_exit+upper_exit+sum(active.values()) == denominator
    remaining = sum(active.values())
    lower, upper = Fraction(lower_exit, denominator), Fraction(lower_exit+remaining, denominator)
    scale = 10**15
    floor = lower.numerator*scale//lower.denominator
    ceil = -(-upper.numerator*scale//upper.denominator)

    def decimal(integer):
        return f'{integer//scale}.{integer%scale:015d}'

    return {'method': 'exact_integer_path_weights_with_survival_remainder',
            'event': 'finite exit with wealth < 0.5', 'rounds': rounds,
            'probability_lower_exact': str(lower), 'probability_upper_exact': str(upper),
            'probability_lower_decimal': decimal(floor), 'probability_upper_decimal': decimal(ceil),
            'remaining_mass_exact': str(Fraction(remaining, denominator)),
            'remaining_mass_numeric': float(Fraction(remaining, denominator)),
            'probability_numeric_display_only': float(lower)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rounds', type=int, default=1000)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = enclose(args.rounds)
    source = Path(__file__).resolve().parents[1]/'kelly_double_bound.pp'
    result['source_sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if not k.endswith('_exact')}))
