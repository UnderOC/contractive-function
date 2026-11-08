#!/usr/bin/env python3
"""Exact rational algebra checks for the Q-learning certificate witnesses.

Only Python's standard library is required. This checks polynomial identities
used in README.md, exact Bellman fixed points and endpoint/range premises,
then recomputes all advertised constants. It does not run the user's synthesizer.
"""
from fractions import Fraction as F
from pathlib import Path
import json

COUNT=0
class Poly:
    def __init__(self, terms=0):
        if isinstance(terms, Poly): self.t=dict(terms.t)
        elif isinstance(terms, dict):self.t={m:F(c) for m,c in terms.items() if c}
        else:self.t={} if not terms else {(0,0,0):F(terms)}
    def __add__(self,other):
        other=Poly(other);t=dict(self.t)
        for m,c in other.t.items():t[m]=t.get(m,F(0))+c
        return Poly(t)
    __radd__=__add__
    def __neg__(self):return Poly({m:-c for m,c in self.t.items()})
    def __sub__(self,other):return self+-Poly(other)
    def __rsub__(self,other):return Poly(other)+-self
    def __mul__(self,other):
        other=Poly(other);t={}
        for a,x in self.t.items():
            for b,y in other.t.items():
                m=tuple(i+j for i,j in zip(a,b));t[m]=t.get(m,F(0))+x*y
        return Poly(t)
    __rmul__=__mul__
    def __truediv__(self,c):return self* (1/F(c))
    def __pow__(self,n):
        assert isinstance(n,int) and n>=0
        result=Poly(1)
        for _ in range(n):result=result*self
        return result
    def __eq__(self,other):return not (self-Poly(other)).t

X=[Poly({tuple(int(i==j) for i in range(3)):1}) for j in range(3)]
def eq(lhs,rhs):
    global COUNT
    assert lhs==rhs, (Poly(lhs)-Poly(rhs)).t
    COUNT+=1

def box_invariance(alpha,gamma,rewards,M):
    assert 0<alpha<=1 and 0<=gamma<1 and M>=0
    for rs in rewards:
        for r in rs: assert r>=0 and r+gamma*M<=M

def bellman(qstar,rewards,gamma):
    for q,rs in zip(qstar,rewards):assert q==sum(rs,F(0))/len(rs)+gamma*max(qstar)


def positive_q1():
    e1,e2=X[:2];e=[e1,e2]
    weights=[F(1),F(3)];p=[F(3,4),F(1,4)]
    eta=e1**2+3*e2**2;N=e1**2+e2**2
    alpha=gamma=F(1,2);sigma2=F(1,64)
    rewards=[[F(3,8),F(5,8)],[F(1,8),F(3,8)]]
    bellman([F(1),F(3,4)],rewards,gamma)
    box_invariance(alpha,gamma,rewards,F(5,4))
    for j,delta in enumerate([e1,e2-F(1,4)]):
        E=eta
        for i in range(2):
            u=(1-alpha)*e[i]+alpha*gamma*delta
            E+=p[i]*weights[i]*(u**2-e[i]**2+alpha**2*sigma2)
        # U = N-delta^2; branch j=1 has q2-q1=e2-e1-1/4>=0.
        U=e2**2 if j==0 else (e1+F(1,4))**2+F(1,2)*(e2-e1-F(1,4))
        eq(N-delta**2,U)
        S=e1**2/F(8)+F(3,16)*U+F(3,16)*sum((v-delta/2)**2 for v in e)
        eq(F(15,16)*eta+F(3,512)-E,S)
        eq(F(123,128)*eta-E,S+F(3,128)*(eta-F(1,4)))
    assert F(7,4)/F(1,4)==7


def positive_q2():
    e1,e2=X[:2];eta=e1**2+e2**2
    E=((e1/2+e2/4)**2+e2**2+e1**2+(e2/2+e1/4)**2)/2
    eq(F(25,32)*eta-E,(e1-e2)**2/F(8))
    assert F(1)==F(3,4)+F(1,2)*F(1,2)
    assert F(1,2)==F(1,2)*F(1)
    box_invariance(F(1,2),F(1,2),[[F(3,4)],[F(0)]],F(3,2))
    assert F(2)/F(1,64)==128


def positive_q3():
    e=X;N=sum(v**2 for v in e);eta=e[0]**2+2*e[1]**2+2*e[2]**2
    weights=[F(1),F(2),F(2)];p=[F(1,2),F(1,4),F(1,4)]
    alpha=F(1,2);gamma=F(1,4);qstar=[F(1),F(3,4),F(1,2)]
    rewards=[[F(3,4)],[F(1,2)],[F(1,4)]]
    bellman(qstar,rewards,gamma);box_invariance(alpha,gamma,rewards,F(1))
    for j in range(3):
        d=qstar[0]-qstar[j];delta=e[j]-d;E=eta
        for i in range(3):E+=p[i]*weights[i]*(((1-alpha)*e[i]+alpha*gamma*delta)**2-e[i]**2)
        if j==0:U=e[1]**2+e[2]**2
        else:
            # qj>=q1 implies e_j-e_1-d>=0.
            U=(e[0]+d)**2+sum(e[i]**2 for i in range(3) if i not in [0,j])+2*d*(e[j]-e[0]-d)
        eq(N-delta**2,U)
        S=F(13,128)*e[0]**2+F(3,64)*U+F(1,8)*sum((v-delta/4)**2 for v in e)
        eq(F(115,128)*eta-E,S)
    assert F(13,8)/F(1,64)==104


def reciprocal(item):
    q1,q2=X[:2];s=q1+q2;eta=1+s
    ident=item['id'];c=F(item['c']);D=F(item['D']);U=F(item['r_upper'])
    if ident=='Q4':
        rewards=[[F(1,2)],[F(1,2)]];M=F(1);h=F(3,2);star=[F(1),F(1)]
    else:
        rewards=[[F(1,2),F(3,4)],[F(1,4),F(1,2)]];M=F(3,2);h=F(5,8);star=[F(5,4),F(1)]
    box_invariance(F(1,2),F(1,2),rewards,M);bellman(star,rewards,F(1,2))
    for maxj,m in enumerate([q1,q2]):
        E=Poly(0);E2=Poly(0);factor=Poly(0)
        for qi,rs in zip([q1,q2],rewards):
            for r in rs:
                p=F(1,2*len(rs));delta=r/2+m/4-qi/2;etap=eta+delta
                E+=p*etap;E2+=p*etap**2
                if ident=='Q4':
                    # Both terms >=0: m<=1 and qi<=m.
                    eq(delta,(1-m)/4+(m-qi)/2)
                    # s-m>=0, qi>=0.
                    eq((U-1)*eta-delta,(s-m+2*qi)/4)
                else:
                    # m<=s<5/8, qi<=m, r>=1/4: allow small negative increments.
                    eq(delta+eta/52,F(3,13)*(h-s)+(s-m)/4+(m-qi)/2+(r-F(1,4))/2)
                    # m>=0,s-m>=0,qi>=0,r<=3/4.
                    eq((U-1)*eta-delta,m/8+F(3,8)*(s-m)+qi/2+(F(3,4)-r)/2)
                # eta'>0 and R<=U, giving an exact nonnegative product for Q4.
                factor+=p*(U*eta-etap)*(U*eta+etap)
        if ident=='Q4':eq(D*eta**2-E2,factor)
        else:
            lo=s-m;gap=2*m-s
            H=F(103,32)*lo**2+F(89,32)*lo*gap+F(61,32)*lo+F(65,128)*gap**2+F(43 if maxj==0 else 39,64)*gap
            eq(D*eta**2-E2,H)
        if ident=='Q4':witness=F(3,20)*(h-s)+(2*m-s)/8
        else:witness=F(3,13)*(h-s)+(2*m-s)/8
        eq(E-c*eta,witness)
    r0=F(item['r0']);assert 0<r0<c and D>=c*c and D<=U*U
    p=(D-c*c)/(D-2*r0*c+r0*r0);z=(D-r0*c)/(c-r0)
    q=p/r0+(1-p)/z
    assert p==F(item['p_star']) and z==F(item['z_star'])
    assert q==F(item['q_mom'])==F(item['q_certified']) and 0<q<1
    assert (r0+U-c)/(r0*U)==F(item['q_direct'])
    assert F(item['b'])==1+h and F(item['eta0'])==1
    assert F(item['initial_factor'])==F(item['b'])/F(item['eta0'])


def main():
    items=json.loads((Path(__file__).with_name('certificates.json')).read_text())
    assert [v['id'] for v in items]==['Q1','Q2','Q3','Q4','Q5']
    positive_q1();positive_q2();positive_q3()
    for item in items[3:]:reciprocal(item)
    assert [F(v['q_certified']) for v in items[:3]]==[F(123,128),F(25,32),F(115,128)]
    for item in items:
        assert 0<F(item['q_certified'])<1
        print(f"{item['id']}: exact certificate PASS; q={item['q_certified']}")
    print(f'{COUNT} exact polynomial identities checked; all rational parameter and range checks PASS.')
if __name__=='__main__':main()
