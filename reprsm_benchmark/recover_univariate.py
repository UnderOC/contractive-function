"""Experiment-only recovery checked by exact univariate root counting.

Numerical rounding, shifts, and relaxed c only propose candidates. Every original
positive/full-moment obligation is rebuilt and proved over exact rational domains.
"""
from functools import lru_cache
from pathlib import Path
from fractions import Fraction
import argparse
import json
import time

import sympy as sp
from contractive_tool.algebra import PolynomialService
from contractive_tool.algebra.polynomial import arithmetic_to_symbolic
from contractive_tool.analysis.semantics import prepare_program
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.expectation import ExpectationEngine
from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.semantic import check_program
from contractive_tool.positivity.ir import BasicSet, Implication
from contractive_tool.positivity.selector import prepare
from contractive_tool.positivity.domains import interval_features


def nonnegative(domain, h):
    domain, h, empty = prepare(Implication('check', domain, sp.expand(h), {}, ()))
    if empty or h == 0:
        return {'method':'empty_domain' if empty else 'zero_identity'}
    if not h.free_symbols:
        return {'method':'rational_constant'} if h >= 0 else None
    if len(domain.variables) != 1 or domain.equalities:
        return None
    x = domain.variables[0]
    features = interval_features(domain)
    if not features['affine_generators']:
        return None
    lower, upper = features['bounds'][str(x)]
    lo = -sp.oo if lower == 'None' else sp.Rational(lower)
    hi = sp.oo if upper == 'None' else sp.Rational(upper)
    if lo > hi:
        return {'method':'empty_interval'}
    poly = sp.Poly(h, x, domain=sp.QQ)
    if lo == hi:
        return {'method':'singleton'} if poly.eval(lo) >= 0 else None
    for endpoint in (lo, hi):
        if endpoint.is_finite and poly.eval(endpoint) < 0:
            return None
    # Each odd-multiplicity interior root forces a sign change. Even roots
    # preserve the sign, so one non-root sign check then proves the whole interval.
    for factor, multiplicity in poly.sqf_list()[1]:
        if multiplicity % 2:
            count = int(factor.count_roots(lo, hi))
            count -= int(bool(lo.is_finite) and factor.eval(lo) == 0)
            count -= int(bool(hi.is_finite) and factor.eval(hi) == 0)
            if count:
                return None
    for i in range(1, poly.degree()+3):
        test = (lo+(hi-lo)*sp.Rational(i, poly.degree()+3) if lo.is_finite and hi.is_finite
                else hi-i if hi.is_finite else lo+i if lo.is_finite else sp.Integer(i))
        value = poly.eval(test)
        if value:
            if value < 0:
                return None
            return {'method':'exact_square_free_root_count_and_sign',
                    'interval':[str(lo),str(hi)], 'positive_test_point':str(test)}
    raise AssertionError('A nonzero polynomial cannot vanish at all distinct test points')


def verify_raw(cfg, evidence, raw, c, delta=sp.Rational(1, 1000000)):
    if not (c.is_Rational and delta.is_Rational and 0 < c < 1 and 0 < delta <= 1):
        return None
    if set(raw) != set(evidence.locations):
        return None
    variables = tuple(sp.Symbol(n) for n in cfg.symbols.program_variables)
    if any(not expr.free_symbols.issubset(set(variables)) for expr in raw.values()):
        return None
    for expr in raw.values():
        sp.Poly(expr, *variables, domain=sp.QQ)
    terminals={cfg.normal_terminal,cfg.failure_terminal}
    if raw[cfg.normal_terminal] != delta or raw[cfg.failure_terminal] != 1:
        return None
    checks=[]
    for loc in sorted(set(evidence.locations)-terminals):
        for i,domain in enumerate(evidence.domains[loc]):
            proof=nonnegative(domain,raw[loc]-delta)
            if proof is None:
                return None
            checks.append({'id':f'{loc}_positive_{i}',**proof})
    engine,service=ExpectationEngine(),PolynomialService()
    functions={loc:service.normalize(expr) for loc,expr in raw.items()}
    for group in cfg.transitions:
        if group.id not in evidence.group_domains:
            continue
        pre,_=engine.transition_expectation(functions,group)
        residual=sp.expand(c*raw[group.source]-pre.expression)
        for i,domain in enumerate(evidence.group_domains[group.id]):
            proof=nonnegative(domain,residual)
            if proof is None:
                return None
            checks.append({'id':f'{group.id}_contraction_{i}',**proof})
    objective=engine.random_expectation(raw[evidence.start].subs(evidence.initial,simultaneous=True),
                                       evidence.initial_random_model).expression
    assert objective.is_Rational and objective>=0
    return {'status':'proved','method':'exact_original_obligations_univariate_roots',
            'A_exact':str(objective),'upper_bound_exact':str(min(1,objective)),
            'A_numeric':float(objective),'c':str(c),'checks':checks}


def zero_flag_constants(cfg, evidence, c, delta):
    flag=sp.Symbol('alive')
    successors={}
    for loc in set(evidence.locations)-{cfg.normal_terminal,cfg.failure_terminal}:
        groups=[]
        for g in cfg.outgoing(loc):
            enabled=False
            for domain in evidence.group_domains.get(g.id,[]):
                d=BasicSet(domain.variables,domain.generators,domain.equalities+(flag,))
                _,_,empty=prepare(Implication('zero_flag',d,sp.Integer(1),{},()))
                if not empty:
                    enabled=True
            if enabled:
                groups.append(g)
        successors[loc]=groups
    visiting=set()
    @lru_cache(None)
    def value(loc):
        if loc==cfg.normal_terminal:
            return delta
        if loc==cfg.failure_terminal:
            return sp.Integer(1)
        if loc in visiting:
            raise ValueError('Zero-flag graph has a cycle')
        visiting.add(loc)
        values=[delta]
        for group in successors[loc]:
            values.append(sum(arithmetic_to_symbolic(b.probability)*value(b.destination)
                              for b in group.branches)/c)
        visiting.remove(loc)
        return max(values)
    return {loc:value(loc) for loc in successors}


def recover(run, seconds=90):
    task=json.loads((run.parent/'task.json').read_text())
    cfg=build_cfg(check_program(parse_file(task['source'])))
    evidence=prepare_program(cfg)
    variables=tuple(sp.Symbol(n) for n in cfg.symbols.program_variables)
    if len([x for x in variables if str(x)!='alive'])>1:
        return {'status':'not_applicable'}
    problem_paths=list(run.glob('analyses/assertion_violation/degrees/*/*/polynomial_problem.json'))
    if not problem_paths:
        return {'status':'no_numerical_candidate'}
    # The serialized polynomial problem preserves the exact template expressions.
    problem=json.loads(problem_paths[0].read_text())
    expressions=problem['expressions']
    pools=[]
    for path in run.rglob('solver.json'):
        data=json.loads(path.read_text())
        if data.get('values'):
            pools.append((str(path.relative_to(run)),data['values']))
    for path in run.rglob('repair.json'):
        data=json.loads(path.read_text())
        for i,a in enumerate(data.get('attempts',[])):
            values=a.get('solver',{}).get('values')
            if values:
                pools.append((str(path.relative_to(run))+f':attempt:{i}',values))
    original_c=sp.Rational(task['c']);delta=sp.Rational(task['options']['assertion_margin'])
    deadline=time.monotonic()+seconds
    best=None;attempts=0
    for label,values in pools:
        substitutions={sp.Symbol(k):sp.Rational(str(v)) for k,v in values.items()}
        raw={loc:sp.expand(sp.sympify(expr).xreplace(substitutions)) for loc,expr in expressions.items()}
        if any(expr.free_symbols-set(variables) for expr in raw.values()):
            continue
        for c in (original_c,1-(1-original_c)/10,1-(1-original_c)/100,1-(1-original_c)/1000):
            constants=zero_flag_constants(cfg,evidence,c,delta) if sp.Symbol('alive') in variables else None
            for shift in (sp.Integer(0),sp.Rational(1,10**8),sp.Rational(1,10**7),sp.Rational(1,10**6),sp.Rational(1,10**5)):
                if time.monotonic()>=deadline:
                    break
                proposal={}
                for loc,expr in raw.items():
                    if loc in (cfg.normal_terminal,cfg.failure_terminal):
                        proposal[loc]=expr
                    elif constants is None:
                        proposal[loc]=sp.expand(expr+shift)
                    else:
                        flag=sp.Symbol('alive')
                        proposal[loc]=sp.expand(flag*(expr.subs(flag,1)+shift)+(1-flag)*constants[loc])
                attempts+=1
                checked=verify_raw(cfg,evidence,proposal,c,delta)
                if checked and (best is None or sp.Rational(checked['A_exact'])<sp.Rational(best['A_exact'])):
                    best={**checked,'raw_polynomials':{k:str(v) for k,v in proposal.items()},
                          'source':task['source'],'source_sha256':task['source_sha256'],
                          'positivity_margin':str(delta),'numerical_origin':label,
                          'solved_c':str(original_c),'constant_shift':str(shift),
                          'degree':max(int(sp.Poly(v,*variables).total_degree()) for v in proposal.values())}
                    print(json.dumps({'case':task['case'],'recovered_A':best['A_numeric'],'c':str(c),'degree':best['degree']}),flush=True)
        if time.monotonic()>=deadline:
            break
    result=best or {'status':'not_recovered'}
    result['recovery_attempts']=attempts
    (run/'univariate_recovery.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('runs',type=Path,nargs='+')
    parser.add_argument('--seconds',type=float,default=90)
    args=parser.parse_args()
    for run in args.runs:
        result=recover(run,args.seconds)
        print(json.dumps({'run':str(run),'status':result['status'],'A':result.get('A_numeric')}),flush=True)
