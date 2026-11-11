#!/usr/bin/env python3
"""Exact universal polynomial witnesses for S4 and S5 (stdlib only).

Checks identities, nonnegative-factor premises, all rational moment parameters,
metadata expressions and source digests. Does not call an external synthesizer.
The package-level source checker independently checks the actual .pp semantics.
"""
from fractions import Fraction as F
from pathlib import Path
import ast
import hashlib
import json

COUNT = 0

class Poly:
    def __init__(self, terms=0):
        if isinstance(terms, Poly):
            self.t = dict(terms.t)
        elif isinstance(terms, dict):
            self.t = {m: F(c) for m, c in terms.items() if c}
        else:
            self.t = {} if not terms else {(0, 0, 0): F(terms)}
    def __add__(self, other):
        other = Poly(other)
        terms = dict(self.t)
        for m, c in other.t.items():
            terms[m] = terms.get(m, F(0)) + c
        return Poly(terms)
    __radd__ = __add__
    def __neg__(self):
        return Poly({m: -c for m, c in self.t.items()})
    def __sub__(self, other):
        return self + -Poly(other)
    def __rsub__(self, other):
        return Poly(other) + -self
    def __mul__(self, other):
        other = Poly(other)
        terms = {}
        for a, x in self.t.items():
            for b, y in other.t.items():
                m = tuple(i + j for i, j in zip(a, b))
                terms[m] = terms.get(m, F(0)) + x*y
        return Poly(terms)
    __rmul__ = __mul__
    def __truediv__(self, other):
        return self * (1 / F(other))
    def __pow__(self, n):
        assert isinstance(n, int) and n >= 0
        result = Poly(1)
        for _ in range(n):
            result = result * self
        return result
    def __eq__(self, other):
        return not (self - Poly(other)).t
    def evaluate(self, values):
        return sum((c * values[0]**m[0] * values[1]**m[1] * values[2]**m[2]
                    for m, c in self.t.items()), F(0))

x, y, noise = [Poly({tuple(int(i == j) for i in range(3)): 1}) for j in range(3)]


def equal(lhs, rhs, label):
    global COUNT
    assert lhs == rhs, (label, (Poly(lhs)-Poly(rhs)).t)
    COUNT += 1


def expression(text, env):
    """Parse metadata without floating-point arithmetic or unrestricted eval."""
    tree = ast.parse(text, mode='eval')
    def ev(node):
        if isinstance(node, ast.Constant):
            return F(ast.get_source_segment(text, node))
        if isinstance(node, ast.Name):
            return env[node.id]
        if isinstance(node, ast.UnaryOp):
            value = ev(node.operand)
            return -value if isinstance(node.op, ast.USub) else value
        if isinstance(node, ast.BinOp):
            lhs, rhs = ev(node.left), ev(node.right)
            if isinstance(node.op, ast.Add): return lhs+rhs
            if isinstance(node.op, ast.Sub): return lhs-rhs
            if isinstance(node.op, ast.Mult): return lhs*rhs
            if isinstance(node.op, ast.Div): return lhs/rhs
            if isinstance(node.op, ast.Pow):
                assert rhs.denominator == 1 and rhs >= 0
                return lhs**int(rhs)
        raise ValueError(ast.dump(node))
    return ev(tree.body)


def check_s4(item):
    f = x*x+y*y
    eta = 2-f
    B = 2-f/4
    c, D, r = (F(item[name]) for name in ('c', 'D', 'r0'))
    assert (c, D, r) == (F(247, 224), F(49, 16), F(1))
    general = (x/2+noise/4)**2 + (y/2)**2
    equal(1-general, F(3, 8)+(1-f)/2+(1-noise**2)/8
          + ((x-noise/2)**2+y*y)/4, 'S4: all intermediate annotations')
    first, second = Poly(0), Poly(0)
    for probability, z in [(F(7, 8), 0), (F(1, 16), 1), (F(1, 16), -1)]:
        fp = (x/2+F(z, 4))**2+(y/2)**2
        etap = 2-fp
        first += probability*etap
        second += probability*etap**2
        if z:
            equal(etap-r*eta, (f-F(1, 4))/2+((x-F(z, 2))**2+y*y)/4,
                  f'S4: support {z}')
        else:
            equal(etap-r*eta, 3*f/4, 'S4: zero-noise support')
    equal(first, F(255, 128)-f/4, 'S4: first moment')
    equal(first-c*eta, F(191, 224)*(f-F(1, 4)), 'S4: mean residual')
    equal(second, B**2-B/64+F(1, 2048)+x*x/128, 'S4: second moment')
    equal(B**2-second, F(39, 2048)+F(3, 256)*(1-f)+y*y/128,
          'S4: baseline moment domination')
    equal(F(7, 4)*eta-B, F(3, 2)*(1-f), 'S4: moment upper factor')
    equal(D*eta**2-second,
          (F(7, 4)*eta-B)*(F(7, 4)*eta+B)
          +F(39, 2048)+F(3, 256)*(1-f)+y*y/128,
          'S4: nonnegative second moment residual')
    # On f<=1: eta>=1, B>=7/4. On the guard: f-1/4>0.
    assert 2-1 > 0 and 2-F(1, 4) > 1
    assert F(191, 224)>0 and F(39, 2048)>0 and F(3, 256)>0
    return first, second


def check_s5(item):
    f = x*x+y*y
    u, v = 3*x/5+4*y/5, -4*x/5+3*y/5
    eta = 2-f
    beta = F(3, 8)
    g = u*u/4+F(9, 64)*v*v
    B0, B = 2-g, 2-F(9, 64)*f
    c, D, r = (F(item[name]) for name in ('c', 'D', 'r0'))
    assert (c, D, r) == (F(3997, 3200), F(14161, 4096), F(39, 40))
    equal(u*u+v*v, f, 'S5: orthogonal coordinate change')
    xp = F(21, 50)*x+F(3, 50)*y+F(9, 40)*noise
    yp = F(3, 50)*x+F(91, 200)*y+F(3, 10)*noise
    equal(3*xp/5+4*yp/5, u/2+beta*noise, 'S5: simultaneous u update')
    equal(-4*xp/5+3*yp/5, 3*v/8, 'S5: simultaneous v update')
    general = xp*xp+yp*yp
    equal(1-general, F(7, 32)+(1-f)/2+F(9, 32)*(1-noise**2)
          +(u/2-beta*noise)**2+F(23, 64)*v*v,
          'S5: all intermediate annotations')
    assert 0<F(3, 8)<=F(1, 2)<1  # exact eigenvalues: stable deterministic map
    first, second = Poly(0), Poly(0)
    for probability, z in [(F(99, 100), 0), (F(1, 200), 1), (F(1, 200), -1)]:
        fp = (u/2+beta*z)**2+F(9, 64)*v*v
        etap = 2-fp
        first += probability*etap
        second += probability*etap**2
        if z:
            equal(etap-r*eta, F(19, 40)*(f-F(1, 2))
                  +((u-F(3*z, 4))**2+v*v)/4+F(7, 64)*v*v+F(1, 160),
                  f'S5: support {z}')
        else:
            equal(etap-r*eta, eta/40+3*u*u/4+F(55, 64)*v*v,
                  'S5: zero-noise support')
    equal(first, 2-g-F(9, 6400), 'S5: first moment')
    equal(first-c*eta, F(3197, 3200)*(f-F(1, 2))+F(7, 64)*v*v,
          'S5: mean residual')
    equal(second, B0**2+F(9, 6400)*(-2*B0+F(9, 64)+u*u), 'S5: second moment')
    equal(B0**2-second, F(9, 6400)*(F(5, 2)-F(9, 64)
          +F(3, 2)*(1-f)+F(39, 32)*v*v), 'S5: baseline moment domination')
    equal(B-B0, F(7, 64)*u*u, 'S5: anisotropic baseline bound')
    equal(F(119, 64)*eta-B, F(55, 32)*(1-f), 'S5: moment upper factor')
    equal(D*eta**2-second,
          (F(119, 64)*eta-B)*(F(119, 64)*eta+B)
          +(B-B0)*(B+B0)+F(9, 6400)*(F(5, 2)-F(9, 64)
          +F(3, 2)*(1-f)+F(39, 32)*v*v), 'S5: nonnegative second moment residual')
    # On f<=1: eta>=1, B>=119/64, B0>=7/4. On the guard: f-1/2>0.
    assert F(5, 2)-F(9, 64)>0 and F(119, 64)>0 and F(7, 4)>0
    assert all(t>0 for t in [F(3197, 3200),F(19,40),F(7,64),F(1,160)])
    # A real reachable energy increase: three consecutive + shocks from the given start.
    u0, v0 = F(7,10), F(1,2)
    energies = [u0*u0+v0*v0]
    for _ in range(3):
        u0, v0 = u0/2+beta, 3*v0/8
        energies.append(u0*u0+v0*v0)
    assert all(F(1,2)<s<=1 for s in energies)
    assert energies[3]>energies[2]
    print('S5 reachable energies:', ', '.join(map(str,energies)))
    return first, second


def check_metadata(item, first, second):
    env={'x':x,'y':y}
    for key, text in item['definitions'].items():
        env[key]=expression(text,env)
    eta=expression(item['eta_expression'],env)
    c,D,r0,k=(F(item[k]) for k in ['c','D','r0','k'])
    equal(expression(item['first_moment_expression'],env),first, item['id']+' metadata mean')
    equal(expression(item['second_moment_expression'],env),second,item['id']+' metadata second moment')
    equal(expression(item['first_moment_residual_expression'],env),first-c*eta,item['id']+' metadata mean residual')
    equal(expression(item['second_moment_residual_expression'],env),D*eta**2-second,item['id']+' metadata moment residual')
    assert k==1 and 0<r0<c and c>1 and D>=c*c
    p=(D-c*c)/(D-2*r0*c+r0*r0)
    z=(D-r0*c)/(c-r0)
    q=p/r0+(1-p)/z
    assert 0<=p<1 and z>=c>r0
    assert p==F(item['p_star']) and z==F(item['z_star'])
    assert q==F(item['q_certified'])==F(item['q_mom']) and 0<q<1
    initial={k:F(v) for k,v in item['initial'].items()}
    f0=initial['x']**2+initial['y']**2
    epsilon=F(item['epsilon'])
    assert epsilon<f0<=1 and F(item['C'])==2 and F(item['M'])==1
    eta0=2-f0
    b=2-epsilon
    assert b>1 and eta0==F(item['eta0'])
    assert b==F(item['b'])==F(item['a_or_b'])
    assert b/eta0==F(item['prefactor'])==F(item['initial_factor'])
    expected_first,expected_second=Poly(0),Poly(0)
    for branch in item['branch_support']:
        probability=F(branch['probability'])
        updates={k:expression(v,{'x':x,'y':y}) for k,v in branch['updates'].items()}
        ep=2-updates['x']**2-updates['y']**2
        expected_first+=probability*ep
        expected_second+=probability*ep**2
    equal(expected_first,first,item['id']+' branch metadata mean')
    equal(expected_second,second,item['id']+' branch metadata second moment')


def main():
    directory=Path(__file__).resolve().parent
    items=json.loads((directory/'certificates.json').read_text())
    assert [item['id'] for item in items]==['S4','S5']
    for item,check in zip(items,[check_s4,check_s5]):
        assert hashlib.sha256((directory/item['file']).read_bytes()).hexdigest()==item['source_sha256']
        first,second=check(item)
        check_metadata(item,first,second)
        print(f"{item['id']}: exact certificate PASS; q={item['q_certified']}")
    print(f'{COUNT} universal polynomial identities checked; all exact parameter checks PASS.')
    print('This is verification of explicit witnesses, not a run of an external SOS synthesizer.')

if __name__=='__main__':
    main()
