"""Check the independent experiment's aggregation against explicit paths."""
from fractions import Fraction
from itertools import product
from pathlib import Path
import runpy


def test_exact_reference_matches_enumeration_and_bounds_surviving_mass():
    script = Path(__file__).resolve().parents[2]/'examples/kelly_exit_reference.py'
    enclose = runpy.run_path(str(script))['enclose']
    failure = surviving = Fraction(0)
    for sequence in product((False, True), repeat=8):
        wins = sum(sequence)
        weight = Fraction(3**wins*2**(8-wins), 5**8)
        wealth = Fraction(1)
        for win in sequence:
            if wealth < Fraction(1,2) or wealth >= 2:
                break
            wealth *= Fraction(6,5) if win else Fraction(4,5)
        if wealth < Fraction(1,2):
            failure += weight
        elif wealth < 2:
            surviving += weight
    reference = enclose(8)
    assert Fraction(reference['probability_lower_exact']) == failure
    assert Fraction(reference['probability_upper_exact']) == failure+surviving
    assert Fraction(enclose(4)['probability_lower_exact']) == Fraction(16,625)
    later = enclose(100)
    assert failure <= Fraction(later['probability_lower_exact']) <= Fraction(later['probability_upper_exact']) <= failure+surviving
