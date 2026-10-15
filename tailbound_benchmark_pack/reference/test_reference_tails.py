"""Independent small-case checks, including brute-force path enumeration."""
from fractions import Fraction
from itertools import product
from math import comb
import unittest
from reference_tails import coupon_tails, walk_tails, polynomial_tails


class ExactTailTests(unittest.TestCase):
    def test_coupon2_closed_form(self):
        for n, q in coupon_tails(2, 50):
            self.assertEqual(q, Fraction(1) if n == 0 else Fraction(1, 2 ** (n - 1)))

    def test_coupon_inclusion_exclusion(self):
        for N in (1, 2, 4, 6):
            for n, q in coupon_tails(N, 20):
                formula = sum(((-1) ** (j + 1) * comb(N, j) * Fraction(N - j, N) ** n
                               for j in range(1, N + 1)), Fraction(0))
                self.assertEqual(q, formula)

    def test_coupon_brute_force(self):
        for N in (2, 4):
            for n, q in coupon_tails(N, 5):
                uncollected = sum(len(set(path)) < N for path in product(range(N), repeat=n))
                self.assertEqual(q, Fraction(uncollected, N**n))

    def test_walk_small_values(self):
        values = dict(walk_tails(1, Fraction(3, 5), 3))
        self.assertEqual(values, {0: Fraction(1), 1: Fraction(2, 5),
                                 2: Fraction(2, 5), 3: Fraction(32, 125)})

    def test_walk_brute_force(self):
        for start in (0, 1, 3):
            for p in (Fraction(3, 5), Fraction(1, 2), Fraction(0), Fraction(1)):
                for n, q in walk_tails(start, p, 8):
                    exact = Fraction(0)
                    for path in product((-1, 1), repeat=n):
                        x, mass = start, Fraction(1)
                        survived = start > 0
                        for step in path:
                            mass *= p if step == -1 else 1 - p
                            if survived:
                                x += step
                                survived = x > 0
                        if survived:
                            exact += mass
                    self.assertEqual(q, exact)

    def test_polynomial_telescoping(self):
        product_ge = Fraction(1)
        for n, q in polynomial_tails(50):
            d = n + 1
            product_ge *= Fraction(d*d, (d+1)*(d+1))
            self.assertEqual(q, product_ge)
        self.assertEqual(dict(polynomial_tails(0))[0], Fraction(1, 4))

    def test_validation(self):
        with self.assertRaises(ValueError):
            list(coupon_tails(0, 10))
        with self.assertRaises(ValueError):
            list(walk_tails(1, Fraction(6, 5), 10))
        with self.assertRaises(TypeError):
            list(walk_tails(1, 0.6, 10))
        with self.assertRaises(ValueError):
            list(polynomial_tails(-1))


if __name__ == "__main__":
    unittest.main()
