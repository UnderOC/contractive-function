"""Degree -> contraction parameter -> positivity encoding search."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from fractions import Fraction
from importlib import metadata
import hashlib
import json
import math
from pathlib import Path
import time

import sympy as sp

from contractive_tool import __version__
from contractive_tool.analysis.degree_policy import DegreePolicy
from contractive_tool.analysis.certificate_families import get_family
from contractive_tool.analysis.parameter_search import ContractionBisection, FixedContractionGrid
from contractive_tool.analysis.semantics import prepare_program, prove_nonnegative
from contractive_tool.analysis.rounds import prepare_round_kernel, make_round_problem
from contractive_tool.analysis.symbolic_rounds import (
    prepare_symbolic_round_kernel, make_symbolic_round_problem, SymbolicRoundKernel)
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.semantic import check_program
from contractive_tool.errors import AnalysisError
from contractive_tool.pipeline import compile_to_cfg
from contractive_tool.positivity.base import EncodingLimits
from contractive_tool.positivity.registry import StrategyRegistry
from contractive_tool.positivity.selector import build_plan


@dataclass(frozen=True)
class SearchOptions:
    initial_degree: int = 1
    max_degree: int = 6
    degree_step: int = 1
    continue_after_success: bool = False
    c_values: tuple[str,...] | None = None
    max_c_steps: int = 10
    max_order: int = 4
    max_attempts_per_point: int = 2
    max_parameter_points: int = 32
    strategy: str = 'auto'
    enabled_strategies: tuple[str,...] = ('putinar','schmudgen','handelman')
    max_products: int = 256
    max_psd_dimension: int = 80
    max_decisions: int = 20000
    total_seconds: float = 300
    per_attempt_seconds: float = 30
    verbose: bool = True
    family: str = 'polynomial'
    tail_rule: str = 'auto'

    def validate(self):
        degrees = DegreePolicy(self.initial_degree,self.max_degree,self.degree_step,self.continue_after_success)
        list(degrees.degrees())
        get_family(self.family)
        ContractionBisection(self.max_c_steps)
        cs = FixedContractionGrid(self.c_values).candidates() if self.c_values is not None else None
        if self.tail_rule not in ('auto','round_survival','late_bad_exit'):
            raise AnalysisError('Unknown tail rule')
        if self.strategy not in ('auto',)+StrategyRegistry.known:
            raise AnalysisError('Unknown positivity strategy')
        StrategyRegistry(self.enabled_strategies)
        budgets = (self.max_order,self.max_attempts_per_point,self.max_parameter_points,self.max_products,
                   self.max_psd_dimension,self.max_decisions,self.total_seconds,self.per_attempt_seconds)
        if any(not math.isfinite(v) or v<=0 for v in budgets) or self.max_order>8:
            raise AnalysisError('Budgets must be positive and finite; max_order <= 8')
        return degrees,cs


def write_json(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_template_check(problem, numerical_values):
    """Alternative certificate: rounded coefficients, original-domain exact identities.

    No time-indexed repair, sampling, or assumption that rounding preserves feasibility.
    """
    for denominator in (1000,1000000):
        values = {sp.Symbol(name):sp.Rational(Fraction(numerical_values[name]).limit_denominator(denominator))
                  for name in problem.decisions}
        proofs=[]
        for obligation in problem.obligations:
            conclusion=sp.expand(obligation.conclusion.xreplace(values))
            proof=prove_nonnegative(obligation.domain,conclusion)
            if proof is None:
                break
            proofs.append({'id':obligation.id,'proof':proof})
        else:
            bound=problem.objective.xreplace(values)
            if bound>=0:
                return {'status':'proved','method':'exact_original_domain_farkas',
                        'bound_exact':str(bound),'bound_numeric':float(bound),
                        'exact_values':{str(x):str(v) for x,v in values.items()},'obligations':proofs}
    return {'status':'solved_unverified','reason':'No exact original-domain certificate recovered'}


def selected_bound(candidate, problem, cfg):
    bound = {'degree':problem.degree,'c':str(problem.c),'A_exact':candidate['bound_exact'],
            'A_numeric':candidate['bound_numeric'],'lambda_expression':f'-log({problem.c})',
            'lambda_numeric':float(-sp.log(problem.c)),
            'expression':f"({candidate['bound_exact']}) * ({problem.c})**n",
            'exponential_expression':f"({candidate['bound_exact']}) * exp(-(-log({problem.c}))*n)",
            'n_domain':'nonnegative integers','time_unit':'pcfg_transition_from_program_entry',
            'event':f'T < infinity and T > n and terminal_location == {cfg.failure_terminal}'}
    if problem.context:
        bound.update({k:v for k,v in problem.context.items() if k!='round_preexpectations'})
        bound['termination_consequence']='K is finite almost surely; finite round/exit paths imply program termination'
        bound['probability_expression']=f"min(1, {bound['expression']})"
    return bound


def run_analysis(source, goal, out_dir=None, *, options=None, model_only=False):
    options=options or SearchOptions()
    policy,cs=options.validate()
    family=get_family(options.family)
    goal={'tail_bound':'tailbound','exponential_tail':'tailbound'}.get(goal,goal)
    if goal not in {'tailbound','assertion_violation'}:
        raise AnalysisError('Goal must be tailbound or assertion_violation')
    source=Path(source).resolve()
    if out_dir is None:
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
        out_dir=Path('generated')/f'{source.stem}_{goal}_{stamp}'
    out_dir=Path(out_dir).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise AnalysisError('Use a new or empty output directory')
    started=time.monotonic()
    compile_to_cfg(source,out_dir/'shared')
    cfg=build_cfg(check_program(parse_file(source)))
    root=out_dir/'analyses'/goal
    summary={'goal':goal,'status':'unknown','selection':None,'proved_candidates':[],
             'degrees_attempted':[],'parameter_points':0,'attempt_count':0,
             'out_dir':str(out_dir),'termination':'unknown','termination_assumed':False,
             'certificate_family':'polynomial','contraction_searches':[]}
    history=[]

    def finish():
        summary['elapsed_seconds']=time.monotonic()-started
        write_json(root/'search_history.json',history)
        write_json(out_dir/'summary.json',summary)
        versions={}
        for package in ('cvxpy','numpy','scipy','mosek'):
            try: versions[package]=metadata.version(package)
            except metadata.PackageNotFoundError: versions[package]=None
        write_json(out_dir/'manifest.json',{'tool_version':__version__,'source_sha256':digest(source),
            'source':str(source),'options':asdict(options),'goal':goal,'mode':'model_only' if model_only else 'solve',
            'backend':'cvxpy','solver':'MOSEK','dependencies':versions,'matlab_invoked':False,
            'budget_policy':'soft checks between symbolic stages; hard solver optimizer time limit',
            'artifacts':{str(p.relative_to(out_dir)):digest(p) for p in sorted(out_dir.rglob('*')) if p.is_file()}})
        return summary

    try:
        if cfg.failure_terminal is None:
            raise AnalysisError('Source needs assert/refute to define the target event')
        evidence=prepare_program(cfg)
    except AnalysisError as error:
        summary.update(status='unsupported',stop_reason='semantic_evidence_unavailable',diagnostic=str(error))
        return finish()
    write_json(root/'domain_evidence.json',evidence.to_data())
    kernel = None
    if goal == 'tailbound' and options.tail_rule != 'late_bad_exit':
        try:
            kernel = prepare_round_kernel(cfg,evidence)
        except AnalysisError as error:
            summary['boolean_round_diagnostic'] = str(error)
            try:
                kernel = prepare_symbolic_round_kernel(cfg,evidence)
            except AnalysisError as symbolic_error:
                summary['round_compilation_diagnostic'] = str(symbolic_error)
                if options.tail_rule == 'round_survival':
                    summary.update(status='unsupported',stop_reason='round_evidence_unavailable')
                    return finish()
    summary['tail_rule'] = ('round_survival' if kernel else 'late_bad_exit') if goal == 'tailbound' else None
    goal_data = {'goal':goal,'event_mode':'late_bad_exit' if goal=='tailbound' else 'eventual',
        'event_source':'source assert/refute','failure_terminal':cfg.failure_terminal,
        'normal_terminal':cfg.normal_terminal,'initial_location':evidence.start,
        'initial':{str(k):str(v) for k,v in evidence.initial.items()},
        'initial_random_symbols':list(evidence.initial_random_model.symbols),
        'initial_support':[domain.to_data() for domain in evidence.initial_support],
        'prefix_steps':len(evidence.prefix),'clock':'pcfg_transition_from_program_entry',
        'prefix_adjustment':(
            'A = c**(-prefix_steps) * E[V_after_prefix(symbolic_initial_state)]'
            if goal=='tailbound' else 'none'),
        'terminal_values':{'normal':0,'failure':1},'absorbing_clock_frozen':True,
        'termination_assumed':False}
    if kernel:
        write_json(root/'round_evidence.json',kernel.to_data())
        goal_data.update(event_mode='round_survival',event='K > n',
            event_source='loop survival (bounds all late exits, including assertion failures)',
            clock='completed_loop_iterations',clock_relation=kernel.to_data()['clock'],
            prefix_adjustment='none; deterministic initialization precedes round zero',
            terminal_values={'survival_process_after_exit':0},active_normalization='eta >= 1',
            polynomial_boundary='nonnegative, not constrained to zero on completed states',
            proof_domain=('symbolic real polynomial invariant domains' if isinstance(kernel,SymbolicRoundKernel)
                          else 'inductively verified Boolean loop-head states'),
            termination_consequence='derived from a verified certificate, not assumed')
    write_json(root/'goal.json',goal_data)
    registry=StrategyRegistry(options.enabled_strategies)
    limits=EncodingLimits(options.max_products,options.max_psd_dimension,options.max_decisions)
    stop=False
    for degree in policy.degrees():
        if time.monotonic()-started>=options.total_seconds:
            summary['stop_reason']='time_budget'; break
        summary['degrees_attempted'].append(degree)
        degree_proved=[]
        search = ContractionBisection(options.max_c_steps) if cs is None else None
        search_record = {'degree':degree, **(search.to_data() if search else
                          {'method':'explicit_grid','candidates':[str(c) for c in cs]})}
        summary['contraction_searches'].append(search_record)

        def feedback(status):
            if search:
                search.observe(status)
                search_record.update(search.to_data())

        for ci,c in enumerate(search.candidates() if search else cs):
            if stop: break
            if summary['parameter_points']>=options.max_parameter_points:
                summary['stop_reason']='parameter_budget'; stop=True; break
            if time.monotonic()-started>=options.total_seconds:
                summary['stop_reason']='time_budget'; stop=True; break
            summary['parameter_points']+=1
            point_history_start=len(history)
            point_path=root/'degrees'/str(degree)/f'c-{ci+1:03d}'
            try:
                problem=(make_symbolic_round_problem(cfg,kernel,degree,c,options.max_decisions)
                         if isinstance(kernel,SymbolicRoundKernel) else
                         make_round_problem(cfg,kernel,degree,c,options.max_decisions) if kernel else
                         family.instantiate(cfg,evidence,degree,c,goal,options.max_decisions))
            except AnalysisError as error:
                history.append({'degree':degree,'c':str(c),'status':'generation_failed','reason':str(error)})
                feedback('unknown')
                continue
            write_json(point_path/'polynomial_problem.json',problem.to_data())
            if goal=='assertion_violation':
                summary.update(status='not_solved',stop_reason='assertion_backend_not_implemented',
                               model=str(point_path/'polynomial_problem.json'))
                return finish()
            max_degree=max((int(sp.Poly(o.conclusion,*o.domain.variables).total_degree())
                            if o.domain.variables and o.conclusion!=0 else 0 for o in problem.obligations),default=0)
            minimum_order=max(1,(max_degree+1)//2)
            if minimum_order>options.max_order:
                history.append({'degree':degree,'c':str(c),'status':'generation_failed',
                                'reason':'Residual degree exceeds max_order'})
                feedback('unknown')
                continue
            attempt=0
            plans=set()
            for order in range(minimum_order,options.max_order+1):
                if attempt>=options.max_attempts_per_point or stop: break
                strategies=[options.strategy]
                if options.strategy=='auto':
                    strategies+=list(registry.known)
                for strategy in strategies:
                    if attempt>=options.max_attempts_per_point or stop: break
                    if time.monotonic()-started>=options.total_seconds:
                        summary['stop_reason']='time_budget';stop=True;break
                    row={'degree':degree,'c':str(c),'order':order,'strategy':strategy,'status':'generation_failed'}
                    try:
                        model,plan=build_plan(problem.obligations,problem.decisions,problem.objective,
                            registry,strategy,order,2*order,limits,fallback=options.strategy=='auto')
                        plan_key=json.dumps(plan['choices'],sort_keys=True)
                        if plan_key in plans: continue
                        plans.add(plan_key)
                        attempt+=1
                        summary['attempt_count']+=1
                        attempt_path=point_path/'attempts'/f'{attempt:03d}'
                        row['path']=str(attempt_path.relative_to(out_dir))
                        write_json(attempt_path/'encoding_plan.json',plan)
                        write_json(attempt_path/'conic_model.json',model.to_data())
                        from contractive_tool.backends.cvxpy.builder import build
                        built=build(model)
                        if model_only:
                            summary.update(status='not_solved',stop_reason='model_only',model=str(attempt_path/'conic_model.json'))
                            row['status']='not_solved';history.append(row)
                            return finish()
                        remaining=options.total_seconds-(time.monotonic()-started)
                        if remaining<=0:
                            row['status']='unknown';summary['stop_reason']='time_budget';stop=True
                        else:
                            from contractive_tool.backends.cvxpy.mosek_solver import solve
                            from contractive_tool.backends.cvxpy.verification import reconstruct
                            solved=solve(built,time_limit=min(remaining,options.per_attempt_seconds),verbose=options.verbose)
                            (attempt_path/'solver.log').write_text(solved.pop('log'),encoding='utf-8')
                            write_json(attempt_path/'solver.json',solved)
                            row.update(status=solved['status'],raw_status=solved['raw_status'])
                            if solved.get('values') is not None:
                                verified=reconstruct(model,solved['values'])
                                if verified['status']!='proved':
                                    fallback=exact_template_check(problem,solved['values'])
                                    fallback['gram_reconstruction']=verified
                                    verified=fallback
                                if verified['status']=='proved':
                                    if sp.Rational(verified['bound_exact'])<0:
                                        raise AnalysisError('Verified objective must be nonnegative')
                                    verified['semantic_evidence']='domain_evidence.json'
                                    if kernel:
                                        verified['round_evidence']='round_evidence.json'
                                    values={sp.Symbol(n):sp.Rational(verified['exact_values'][n]) for n in problem.decisions}
                                    polynomial={l:str(v.xreplace(values)) for l,v in problem.expressions.items()}
                                    bound=selected_bound(verified,problem,cfg)
                                    bound['certificate']=str((attempt_path/'certificate.json').relative_to(out_dir))
                                    write_json(attempt_path/'certificate.json',{'polynomials':polynomial,'bound':bound,
                                        'verification_method':verified['method'],'integer_power_factorization_required':False})
                                    degree_proved.append(bound);summary['proved_candidates'].append(bound)
                                row['status']=verified['status']
                                write_json(attempt_path/'verification.json',verified)
                            if solved['status']=='solver_failed':
                                summary.update(stop_reason='solver_failed',diagnostic=solved.get('diagnostic'))
                                stop=True
                    except (AnalysisError,ImportError,ValueError) as error:
                        row['diagnostic']=f'{type(error).__name__}: {error}'
                        attempt+=1 if 'path' not in row else 0
                        if isinstance(error,ImportError):
                            summary['stop_reason']='missing_backend';stop=True
                    history.append(row)
                    if row['status']=='proved': break
                if history and history[-1]['degree']==degree and history[-1]['c']==str(c) and history[-1]['status']=='proved': break
            point_statuses=[row['status'] for row in history[point_history_start:]]
            feedback('proved' if 'proved' in point_statuses else
                     'infeasible' if point_statuses and all(s=='infeasible' for s in point_statuses) else 'unknown')
        if degree_proved and not options.continue_after_success:
            if not stop: summary['stop_reason']='first_successful_degree'
            break
        if stop: break
    summary.setdefault('stop_reason','max_degree')
    if summary['proved_candidates']:
        summary['status']='proved'
        if kernel:
            summary['termination']='proved_almost_sure'
        summary['pareto_candidates']=[b for b in summary['proved_candidates'] if not any(
            sp.Rational(a['c'])<=sp.Rational(b['c']) and sp.Rational(a['A_exact'])<=sp.Rational(b['A_exact'])
            and (a['c'],a['A_exact'])!=(b['c'],b['A_exact']) for a in summary['proved_candidates'])]
        summary['selection']=min(summary['proved_candidates'],key=lambda b:(sp.Rational(b['c']),sp.Rational(b['A_exact'])))
    elif summary['stop_reason'] in {'solver_failed','missing_backend'}:
        summary['status']='solver_failed'
    else:
        summary['status']='no_certificate_found'
    return finish()
