"""Reproducible encodings of the supplied paper's benchmark figures.

Only syntax lowering and sound interval/Boolean annotations are automatic. Any repairs
or completions of inconsistent/elliptic pseudocode are explicit inventory data.
The production analyzer is not modified by this benchmark generator.
"""
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INVENTORY = []


def number(value):
    value = F(value)
    # Benchmark constants all have terminating decimal expansions.
    from decimal import localcontext
    with localcontext() as ctx:
        ctx.prec = 100
        result = format(Decimal(value.numerator)/Decimal(value.denominator), 'f')
    assert F(result) == value
    return result.rstrip('0').rstrip('.') if '.' in result else result


def annotation(state):
    terms=[]
    for var,(lo,hi) in state.items():
        if lo is not None and hi is not None and lo==hi:
            terms.append(f'{var} = {number(lo)}')
            if var == 'alive' and lo not in (0, 1):
                # Keep impossible intermediate intervals explicitly empty.
                terms.append('(alive = 0 or alive = 1)')
        else:
            if lo is not None: terms.append(f'{number(lo)} <= {var}')
            if hi is not None: terms.append(f'{var} <= {number(hi)}')
            # This introduced control flag is assigned only 0 or 1. Retaining
            # its exact range prevents spurious cycles at the 0.5 guard boundary
            # when the analyzer takes closed real overapproximations.
            if var == 'alive': terms.append('(alive = 0 or alive = 1)')
    return ' and '.join(terms) or 'true'


def join(states):
    keys=states[0].keys()
    return {k:(None if any(s[k][0] is None for s in states) else min(s[k][0] for s in states),
               None if any(s[k][1] is None for s in states) else max(s[k][1] for s in states)) for k in keys}


def narrow(state, condition, negate=False):
    import re
    result=deepcopy(state)
    parts=condition.split(' and ')
    if negate and len(parts)>1: return result
    for part in parts:
        match=re.fullmatch(r'([A-Za-z_]+)\s*(<=|>=|=|<|>)\s*(-?[0-9.]+)',part.strip())
        if not match: continue
        var,op,value=match.groups();value=F(value)
        if negate: op={'<=':'>','>=':'<','<':'>=','>':'<=','=':'!='}[op]
        lo,hi=result[var]
        if op in ('>=','>','='): lo=value if lo is None else max(lo,value)
        if op in ('<=','<','='): hi=value if hi is None else min(hi,value)
        result[var]=(lo,hi)
    return result


# Small structured IR. Assignments are constants or increments of the same var.
def assign(var, value, add=False): return ('assign',var,F(value),add)
def assertion(condition): return ('assert',condition)
def choice(p,left,right): return ('if',f'prob({number(p)})',left,right)
def branch(condition,left,right): return ('if',condition,left,right)
def loop(condition,invariant,body): return ('while',condition,invariant,body)
def skip(): return ('skip',)


def emit(nodes,state,indent=0):
    lines=[];state=deepcopy(state);pad='  '*indent
    for node in nodes:
        kind=node[0]
        if kind=='while':
            _,guard,inv,body=node
            # All variables have already been initialized; preserve other bounds.
            inv={**state,**{k:(None if a is None else F(a),None if b is None else F(b)) for k,(a,b) in inv.items()}}
            lines.extend([pad+'{'+annotation(inv)+'}',pad+'while '+guard+' do'])
            sub,_=emit(body,narrow(inv,guard),indent+1);lines+=sub
            lines.append(pad+'od;');state=narrow(inv,guard,True)
            continue
        lines.append(pad+'{'+annotation(state)+'}')
        if kind=='assign':
            _,var,val,add=node
            if add:
                expr=f'{var} '+('+' if val>=0 else '-')+' '+number(abs(val))
                lo,hi=state[var];state[var]=(None if lo is None else lo+val,None if hi is None else hi+val)
            else:
                expr=number(val);state[var]=(val,val)
            lines.append(pad+f'{var} := {expr};')
        elif kind=='assert':
            lines.append(pad+'assert ('+node[1]+');')
            state=narrow(state,node[1])
        elif kind=='skip':lines.append(pad+'skip;')
        elif kind=='if':
            _,cond,left,right=node
            lines.append(pad+'if '+cond+' then')
            ll,ls=emit(left,narrow(state,cond),indent+1);lines+=ll
            lines.append(pad+'else')
            rl,rs=emit(right,narrow(state,cond,True),indent+1);lines+=rl
            lines.append(pad+'fi;');state=join([ls,rs])
        else:raise ValueError(node)
    return lines,state


def save(family,label,initial,body,figure,parameters,category='upper',notes=None,status='paper_parameterization',folder='pp'):
    stem=family.lower()+'_'+label
    nodes=[assign(k,v) for k,v in initial.items()]+body
    lines,_=emit(nodes,{})
    comments=[f'{family}; paper figure {figure}; parameters {parameters}.',
              f'Provenance status: {status}. Paper target: {category} bound.',
              'Annotations are sound interval overapproximations, checked by prepare_program.',
              'Sequential updates replace tuple updates only when RHS variables do not cross-depend.']+(notes or [])
    source='/*\n * '+'\n * '.join(comments)+'\n */\n\n'+'\n'.join(lines)+'\n'
    path=ROOT/folder/(stem+'.pp');path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source)
    INVENTORY.append({'id':stem,'family':family,'parameters':parameters,'figure':figure,
                      'paper_bound_direction':category,'translation_status':status,'notes':notes or [],
                      'source':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.encode()).hexdigest()})


def race():
    for x0 in [40,35,45]:
        inv={'x':(x0,100),'y':(0,101)}
        body=[choice(F(1,2),[assign('x',1,True),assign('y',2,True)],[assign('x',1,True)])]
        save('Race',f'x{x0}_y0',{'x':x0,'y':0},[loop('x <= 99 and y <= 99',inv,body),assertion('x >= 100')],1,{'x':x0,'y':0})


def rdwalk():
    for horizon in [400,500,600]:
        body=[choice(F(3,4),[assign('x',1,True)],[assign('x',-1,True)]),assign('t',1,True)]
        save('Rdwalk',f't{horizon}',{'x':0,'t':0},[loop('x <= 99',{'x':(None,100),'t':(0,None)},body),assertion(f't <= {horizon}')],2,{'T_greater_than':horizon},notes=['Unbounded lower x and upper t are retained; no finite horizon is imposed.'])


def walks():
    for x0 in [10,50,100]:
        body=[assertion('x <= 1000'),choice(F(1,2),[assign('x',-2,True)],[assign('x',1,True)])]
        save('1DWalk',f'x{x0}',{'x':x0},[loop('x >= 0',{'x':(-2,1001)},body)],6,{'x':x0})
    for x0,y0 in [(1000,10),(500,40),(400,50)]:
        body=[choice(F(1,2),[choice(F(3,4),[assign('x',1,True)],[assign('x',-1,True)])],
                     [choice(F(3,4),[assign('y',-1,True)],[assign('y',1,True)])]),assertion('x >= 1')]
        save('2DWalk',f'x{x0}_y{y0}',{'x':x0,'y':y0},[loop('y >= 1',{'x':(0,None),'y':(0,None)},body)],7,{'x':x0,'y':y0},notes=['Initial values follow Table 1, not the zero placeholders in Figure 7.'])
    for x0,y0,z0 in [(100,100,100),(100,150,200),(300,100,150)]:
        # Retain the sum assertion; use lower-only annotations to avoid redundant LP bounds.
        body=[assertion('x + y + z <= 1000'),choice(F(9,10),
              [choice(F(1,2),[assign('x',-1,True),assign('y',-1,True)],[assign('z',-1,True)])],
              [choice(F(1,2),[assign('x','0.1',True),assign('y','0.1',True)],[assign('z','0.1',True)])])]
        save('3DWalk',f'x{x0}_y{y0}_z{z0}',{'x':x0,'y':y0,'z':z0},[loop('x >= 0 and y >= 0 and z >= 0',{'x':(-1,None),'y':(-1,None),'z':(-1,None)},body)],8,{'x':x0,'y':y0,'z':z0},notes=['All three initial values come from Table 1; Figure 8 omits z initialization.'])


def prspeed():
    for horizon in [150,200,250]:
        speed=choice(F(1,2),[choice(F(1,2),[skip()],[assign('x',1,True)])],
                           [choice(F(1,2),[assign('x',2,True)],[assign('x',3,True)])])
        body=[branch('y <= 49',[choice(F(1,2),[assign('y',1,True)],[skip()])],[speed]),
              assign('t',1,True),assertion(f't <= {horizon}')]
        save('Prspeed',f't{horizon}',{'x':0,'y':0,'t':0},[loop('x <= 47',{'x':(0,50),'y':(0,50),'t':(0,horizon)},body)],10,{'T_greater_than':horizon},notes=['Four equiprobable updates are encoded by two fair choices; time counts original iterations.'])


def hardware():
    for p in [F('1e-7'),F('1e-5'),F('1e-4')]:
        body=[choice(p,[assign('alive',0)],[choice(F(3,4),[assign('x',1,True)],[assign('x',-1,True)])])]
        save('M1DWalk',f'p{number(p)}',{'x':1,'alive':1},[loop('x <= 99 and alive >= 0.5',{'x':(None,100),'alive':(0,1)},body),assertion('alive < 0.5')],3,{'p':number(p)},'lower',notes=['exit becomes alive=0; successful completion violates the assertion, as in Figure 3. Flag tests use threshold 0.5, equivalent on reachable flags 0/1.','Current analyzer computes an UPPER bound for this same success event, not the paper lower bound.'])
    for p in [F('.0005'),F('.001'),F('.0015')]:
        # Preserve each independent hazard, including the two 0.9999 checks.
        hazards=[(1-p)**5,F('.9999'),F('.9999'),(1-p)**3,(1-p)**6]
        body=[]
        for probability in hazards:
            body.append(branch('alive >= 0.5',[choice(probability,[skip()],[assign('alive',0)])],[skip()]))
        body.append(branch('alive >= 0.5',[assign('i',1,True)],[skip()]))
        save('Newton',f'p{number(p)}',{'i':0,'alive':1},[loop('i <= 40 and alive >= 0.5',{'i':(0,41),'alive':(0,1)},body),assertion('alive < 0.5')],11,{'p':number(p)},'lower',notes=['Missing final assertion is supplied using Section 3.3 hardware-success event.','exit is encoded by a flag; all subsequent hazards/updates are skipped when alive=0.','No numerical Newton update is invented: the paper explicitly abstracts it to skip.'])
    for p in [F('1e-7'),F('1e-6'),F('1e-5')]:
        inner=[choice((1-p)**3,[assign('k',1,True)],[assign('alive',0)])]
        middle=[assign('k',0),loop('k <= 15 and alive >= 0.5',{'k':(0,16),'alive':(0,1)},inner),branch('alive >= 0.5',[assign('j',1,True)],[skip()])]
        outer=[assign('j',0),loop('j <= 15 and alive >= 0.5',{'j':(0,16),'k':(0,16),'alive':(0,1)},middle),
               branch('alive >= 0.5',[choice(1-p,[assign('i',1,True)],[assign('alive',0)])],[skip()])]
        save('Ref',f'p{number(p)}',{'i':0,'j':0,'k':0,'alive':1},[loop('i <= 19 and alive >= 0.5',{'i':(0,20),'j':(0,16),'k':(0,16),'alive':(0,1)},outer),assertion('alive < 0.5')],12,{'p':number(p)},'lower',notes=['Three nested loops and all hazards are retained; source has 20*(16*16*3+1)=15380 elementary survival factors.','Final success event is made explicit as for Figure 3; results are upper, not lower, bounds.'])


def literal_rdadder():
    # A literal reading of the inconsistent RdAdder, for auditing only.
    body=[choice(F(1,2),[assign('i',1,True),assign('x',1,True)],[assign('i',1,True)]),assertion('x <= 200')]
    save('RdAdderLiteral','figure4',{'i':0,'x':0},[loop('x <= 99',{'i':(0,None),'x':(0,100)},body)],4,
         {'literal_assertion':'x <= 200'},status='literal_degenerate_zero_violation',folder='literal',notes=[
             'The assertion remains inside the loop as printed. This literal figure has zero violation probability.',
             'It does not represent any of the three Table 1 deviation events.'])


def main():
    race();rdwalk();walks();prspeed();hardware();literal_rdadder()
    (ROOT/'inventory.json').write_text(json.dumps(INVENTORY,indent=2)+'\n')
    print(f'Generated {len(INVENTORY)} inputs')


if __name__=='__main__':main()
