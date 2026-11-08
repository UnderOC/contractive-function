"""Small exact multivariate polynomial algebra for source-level certificate checks."""
from fractions import Fraction as F


class Poly:
    def __init__(self, value=0, nvars=2):
        if isinstance(value, Poly):
            self.n = value.n
            self.terms = dict(value.terms)
        else:
            self.n = nvars
            if isinstance(value, dict):
                assert all(len(m) == self.n for m in value)
                self.terms = {tuple(m): F(c) for m, c in value.items() if c}
            else:
                self.terms = {} if not value else {(0,) * self.n: F(value)}

    def coerce(self, value):
        if isinstance(value, Poly):
            assert value.n == self.n
            return value
        return Poly(value, self.n)

    def __add__(self, other):
        other = self.coerce(other)
        terms = dict(self.terms)
        for m, c in other.terms.items():
            terms[m] = terms.get(m, F(0)) + c
        return Poly(terms, self.n)

    __radd__ = __add__

    def __neg__(self):
        return Poly({m: -c for m, c in self.terms.items()}, self.n)

    def __sub__(self, other):
        return self + (-self.coerce(other))

    def __rsub__(self, other):
        return self.coerce(other) + (-self)

    def __mul__(self, other):
        other = self.coerce(other)
        terms = {}
        for a, x in self.terms.items():
            for b, y in other.terms.items():
                m = tuple(i+j for i, j in zip(a, b))
                terms[m] = terms.get(m, F(0)) + x*y
        return Poly(terms, self.n)

    __rmul__ = __mul__

    def __truediv__(self, value):
        return self * (1/F(value))

    def __pow__(self, exponent):
        assert isinstance(exponent, int) and exponent >= 0
        result = Poly(1, self.n)
        for _ in range(exponent):
            result *= self
        return result

    def __eq__(self, other):
        return not (self-self.coerce(other)).terms

    def __bool__(self):
        raise TypeError("A symbolic polynomial cannot be used as a Boolean")

    def __repr__(self):
        return f"Poly({self.terms!r}, nvars={self.n})"

    def degree(self):
        return max((sum(m) for m in self.terms), default=0)

    def as_records(self, names):
        assert len(names) == self.n
        return [{"coefficient": str(c), "powers": {name: p for name, p in zip(names, monomial) if p}}
                for monomial, c in sorted(self.terms.items())]


def variables(names):
    n = len(names)
    return {name: Poly({tuple(int(i == j) for i in range(n)): 1}, n)
            for j, name in enumerate(names)}


def equal(lhs, rhs, label):
    if lhs != rhs:
        raise AssertionError(f"{label}: nonzero polynomial residual {lhs-rhs!r}")

