#!/usr/bin/env python3
"""Exact rational verifier for three stochastic affine positive certificates.

Verifies complete polynomial identities, rational constants, and affine-box
invariant implications. This is a universal algebraic proof check, not sampling.
The source SHA binds these witnesses to their reviewed sequential .pp programs.
Only Python standard-library modules are required.
"""
import ast
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path

N = 3
IDENTITIES = 0
RANGES = 0

class Poly:
    def __init__(self, data=0):
        if isinstance(data, Poly): self.a = dict(data.a)
        elif isinstance(data, dict): self.a = {k: F(v) for k,v in data.items() if v}
        else: self.a = {} if not data else {(0,)*N: F(data)}
    def __add__(self, other):
        r = dict(self.a)
        for k,v in Poly(other).a.items(): r[k] = r.get(k,F(0)) + v
        return Poly(r)
    __radd__ = __add__
    def __neg__(self): return Poly({k: -v for k,v in self.a.items()})
    def __sub__(self, other): return self + -Poly(other)
    def __rsub__(self, other): return Poly(other) + -self
    def __mul__(self, other):
        r = {}
        for k,v in self.a.items():
            for j,w in Poly(other).a.items():
                t = tuple(a+b for a,b in zip(k,j))
                r[t] = r.get(t,F(0)) + v*w
        return Poly(r)
    __rmul__ = __mul__
    def __truediv__(self, other):
        other = Poly(other)
        assert set(other.a) == {(0,)*N}, 'Only division by nonzero constants'
        return self * (1/other.a[(0,)*N])
    def __pow__(self, n):
        assert isinstance(n,int) and n >= 0
        r = Poly(1)
        for _ in range(n): r = r*self
        return r
    def sub(self, xs):
        r = Poly()
        for k,v in self.a.items():
            t = Poly(v)
            for i,p in enumerate(k): t = t*Poly(xs[i])**p
            r = r+t
        return r
    def at(self, xs):
        r = F(0)
        for k,v in self.a.items():
            t = v
            for i,p in enumerate(k): t *= F(xs[i])**p
            r += t
        return r

x,y,z = [Poly({tuple(int(i==j) for i in range(N)): 1}) for j in range(N)]
VARS = {'x': x, 'y': y, 'z': z}

def parse(text):
    """Restricted exact arithmetic; no Python eval or binary floats."""
    def visit(n):
        if isinstance(n, ast.Constant):
            assert isinstance(n.value, int)
            return Poly(n.value)
        if isinstance(n, ast.Name): return VARS[n.id]
        if isinstance(n, ast.UnaryOp):
            if isinstance(n.op, ast.USub): return -visit(n.operand)
            if isinstance(n.op, ast.UAdd): return visit(n.operand)
        if isinstance(n, ast.BinOp):
            a = visit(n.left)
            if isinstance(n.op, ast.Pow):
                assert isinstance(n.right, ast.Constant) and isinstance(n.right.value,int)
                return a**n.right.value
            b = visit(n.right)
            if isinstance(n.op, ast.Add): return a+b
            if isinstance(n.op, ast.Sub): return a-b
            if isinstance(n.op, ast.Mult): return a*b
            if isinstance(n.op, ast.Div): return a/b
        raise ValueError(ast.dump(n))
    return visit(ast.parse(text, mode='eval').body)

def eq(a,b):
    global IDENTITIES
    r = Poly(a)-Poly(b)
    assert not r.a, r.a
    IDENTITIES += 1

def affine_range(p, bounds):
    """Exact range of an affine polynomial on a rectangular domain."""
    lo = hi = F(0)
    for exps,c in Poly(p).a.items():
        assert sum(exps) <= 1
        if sum(exps) == 0:
            lo += c; hi += c
        else:
            i = exps.index(1)
            a,b = (c*bounds[i][0],c*bounds[i][1])
            lo += min(a,b); hi += max(a,b)
    return lo,hi

def inside(p, bounds, low, high):
    global RANGES
    lo,hi = affine_range(p,bounds)
    assert F(low) <= lo <= hi <= F(high), (lo,hi,low,high)
    RANGES += 1

def witnesses(cid, eta, a):
    # Each first member is globally nonnegative; the second is a
    # positive constant times the nonnegative closed-guard polynomial eta-a.
    if cid == 'S1':
        coeffs = [F(5,16),F(19,320),F(1,25)]
        sos = F(5,16)*(x-F(3,5)*y)**2 + F(19,320)*y*y
    elif cid == 'S2':
        coeffs = [F(3,16),F(17,32)]
        sos = F(3,16)*y*y
    elif cid == 'S3':
        coeffs = [F(27,128),F(3,16)]
        sos = F(27,128)*(y*y+z*z)
    else: raise ValueError(cid)
    assert all(t > 0 for t in coeffs)
    return sos, sos+coeffs[-1]*(eta-a)

def invariant_check(cid, branches):
    cube = [(F(-2),F(2))]*3
    if cid == 'S1':
        for _,xs in branches:
            # x is assigned first and y second; each new coordinate is
            # bounded by two independently of the untouched old coordinate.
            inside(xs[0],cube,-2,2); inside(xs[1],cube,-2,2)
    elif cid == 'S2':
        chart = [x+4*y,y,z]  # here x=u, y=v
        bounds = [(F(-2),F(2)),(F(-1),F(1)),(F(0),F(0))]
        for sign,(_,xs) in zip([1,-1],branches):
            U = (xs[0]-4*xs[1]).sub(chart)
            V = xs[1].sub(chart)
            eq(U,x/2+F(sign,2)); eq(V,y/4+F(sign,8))
            inside(U,bounds,-2,2); inside(V,bounds,-1,1)
            # First assignment establishes its branch-specific middle box.
            middle = (xs[0]-y).sub(chart)
            eq(middle,x/2+sign)
            qlo,qhi = ((0,2) if sign==1 else (-2,0))
            inside(middle,bounds,qlo,qhi)
            # Second assignment implication holds on the ENTIRE stated
            # middle domain, not just the reachable subset.
            # Let q=already_updated_x-old_y, with q represented by x.
            middle_bounds = [(F(qlo),F(qhi)),(F(-1),F(1)),(F(0),F(0))]
            final_y = y/4+F(sign,8)
            final_u = (x+y)-4*final_y
            eq(final_u,x-F(sign,2))
            inside(final_u,middle_bounds,-2,2)
            inside(final_y,middle_bounds,-1,1)
    elif cid == 'S3':
        for _,xs in branches:
            # Source order y,z,x keeps old x until the last assignment.
            # Each intermediate state stays in the same rectangular cube.
            for coordinate in xs: inside(coordinate,cube,-2,2)
    else: raise ValueError(cid)

def first_n_below(prefactor,q,target):
    n=0; bound=prefactor
    while bound > target:
        n+=1; bound*=q
    return n

def main():
    root = Path(__file__).resolve().parent
    certs = json.loads((root/'certificates.json').read_text())
    assert [c['id'] for c in certs] == ['S1','S2','S3']
    for c in certs:
        source = (root/c['file']).read_bytes()
        assert hashlib.sha256(source).hexdigest() == c['source_sha256']
        assert c['mode']=='positive' and F(c['k'])==1
        eta = parse(c['eta_expression'])
        a,lam,nu,cc,q = map(F,[c['a_or_b'],c['lambda'],c['nu'],c['c'],c['q_certified']])
        assert a==F(c['a']) and a>0 and nu>0 and 0<lam<1
        assert cc==lam+nu/a and q==cc and 0<q<1
        if c['id']=='S2': eq(eta,(x-4*y)**2+y*y)
        elif c['id']=='S1': eq(eta,x*x+y*y)
        else: eq(eta,x*x+y*y+z*z)
        init = [F(c['initial'].get(v,'0')) for v in ['x','y','z']]
        assert eta.at(init)==F(c['eta0'])>a
        prefactor=F(c['prefactor'])
        assert prefactor==F(c['eta0'])/a
        bs=[]
        for b in c['branch_support']:
            p=F(b['probability']); assert p>0
            xs=[parse(b['updates'].get(v,v)) for v in ['x','y','z']]
            assert all(sum(e)<=1 for t in xs for e in t.a)
            # At least one nonzero constant: every program has genuinely
            # additive noise (S1's zero-shock branch is deliberately allowed).
            bs.append((p,xs))
        assert sum(p for p,_ in bs)==1
        assert any(any((0,0,0) in t.a for t in xs) for _,xs in bs)
        E=sum((p*eta.sub(xs) for p,xs in bs),Poly())
        eq(E,parse(c['first_moment_expression']))
        sos,guarded=witnesses(c['id'],eta,a)
        eq(lam*eta+nu-E,sos)
        eq(sos,parse(c['global_drift_residual_expression']))
        eq(cc*eta-E,guarded)
        eq(guarded,parse(c['first_moment_residual_expression']))
        invariant_check(c['id'],bs)
        print(c['id']+': PASS; c='+str(q)+'; prefactor='+str(prefactor)
              +'; certified Pr(T>n)<=0.01 for n>='+str(first_n_below(prefactor,q,F(1,100))))
    # Structural facts used in the discussion.
    assert F(1,1)*F(17,1)-F(-4,1)**2==1  # SPD determinant of S2's P.
    assert F(1)+F(1,16)>1                # S2 Euclidean noiseless expansion.
    assert 3*F(3,4)**2==F(27,16)>1       # S3 rare-mode energy expansion.
    print('Verified '+str(IDENTITIES)+' exact polynomial identities and '
          +str(RANGES)+' full-domain affine interval implications; no sampling or optimizer.')

if __name__=='__main__':
    main()
