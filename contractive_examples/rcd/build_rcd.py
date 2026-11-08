from pathlib import Path
import json
import hashlib
from fractions import Fraction as F
P=Path(__file__).parent
f2='x*x + x*y + y*y'
f3='(x-1)*(x-1) + (x-1)*(y+1) + (y+1)*(y+1) + 2*(z-0.5)*(z-0.5)'
f4='(x-1)*(x-1) + 4*(y+2)*(y+2)'

def ann(f,M):return '{0 <= ('+f+') and ('+f+') <= '+M+'}'
def b(i,f,M):return '  '*i+ann(f,M)+'\n'
def program(name,descr,init,f,M,guard,body):
 text='/*\n * '+descr+'\n * All variables are real. Every finite exit is counted as termination.\n * No fixed horizon is imposed. The quadratic sublevel set is inductive.\n */\n\n'+init+'\n\n'+ann(f,M)+'\nwhile '+guard+' do\n'+body+'od;\n\n'+ann(f,M)+'\nrefute true;\n'
 (P/name).write_text(text)

def binary(f,M,prob,a1,a2):
 return b(1,f,M)+'  if prob('+prob+') then\n'+b(2,f,M)+'    '+a1+'\n  else\n'+b(2,f,M)+'    '+a2+'\n  fi\n'
program('rcd_01_biased_exact.pp','Biased two-coordinate descent for f=x^2+x*y+y^2; selection (1/4,3/4).','x := 1;\ny := 1;',f2,'3','16 * ('+f2+') > 1',binary(f2,'3','0.25','x := -0.5*y','y := -0.5*x'))
program('rcd_02_damped.pp','Half-step randomized coordinate descent; both coordinates selected fairly.','x := 2;\ny := -1;',f2,'3','64 * ('+f2+') > 1',binary(f2,'3','0.5','x := 0.5*x - 0.25*y','y := 0.5*y - 0.25*x'))
body=b(1,f3,'5')+'  if prob(0.5) then\n'+b(2,f3,'5')+'    if prob(0.5) then\n'+b(3,f3,'5')+'      x := 0.5 - 0.5*y\n    else\n'+b(3,f3,'5')+'      y := -0.5 - 0.5*x\n    fi\n  else\n'+b(2,f3,'5')+'    z := 0.5\n  fi\n'
program('rcd_03_shifted_3d.pp','Shifted 3D quadratic with coupled x,y and anisotropic z; selection (1/4,1/4,1/2).','x := 2;\ny := 0;\nz := 1.5;',f3,'5','16 * ('+f3+') > 1',body)
program('rcd_04_reciprocal_anisotropic.pp','Anisotropic shifted quadratic, exact random coordinate minimization, stopped at f<=15/8.','x := 2.5;\ny := -1.75;',f4,'2.5','8 * ('+f4+') > 15',binary(f4,'2.5','0.5','x := 1','y := -2'))
body=b(1,f2,'1')+'  if prob(0.5) then\n'+b(2,f2,'1')+'    if prob(0.5) then\n'+b(3,f2,'1')+'      x := 0.5*x - 0.25*y\n    else\n'+b(3,f2,'1')+'      x := -0.5*y\n    fi\n  else\n'+b(2,f2,'1')+'    if prob(0.5) then\n'+b(3,f2,'1')+'      y := 0.5*y - 0.25*x\n    else\n'+b(3,f2,'1')+'      y := -0.5*x\n    fi\n  fi\n'
program('rcd_05_reciprocal_random_step.pp','Coupled quadratic, random coordinate and independent random step length (half or exact).','x := 1;\ny := -1;',f2,'1','4 * ('+f2+') > 3',body)
items=[
 dict(id='RCD-P1',file='rcd_01_biased_exact.pp',mode='positive',eta='x*x+x*y+y*y',k='1',a_or_b='1/16',threshold_kind='a',q_certified='7/8',c='7/8',eta0='3',prefactor='48',objective=f2,initial={'x':'1','y':'1'},invariant_upper='3',notes='Biased coordinate choices, no union-of-lines restriction.'),
 dict(id='RCD-P2',file='rcd_02_damped.pp',mode='positive',eta='x*x+x*y+y*y',k='1',a_or_b='1/64',threshold_kind='a',q_certified='13/16',c='13/16',eta0='3',prefactor='192',objective=f2,initial={'x':'2','y':'-1'},invariant_upper='3',notes='Half steps; global quadratic certificate.'),
 dict(id='RCD-P3',file='rcd_03_shifted_3d.pp',mode='positive',eta=f3,k='1',a_or_b='1/16',threshold_kind='a',q_certified='7/8',c='7/8',eta0='5',prefactor='80',objective=f3,initial={'x':'2','y':'0','z':'3/2'},invariant_upper='5',notes='3D shifted optimum and unequal coordinate probabilities.'),
 dict(id='RCD-R1',file='rcd_04_reciprocal_anisotropic.pp',mode='reciprocal',eta='5-((x-1)*(x-1)+4*(y+2)*(y+2))',k='1',a_or_b='25/8',threshold_kind='b',c='13/10',D='5/2',r0='1',eta0='5/2',prefactor='5/4',objective=f4,guard_threshold='15/8',initial={'x':'5/2','y':'-7/4'},invariant_upper='5/2',notes='Polynomial progress complement; first and second moments include exits.'),
 dict(id='RCD-R2',file='rcd_05_reciprocal_random_step.pp',mode='reciprocal',eta='2-(x*x+x*y+y*y)',k='1',a_or_b='5/4',threshold_kind='b',c='181/160',D='1409/512',r0='1',eta0='1',prefactor='5/4',objective=f2,guard_threshold='3/4',initial={'x':'1','y':'-1'},invariant_upper='1',notes='Random coordinate and step length; quartic second-moment SOS witness.')
]
for i in items:
 if i['mode']=='reciprocal':
  c,D,r=map(F,[i['c'],i['D'],i['r0']]);p=(D-c*c)/(D-2*r*c+r*r);z=(D-r*c)/(c-r);q=p/r+(1-p)/z
  i.update(p_star=str(p),z_star=str(z),q_certified=str(q))
items[3]['additional_certificates']=[{'k':'1/2','q_certified':'19/20','prefactor_exact':'sqrt(5)/2'},{'k':'2','q_certified':'29/32','prefactor_exact':'25/16'}]
items[4]['all_positive_k_feasible']=True
for i in items:i['eta_expression']=i['eta']
for i in items:i['source_sha256']=hashlib.sha256((P/i['file']).read_bytes()).hexdigest()
(P/'certificates.json').write_text(json.dumps(items,indent=2,ensure_ascii=False)+'\n')
