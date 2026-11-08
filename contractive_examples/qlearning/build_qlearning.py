from pathlib import Path
from fractions import Fraction as F
import json
P=Path(__file__).resolve().parent

def dec(v):
    v=F(v)
    s=f'{float(v):.10f}'.rstrip('0').rstrip('.')
    assert F(s)==v
    return s

def ann(inv,n=0):return '  '*n+'{'+inv+'}\n'
def stmt(txt,inv,n):return ann(inv,n)+'  '*n+txt+'\n'
def action_tree(dim,probs,maxvar,rewards,alpha,gamma,inv,n):
    def assign(i,j):
        rhs=f'{dec(1-alpha)}*q{i+1} + {dec(alpha*gamma)}*{maxvar}'
        if rewards[i][j]:rhs+=' + '+dec(alpha*rewards[i][j])
        return stmt(f'q{i+1} := {rhs}',inv,n)
    if dim==1:
        if len(rewards[0])==1:return assign(0,0)
    def one(i,lev):
        def assignment(j):
            rhs=f'{dec(1-alpha)}*q{i+1} + {dec(alpha*gamma)}*{maxvar}'
            if rewards[i][j]:rhs+=' + '+dec(alpha*rewards[i][j])
            return stmt(f'q{i+1} := {rhs}',inv,lev+(len(rewards[i])>1))
        if len(rewards[i])==1:return assignment(0)
        return ann(inv,lev)+'  '*lev+'if prob(0.5) then\n'+assignment(0)+'  '*lev+'else\n'+assignment(1)+'  '*lev+'fi\n'
    out=ann(inv,n)+'  '*n+f'if prob({dec(probs[0])}) then\n'+one(0,n+1)+'  '*n+'else\n'
    if dim==2:out+=one(1,n+1)
    else:
        out+=ann(inv,n+1)+'  '*(n+1)+'if prob(0.5) then\n'+one(1,n+2)+'  '*(n+1)+'else\n'+one(2,n+2)+'  '*(n+1)+'fi\n'
    return out+'  '*n+'fi\n'

def max_tree(dim,probs,rewards,alpha,gamma,inv,n):
    if dim==2:
        out=ann(inv,n)+'  '*n+'if q1 >= q2 then\n'
        out+=action_tree(dim,probs,'q1',rewards,alpha,gamma,inv,n+1)
        out+='  '*n+'else\n'+action_tree(dim,probs,'q2',rewards,alpha,gamma,inv,n+1)
        return out+'  '*n+'fi\n'
    out=ann(inv,n)+'  '*n+'if q1 >= q2 and q1 >= q3 then\n'
    out+=action_tree(dim,probs,'q1',rewards,alpha,gamma,inv,n+1)
    out+='  '*n+'else\n'+ann(inv,n+1)+'  '*(n+1)+'if q2 >= q3 then\n'
    out+=action_tree(dim,probs,'q2',rewards,alpha,gamma,inv,n+2)
    out+='  '*(n+1)+'else\n'+action_tree(dim,probs,'q3',rewards,alpha,gamma,inv,n+2)
    return out+'  '*(n+1)+'fi\n'+'  '*n+'fi\n'

def make(name,comment,initial,inv,guard,body):
    txt='/*\n'+''.join(' * '+l+'\n' for l in comment.splitlines())+' */\n\n'
    txt+=''.join(f'q{i+1} := {dec(v)};\n' for i,v in enumerate(initial))+'\n'
    txt+=ann(inv)+f'while {guard} do\n'+body+'od;\n\n'+ann(inv)+'refute true;\n'
    (P/name).write_text(txt)

inv='0 <= q1 and q1 <= 1.25 and 0 <= q2 and q2 <= 1.25'
make('Q1_biased_noisy_two_actions.pp','One-state, two-action tabular Q-learning. alpha=1/2, gamma=1/2.\nAction probabilities 3/4 and 1/4. Rewards are {3/8,5/8} and {1/8,3/8}, equally likely.\nBellman optimum Q*=(1,3/4). Stop at weighted squared error <= 1/4.\nEvery probabilistic choice is fresh and independent conditional on the state.',[0,F(5,4)],inv,'(q1-1)*(q1-1) + 3*(q2-0.75)*(q2-0.75) > 0.25',max_tree(2,[F(3,4),F(1,4)],[[F(3,8),F(5,8)],[F(1,8),F(3,8)]],F(1,2),F(1,2),inv,1))
inv='0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5'
body=ann(inv,1)+'  if prob(0.5) then\n'+stmt('q1 := 0.5*q1 + 0.25*q2 + 0.375',inv,2)+'  else\n'+stmt('q2 := 0.5*q2 + 0.25*q1',inv,2)+'  fi\n'
make('Q2_two_state_cycle.pp','Two-state, one-action-per-state tabular Q-learning with generative sampling.\nThe deterministic transitions alternate the two states. Rewards are 3/4 and 0.\nEach iteration chooses either state with probability 1/2; alpha=gamma=1/2.\nBellman optimum Q*=(1,1/2). Stop at squared error <= 1/64.',[0,F(3,2)],inv,'(q1-1)*(q1-1) + (q2-0.5)*(q2-0.5) > 0.015625',body)
inv='0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1 and 0 <= q3 and q3 <= 1'
make('Q3_three_action_max.pp','One-state, three-action tabular Q-learning. alpha=1/2, gamma=1/4.\nAction probabilities 1/2,1/4,1/4; deterministic rewards 3/4,1/2,1/4.\nBellman optimum Q*=(1,3/4,1/2). The maximum is expanded into branches.\nStop at weighted squared error <= 1/64.',[0,1,1],inv,'(q1-1)*(q1-1) + 2*(q2-0.75)*(q2-0.75) + 2*(q3-0.5)*(q3-0.5) > 0.015625',max_tree(3,[F(1,2),F(1,4),F(1,4)],[[F(3,4)],[F(1,2)],[F(1,4)]],F(1,2),F(1,4),inv,1))
inv='0 <= q1 and q1 <= 1 and 0 <= q2 and q2 <= 1'
make('Q4_reciprocal_underestimate.pp','One-state, two-action Q-learning from underestimates. alpha=gamma=1/2.\nBoth rewards are 1/2. Each action is selected with probability 1/2.\nBellman optimum Q*=(1,1). Stop when q1+q2 reaches 3/2.\nThis is a progress milestone, not a squared-error tolerance.',[0,0],inv,'q1 + q2 < 1.5',max_tree(2,[F(1,2),F(1,2)],[[F(1,2)],[F(1,2)]],F(1,2),F(1,2),inv,1))
inv='0 <= q1 and q1 <= 1.5 and 0 <= q2 and q2 <= 1.5'
make('Q5_reciprocal_noisy_progress.pp','One-state, two-action Q-learning with random rewards. alpha=gamma=1/2.\nEach action is selected with probability 1/2. Rewards are {1/2,3/4} and {1/4,1/2}.\nEach reward choice is fair. Bellman optimum Q*=(5/4,1).\nStop when q1+q2 reaches 5/8, a progress milestone from the zero initialization.\nThe full box is inductive; low-reward updates may decrease q1+q2 while the guard holds.',[0,0],inv,'q1 + q2 < 0.625',max_tree(2,[F(1,2),F(1,2)],[[F(1,2),F(3,4)],[F(1,4),F(1,2)]],F(1,2),F(1,2),inv,1))
items=[
 dict(id='Q1',file='Q1_biased_noisy_two_actions.pp',mode='positive',eta='(q1-1)^2+3*(q2-3/4)^2',k='1',a_or_b='1/4',a='1/4',eta0='7/4',q_certified='123/128',initial_factor='7',degree=2),
 dict(id='Q2',file='Q2_two_state_cycle.pp',mode='positive',eta='(q1-1)^2+(q2-1/2)^2',k='1',a_or_b='1/64',a='1/64',eta0='2',q_certified='25/32',initial_factor='128',degree=2),
 dict(id='Q3',file='Q3_three_action_max.pp',mode='positive',eta='(q1-1)^2+2*(q2-3/4)^2+2*(q3-1/2)^2',k='1',a_or_b='1/64',a='1/64',eta0='13/8',q_certified='115/128',initial_factor='104',degree=2),
 dict(id='Q4',file='Q4_reciprocal_underestimate.pp',mode='reciprocal',eta='1+q1+q2',k='1',a_or_b='5/2',b='5/2',eta0='1',c='41/40',D='25/16',r0='1',r_upper='5/4',p_star='819/820',z_star='43/2',q_certified='859/860',q_mom='859/860',q_direct='49/50',initial_factor='5/2',degree=1),
 dict(id='Q5',file='Q5_reciprocal_noisy_progress.pp',mode='reciprocal',eta='1+q1+q2',k='1',a_or_b='13/8',b='13/8',eta0='1',c='115/104',D='201/128',r0='51/52',r_upper='11/8',p_star='7519/7857',z_star='10509/2704',q_certified='528892/535959',q_mom='528892/535959',q_direct='520/561',initial_factor='13/8',degree=1)
]
for item in items:
 item['eta_expression']=item['eta'].replace('^','**')
 if item['mode']=='positive':item['c']=item['q_certified']
(P/'certificates.json').write_text(json.dumps(items,indent=2,ensure_ascii=False)+'\n')
print('Wrote 5 .pp programs and certificates.json')
