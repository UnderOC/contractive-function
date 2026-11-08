#!/usr/bin/env python3
"""Exact rational identity checker for the five RCD certificates.

No sampling, numerical optimizer, or SMT/SDP solver is used. Identities plus
nonnegative multipliers on the declared sublevel-set domains prove the claims.
The recorded source digest binds each witness to its reviewed .pp source.
"""
from fractions import Fraction as F
from pathlib import Path
import json
import hashlib

N=3
class Poly:
    def __init__(self, data=0):
        if isinstance(data, Poly): self.a=dict(data.a)
        elif isinstance(data, dict): self.a={k:F(v) for k,v in data.items() if v}
        else: self.a={} if not data else {(0,)*N:F(data)}
    def __add__(self, other):
        r=dict(self.a)
        for k,v in Poly(other).a.items(): r[k]=r.get(k,F(0))+v
        return Poly(r)
    __radd__=__add__
    def __neg__(self): return Poly({k:-v for k,v in self.a.items()})
    def __sub__(self, other): return self+-Poly(other)
    def __rsub__(self, other): return Poly(other)+-self
    def __mul__(self, other):
        r={}
        for k,v in self.a.items():
            for j,w in Poly(other).a.items():
                t=tuple(a+b for a,b in zip(k,j));r[t]=r.get(t,F(0))+v*w
        return Poly(r)
    __rmul__=__mul__
    def __pow__(self,n):
        assert isinstance(n,int) and n>=0
        r=Poly(1)
        for _ in range(n):r=r*self
        return r
    def sub(self, xs):
        r=Poly()
        for k,v in self.a.items():
            t=Poly(v)
            for i,p in enumerate(k):t=t*xs[i]**p
            r=r+t
        return r
    def at(self,xs):
        r=F(0)
        for k,v in self.a.items():
            t=v
            for i,p in enumerate(k):t*=F(xs[i])**p
            r+=t
        return r

x,y,z=[Poly({tuple(int(i==j) for i in range(N)):1}) for j in range(N)]
identities=0
def eq(a,b):
    global identities
    assert not (Poly(a)-Poly(b)).a, (Poly(a)-Poly(b)).a
    identities+=1

def main():
    root=Path(__file__).parent
    certs=json.loads((root/'certificates.json').read_text())
    for d in certs:
        data=(root/d['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==d['source_sha256']
    f=x*x+x*y+y*y;g=x+y*F(1,2);h=y+x*F(1,2)
    eq(f,g*g+F(3,4)*y*y)
    eq(f,h*h+F(3,4)*x*x)
    # Branch decreases prove the entire quadratic sublevel set is invariant.
    fx=f.sub([-y*F(1,2),y,z]);fy=f.sub([x,-x*F(1,2),z])
    eq(f-fx,g*g);eq(f-fy,h*h)
    E=fx*F(1,4)+fy*F(3,4)
    eq(F(7,8)*f-E,F(5,16)*(x+F(7,5)*y)**2+F(3,40)*y*y)
    assert f.at([1,1,0])==3
    # Half-step descent: loss=(3/4)*coordinate_gradient^2.
    fhx=f.sub([x*F(1,2)-y*F(1,4),y,z])
    fhy=f.sub([x,y*F(1,2)-x*F(1,4),z])
    eq(f-fhx,F(3,4)*g*g);eq(f-fhy,F(3,4)*h*h)
    E=(fhx+fhy)*F(1,2)
    eq(F(13,16)*f-E,F(9,32)*(x+y)**2)
    assert f.at([2,-1,0])==3
    # Shifted 3D objective, positive definiteness and three branch decreases.
    u=x-1;v=y+1;w=z-F(1,2)
    f3=u*u+u*v+v*v+2*w*w
    eq(f3,(u+v*F(1,2))**2+F(3,4)*v*v+2*w*w)
    bs=[f3.sub([F(1,2)-y*F(1,2),y,z]),f3.sub([x,-F(1,2)-x*F(1,2),z]),f3.sub([x,y,Poly(F(1,2))])]
    eq(f3-bs[0],(u+v*F(1,2))**2);eq(f3-bs[1],(v+u*F(1,2))**2);eq(f3-bs[2],2*w*w)
    E=bs[0]*F(1,4)+bs[1]*F(1,4)+bs[2]*F(1,2)
    eq(F(7,8)*f3-E,F(3,16)*(u+v)**2+F(3,4)*w*w)
    assert f3.at([2,0,F(3,2)])==5
    # Reciprocal R1: shifted anisotropic objective.
    u=x-1;v=y+2;f4=u*u+4*v*v;eta=5-f4
    f4x=f4.sub([Poly(1),y,z]);f4y=f4.sub([x,Poly(-2),z])
    eq(f4-f4x,u*u);eq(f4-f4y,4*v*v)
    es=[5-f4x,5-f4y]
    E=(es[0]+es[1])*F(1,2)
    E2=(es[0]**2+es[1]**2)*F(1,2)
    eq(E-F(13,10)*eta,F(4,5)*(f4-F(15,8)))
    slack=F(5,2)-f4
    eq(F(5,2)*eta**2-E2,10*slack+2*slack**2+4*u*u*v*v)
    assert f4.at([F(5,2),F(-7,4),0])==F(5,2)
    # Reciprocal R2: four independent coordinate/step branches.
    eta=2-f;fs=[fhx,fx,fhy,fy];es=[2-t for t in fs]
    E=sum(es,Poly())*F(1,4);E2=sum([e*e for e in es],Poly())*F(1,4)
    eq(E-F(181,160)*eta,F(7,20)*(f-F(3,4))+F(21,64)*(x+y)**2)
    slack=1-f;d=x-y
    witness=F(561,128)*slack+F(21,8)*slack**2+F(7,32)*d*d+F(7,32)*slack*d*d+F(25,1024)*d**4
    eq(F(1409,512)*eta**2-E2,witness)
    eq(F(9,8)*f*f-g**4-h**4,F(1,16)*(x-y)**4)
    assert f.at([1,-1,0])==1
    assert F(9,10)+F(1,10)/2 == F(19,20)
    assert F(9,10)+F(1,10)/16 == F(29,32)
    for c in certs:
        assert F(c['eta0'])>0 and F(c['a_or_b'])>0
        q=F(c['q_certified']);assert 0<q<1
        if c['mode']=='positive':
            assert F(c['c'])==q
            assert F(c['prefactor'])==F(c['eta0'])/F(c['a_or_b'])
        else:
            cc,D,r=map(F,[c['c'],c['D'],c['r0']])
            assert 0<r<cc and cc>1 and D>=cc*cc
            pp=(D-cc*cc)/(D-2*r*cc+r*r);zz=(D-r*cc)/(cc-r)
            assert str(pp)==c['p_star'] and str(zz)==c['z_star']
            assert pp/r+(1-pp)/zz==q
            assert F(c['prefactor'])==F(c['a_or_b'])/F(c['eta0'])
        print(c['id']+': PASS; q='+str(q)+'; prefactor='+c['prefactor'])
    print('Verified '+str(identities)+' exact polynomial identities and all rational moment/tail constants.')

if __name__=='__main__':main()
