"""Independent exact finite-prefix probability checks for packaged examples.

Uses the package's Fraction interpreter, not the synthesis round compiler.
State count and arithmetic caps stop only between complete horizons: a partial
frontier is never reported as a true survival probability.
"""
import argparse
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

import sympy as sp
from contractive_tool.analysis.symbolic_workflow import _bound_value

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'contractive_examples'))
from pp_semantics import Program


def check(source,candidates,seconds=20):
    program=Program(source)
    initial=tuple(sorted(program.initial.items()))
    alive={initial:Fraction(1)} if program.active(program.initial) else {}
    rows=[];started=time.monotonic();last=1000
    stop='horizon_limit'
    for n in range(last+1):
        truth=sum(alive.values(),Fraction())
        exact=sp.Rational(truth.numerator,truth.denominator)
        for candidate in candidates:
            if exact>_bound_value(candidate,n):
                raise AssertionError(f'Bound below exact probability: n={n}, id={candidate["id"]}')
        rows.append({'n':n,'true_tail_exact':str(truth),'true_tail_numeric':float(truth),'states':len(alive)})
        if not alive:
            stop='all_paths_exited';break
        if n==last: break
        if time.monotonic()-started>=seconds:
            stop='reference_time_budget';break
        following={};reason=None
        for frozen,mass in alive.items():
            if time.monotonic()-started>=seconds:
                reason='reference_time_budget';break
            if max(max(v.numerator.bit_length(),v.denominator.bit_length()) for _,v in frozen)>1024:
                reason='reference_arithmetic_budget';break
            for p,state in program.successors(dict(frozen)):
                if program.active(state):
                    key=tuple(sorted(state.items()))
                    following[key]=following.get(key,Fraction())+mass*p
            if len(following)>2000:
                reason='reference_state_budget';break
        if reason:
            stop=reason;break
        alive=following
    return {'status':'passed','method':'independent_source_Fraction_interpreter_surviving_path_propagation',
        'source_sha256':sha256(source.read_bytes()).hexdigest(),'horizons_checked':[0,rows[-1]['n']],
        'candidates_checked':len(candidates),'stop_reason':stop,'elapsed_seconds':time.monotonic()-started,
        'note':'Only complete horizons are reported; finite checks do not replace uniform proofs.', 'rows':rows}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root',type=Path)
    args=parser.parse_args()
    rows=json.loads((args.root/'results.json').read_text())
    checks=[]
    for row in rows:
        case=args.root/row['name'];source=PROJECT/row['source']
        path=case/'run/summary.json'
        summary=json.loads(path.read_text()) if path.exists() else {}
        candidates=summary.get('symbolic_workflow',{}).get('candidates',[])
        try:
            result=check(source,candidates)
        except Exception as error:
            result={'status':'failed','error':repr(error)}
        (case/'reference_check.json').write_text(json.dumps(result,indent=2)+'\n')
        record={'name':row['name'],**{k:v for k,v in result.items() if k!='rows'}}
        checks.append(record)
        (args.root/'reference_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
        print(json.dumps(record),flush=True)
    return int(any(c['status']!='passed' for c in checks))


if __name__=='__main__':
    raise SystemExit(main())
