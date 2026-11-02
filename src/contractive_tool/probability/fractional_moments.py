"""Finite joint laws and rational witnesses for positive rational powers.

No floating point computation is trusted by the checker. Correlated coordinates
are represented by joint atoms, not multiplied marginal moments.
"""
from dataclasses import dataclass
from fractions import Fraction

import sympy as sp

from contractive_tool.errors import AnalysisError


def rational(value):
    if isinstance(value, str):
        try:
            fraction = Fraction(value)
            return sp.Rational(fraction.numerator, fraction.denominator)
        except (ValueError, ZeroDivisionError) as error:
            raise AnalysisError(f'Expected a rational number, got {value!r}') from error
    value = sp.sympify(value)
    if value.is_Rational is not True:
        raise AnalysisError(f'Expected an exact rational number, got {value}')
    return value


@dataclass(frozen=True)
class FiniteLaw:
    symbols: tuple
    atoms: tuple  # ((coordinate values), probability)

    def validate(self):
        if len(set(self.symbols)) != len(self.symbols):
            raise AnalysisError('Duplicate random coordinates')
        if not all(isinstance(s, sp.Symbol) for s in self.symbols):
            raise AnalysisError('Random coordinates must be symbols')
        if not self.atoms:
            raise AnalysisError('Empty finite law')
        total = sp.Integer(0)
        for values, probability in self.atoms:
            if len(values) != len(self.symbols):
                raise AnalysisError('Joint atom dimension mismatch')
            for value in values:
                rational(value)
            probability = rational(probability)
            if probability < 0:
                raise AnalysisError('Negative atom probability')
            total += probability
        if total != 1:
            raise AnalysisError('Joint probabilities must sum exactly to one')
        return self

    def norm_atoms(self, basis):
        self.validate()
        squared_norm = sum((sp.sympify(b)**2 for b in basis), sp.Integer(0))
        if squared_norm.free_symbols - set(self.symbols):
            raise AnalysisError('Random basis depends on state or unknown symbols')
        result = []
        for values, probability in self.atoms:
            if probability == 0:
                continue
            h = rational(squared_norm.subs(dict(zip(self.symbols, values)), simultaneous=True))
            if h < 0:
                raise AnalysisError('Negative squared norm')
            result.append((h, rational(probability)))
        return tuple(result)

    def to_data(self):
        return {'symbols': list(map(str, self.symbols)),
                'atoms': [{'values': list(map(str, values)), 'probability': str(p)}
                          for values, p in self.atoms]}


def power_enclosure(base, exponent, digits=12):
    """Exact enclosing decimal rationals; integer root arithmetic only."""
    base, exponent = rational(base), rational(exponent)
    if base < 0 or exponent <= 0:
        raise AnalysisError('Power bounds require base >= 0 and exponent > 0')
    if type(digits) is not int or not 1 <= digits <= 50:
        raise AnalysisError('Power precision must be in [1,50]')
    p, q = int(exponent.p), int(exponent.q)
    if max(p, q) > 4096:
        raise AnalysisError('Rational exponent exceeds arithmetic budget')
    value = base**p
    scale = 10**digits
    scaled = int(value.p) * scale**q // int(value.q)
    root, _ = sp.integer_nthroot(scaled, q)
    lower = sp.Rational(root, scale)
    upper = lower if lower**q == value else sp.Rational(root+1, scale)
    return {'base': str(base), 'exponent': str(exponent),
            'lower': str(lower), 'upper': str(upper)}


def verify_power(witness):
    try:
        base, exponent, lower, upper = (rational(witness[k]) for k in
                                        ('base', 'exponent', 'lower', 'upper'))
        return bool(base >= 0 and exponent > 0 and 0 <= lower <= upper
                    and lower**exponent.q <= base**exponent.p <= upper**exponent.q)
    except (KeyError, ValueError, TypeError, AnalysisError):
        return False


def certify_moment(norm_atoms, k, digits=12):
    k = rational(k)
    if k <= 0:
        raise AnalysisError('Exponent must be positive')
    rows, total = [], sp.Integer(0)
    for h, probability in norm_atoms:
        probability = rational(probability)
        if probability < 0:
            raise AnalysisError('Negative atom probability')
        witness = power_enclosure(h, k/2, digits)
        total += probability * sp.Rational(witness['upper'])
        rows.append({'probability': str(probability), 'power': witness})
    if sum((sp.Rational(r['probability']) for r in rows), sp.Integer(0)) != 1:
        raise AnalysisError('Moment probabilities must sum to one')
    return {'k': str(k), 'upper': str(total), 'atoms': rows}


def verify_moment(certificate, norm_atoms):
    try:
        k = rational(certificate['k'])
        rows = certificate['atoms']
        if len(rows) != len(norm_atoms) or k <= 0:
            return False
        total = sp.Integer(0)
        for row, (h, probability) in zip(rows, norm_atoms):
            w = row['power']
            if (rational(row['probability']) != probability or rational(w['base']) != h
                    or rational(w['exponent']) != k/2 or not verify_power(w)):
                return False
            total += probability*rational(w['upper'])
        return bool(sum(p for _, p in norm_atoms) == 1 and
                    total == rational(certificate['upper']))
    except (KeyError, ValueError, TypeError, AnalysisError):
        return False
