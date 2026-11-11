"""Isolate exact recovery from previously saved numerical repair outputs.
No source/template edits, no new SDP solve, and no change to baseline results.
"""
from pathlib import Path
import json,time,hashlib
import sympy as sp
from contractive_tool.positivity.ir import ConicModel
from contractive_tool.backends.cvxpy.verification import reconstruct,check_conic_values
from contractive_tool.analysis_pipeline import SearchOptions
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.semantic import check_program
from contractive_tool.analysis.invariant_certification import prepare_certified_program
from contractive_tool.analysis.symbolic_rounds import prepare_symbolic_round_kernel,make_symbolic_round_problem
from contractive_tool.positivity.registry import StrategyRegistry
from contractive_tool.positivity.selector import build_plan
from contractive_tool.positivity.base import EncodingLimits
HERE=Path(__file__).resolve().parent;TOOL=HERE.parents[1]
RUN=TOOL/'generated/conditional_qlearning_20261109/Q3_three_action_max/run'
read=lambda p:json.loads(p.read_text())
canonical=lambda d:json.loads(json.dumps(d,default=str))
manifest=read(RUN/'manifest.json');source=Path(manifest['source'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['source_sha256']
cfg=build_cfg(check_program(parse_file(source)))
evidence=prepare_certified_program(cfg,saved_evidence=read(RUN/'analyses/tailbound/domain_evidence.json'))
kernel=prepare_symbolic_round_kernel(cfg,evidence);options=SearchOptions(**manifest['options'])
records=[]
for case,c in [('c-003','7/8'),('c-004','15/16')]:
 directory=RUN/'analyses/tailbound/degrees/2'/case
 attempt=directory/'attempts/002';audit=read(attempt/'repair.json');values=audit['attempts'][0]['solver']['values']
 model=ConicModel.from_data(read(attempt/'conic_model.json'))
 started=time.monotonic();verification=reconstruct(model,values,deadline=started+60)
 record={'case':case,'c':c,'status':verification['status'],'elapsed_seconds':time.monotonic()-started,'extra_reconstruction_budget_seconds':60,'source_sha256':manifest['source_sha256'],'saved_repair':str(attempt/'repair.json'),'saved_conic_model':str(attempt/'conic_model.json'),'verification':verification,'new_solver_calls':0}
 if verification['status']=='proved':
  assert check_conic_values(model,verification['exact_values'])
  problem=make_symbolic_round_problem(cfg,kernel,2,sp.Rational(c),options.max_decisions,template_variables=options.tail_variables)
  assert canonical(problem.to_data())==read(directory/'polynomial_problem.json')
  plan=read(attempt/'encoding_plan.json');order=plan['choices'][0]['order']
  rebuilt,rebuilt_plan=build_plan(problem.obligations,problem.decisions,problem.objective,StrategyRegistry(options.enabled_strategies),plan['requested_strategy'],order,2*order,EncodingLimits(options.max_products,options.max_psd_dimension,options.max_decisions),fallback=options.strategy=='auto')
  assert canonical(rebuilt.to_data())==read(attempt/'conic_model.json') and rebuilt_plan['choices']==plan['choices']
  sub={sp.Symbol(k):sp.Rational(v) for k,v in verification['exact_values'].items()}
  A=problem.objective.xreplace(sub);assert A==sp.Rational(verification['bound_exact'])
  record.update(source_model_rebuild='passed',exact_cone_recheck='passed',eta=str(sp.expand(problem.expressions[kernel.header].xreplace(sub))),prefactor=str(A),decay=c,tail_bounds={str(n):float(min(1,A*sp.Rational(c)**n)) for n in (10,50,100)})
 (HERE/(case+'_reconstruction.json')).write_text(json.dumps(record,indent=2)+'\n')
 records.append({k:v for k,v in record.items() if k!='verification'})
 (HERE/'summary.json').write_text(json.dumps(records,indent=2)+'\n')
 print(case,record['status'],round(record['elapsed_seconds'],2),record.get('tail_bounds'),flush=True)
