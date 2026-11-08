"""Positive-power searches plus an independently budgeted reciprocal branch.

Comparisons use complete, certified C*rho**n bounds. The rational portfolio
contains the integer portfolio; direct polynomial V is explicitly k=1, not an
unjustified factorization V=eta**degree. No external/generated seed is loaded.
"""
from copy import deepcopy
from decimal import Decimal
from dataclasses import asdict, replace
from pathlib import Path
import json
import math
import time

import sympy as sp

from contractive_tool.errors import AnalysisError
from contractive_tool.analysis.cauchy import (
    CauchyOptions, ExponentOptions, EtaTemplate, automatic_t_grid,
    search_fixed_eta, search_template_eta)
from contractive_tool.analysis.cauchy_expressions import parse_expression
from contractive_tool.analysis.cauchy_verification import verify_result, check_conic_values
from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.analysis.templates import total_degree_exponents, select_variables
from contractive_tool.analysis.symbolic_rounds import make_symbolic_round_problem
from contractive_tool.positivity.base import EncodingLimits
from contractive_tool.probability.fractional_moments import rational, power_enclosure


def _json(path):
    return json.loads(Path(path).read_text())


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')


def _canonical(value):
    return json.loads(json.dumps(value))


def workflow_config(options):
    data = _json(options.workflow_config) if options.workflow_config else {}
    known = {'basis', 't_values', 'exponents', 'cauchy', 'direct_fraction',
             'max_fixed_seeds', 'guided_t', 'template', 'reciprocal'}
    if set(data)-known:
        raise AnalysisError(f'Unknown workflow config fields: {sorted(set(data)-known)}')
    fraction = data.get('direct_fraction', 0.5)
    if not isinstance(fraction, (int, float)) or not math.isfinite(fraction) or not 0 < fraction < 1:
        raise AnalysisError('direct_fraction must lie in (0,1)')
    count = data.get('max_fixed_seeds', 3)
    if type(count) is not int or not 1 <= count <= 16:
        raise AnalysisError('max_fixed_seeds must be in [1,16]')
    if not isinstance(data.get('guided_t', True), bool):
        raise AnalysisError('guided_t must be Boolean')
    exponent_config = data.get('exponents', {})
    try:
        exponents = ExponentOptions(**({'interval': ('1/4','4'), 'coarse_points':16,
                                      'refinements':1} | exponent_config))
    except TypeError as error:
        raise AnalysisError(f'Invalid exponent configuration: {error}') from error
    # Always include all integer exponents in the searched interval in the
    # same state models. This is a nested, comparable integer/rational search.
    ks = set(exponents.candidates())
    if exponents.interval:
        lo, hi = map(rational, exponents.interval)
        ks.update(sp.Integer(k) for k in range(max(1, int(sp.ceiling(lo))), int(sp.floor(hi))+1))
    if len(ks) > exponents.max_candidates:
        raise AnalysisError('Exponent budget cannot cover rational grid plus integer baseline')
    exponents = replace(exponents, values=tuple(map(str, sorted(ks))), interval=None)
    settings = {'product_depth':4, 'solver_seconds':options.per_attempt_seconds,
                'repair_seconds':options.repair_seconds, 'repair_relative_gap':options.repair_relative_gap,
                'repair_max_solves':options.repair_max_solves}
    settings.update(data.get('cauchy', {}))
    # Workflow owns the global budget. Encoding limits cannot silently exceed
    # those configured for the overall analysis.
    if set(settings) & {'limits', 'total_seconds', 'exponents'}:
        raise AnalysisError('Set global budgets in solve options, and exponents in their own section')
    try:
        cauchy = CauchyOptions(exponents=exponents,
            limits=EncodingLimits(options.max_products, options.max_psd_dimension, options.max_decisions), **settings)
    except TypeError as error:
        raise AnalysisError(f'Invalid Cauchy configuration: {error}') from error
    cauchy.validate()
    return data, cauchy


def _bound_value(candidate, n, *, clipped=True):
    value = rational(candidate['prefactor_upper'])*rational(candidate['decay_upper'])**n
    return min(sp.Integer(1), value) if clipped else value


def _exact_text(value):
    # Decimal(int) avoids Python's decimal-string digit limit without changing
    # process-wide security settings. Selection and replay still use rationals.
    value = rational(value)
    numerator = format(Decimal(int(value.p)), 'f')
    return numerator if value.q == 1 else numerator+'/'+format(Decimal(int(value.q)), 'f')


def compare_candidates(candidates, n, *, include_reciprocal=True):
    if type(n) is not int or not 0 <= n <= 10000:
        raise AnalysisError('Comparison n must be an integer in [0,10000]')
    positive = [c for c in candidates if c['method'] != 'reciprocal']
    groups = {
        'integer': [c for c in positive if rational(c['k']).q == 1],
        'rational': list(positive),
        'noninteger': [c for c in positive if rational(c['k']).q != 1],
        'direct_polynomial': [c for c in candidates if c['method'] == 'direct_polynomial'],
        'cauchy_integer': [c for c in candidates if c['method'].startswith('cauchy') and rational(c['k']).q == 1],
    }
    if include_reciprocal:
        groups.update(reciprocal=[c for c in candidates if c['method']=='reciprocal'],
                      overall=list(candidates))
    result = {'n': n}
    for name, group in groups.items():
        if not group:
            result[name] = None
            continue
        # A Jensen power is globally dominated by its parent after clipping.
        # Keep it for the noninteger comparison, but never replace a parent
        # merely because both bounds clip to one at a small horizon.
        identifiers = {c['id'] for c in group}
        selectable = [c for c in group if not (c['method']=='positive_jensen'
                      and c['reference']['seed'] in identifiers)]
        best = min(selectable, key=lambda c: (_bound_value(c, n, clipped=False), c['id']))
        value = _bound_value(best, n)
        result[name] = {**best, 'upper_bound_exact': _exact_text(value), 'upper_bound_numeric': float(value)}
    integer, rational_best = result['integer'], result['rational']
    if integer is not None and rational_best is not None:
        old, new = _bound_value(integer,n), _bound_value(rational_best,n)
        result['rational_no_worse'] = bool(new <= old)
        result['integer_over_rational_exact'] = _exact_text(old/new) if new else ('1' if old == 0 else None)
        result['strict_improvement'] = bool(new < old)
    result['numeric_is_display_only'] = True
    return result


def comparison_markdown(workflow):
    lines = ['# 整数与有理数指数尾界比较', '',
        '以下最优指本次实际搜索并通过精确验证的候选中的最优，不代表全局最优。',
        '事件为 K>n，K 计完整循环轮数；表中浮点数仅作展示，精确值保存在 comparisons.json。',
        '有理数集合包含整数；另列非整数候选，避免把整数结果误称为非整数改进。', '',
        '| n | 直接多项式界 (k=1) | 最佳整数 k | 整数界 | 最佳有理数 k | 有理数界 | 整数界/有理数界 |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for row in workflow['comparisons']:
        def number(name):
            return f"{row[name]['upper_bound_numeric']:.12g}" if row[name] else '未找到'
        def exponent(name):
            return row[name]['k'] if row[name] else '—'
        ratio = (f"{float(_bound_value(row['integer'],row['n'])/_bound_value(row['rational'],row['n'])):.8g}"
                 if row['integer'] and row['rational'] and _bound_value(row['rational'],row['n']) else '—')
        lines.append(f"| {row['n']} | {number('direct_polynomial')} | {exponent('integer')} | "
                     f"{number('integer')} | {exponent('rational')} | {number('rational')} | {ratio} |")
    lines += ['', '每份候选的形式是 `min(1, C * rho**n)`，均对所有非负整数 n 有效。', '']
    for row in workflow['comparisons']:
        lines.append(f"## 在 n={row['n']} 选择的证书")
        lines.append('')
        for category in ('integer','rational','noninteger'):
            c = row[category]
            if c is None:
                lines.append(f'- {category}：本次搜索未找到证书。')
                continue
            lines += [f"- {category}: k={c['k']}, method={c['method']}, id={c['id']}",
                      f"  - 精确前因子 C = {c['prefactor_upper']}",
                      f"  - 精确收缩上界 rho = {c['decay_upper']}",
                      f"  - eta = {c['eta']}"]
        lines.append('')
    if workflow.get('schema_version',1) >= 2:
        lines += ['## 正幂与倒数路线', '', '| n | 正整数幂 | 正非整数幂 | 倒数幂 | 合并最优 |',
                  '|---|---:|---:|---:|---:|']
        for row in workflow['comparisons']:
            values = [f"{row[key]['upper_bound_numeric']:.12g}" if row[key] else '未找到'
                      for key in ('integer','noninteger','reciprocal','overall')]
            lines.append('| '+str(row['n'])+' | '+' | '.join(values)+' |')
    return '\n'.join(lines)+'\n'


def _normalize(method, eta, C, rho, k, reference, *, identifier, t=None):
    C, rho, k = rational(C), rational(rho), rational(k)
    if C < 0 or not 0 <= rho < 1 or k <= 0:
        raise AnalysisError('Invalid portfolio bound')
    result = {'id':identifier, 'method':method, 'eta':str(eta), 'k':str(k),
        'prefactor_upper':str(C), 'decay_upper':str(rho), 'reference':reference,
        'event':'K > n', 'time_unit':'completed_loop_iterations',
        'expression':f'min(1, ({C})*({rho})**n)'}
    if t is not None:
        result['t'] = str(t)
    return result


def verify_direct_candidate(root, bound, cfg, evidence, kernel, options):
    """Rebuild the old symbolic obligations and verify their exact certificate."""
    from contractive_tool.positivity.registry import StrategyRegistry
    from contractive_tool.positivity.selector import build_plan
    from contractive_tool.analysis.semantics import prove_nonnegative
    path = Path(root)/bound['certificate']
    certificate, checked = _json(path), _json(path.with_name('verification.json'))
    if checked['status'] != 'proved' or certificate['bound'] != bound:
        raise AnalysisError('Direct certificate/bound mismatch')
    problem = make_symbolic_round_problem(cfg, kernel, bound['degree'], rational(bound['c']), options.max_decisions,
                                          template_variables=options.tail_variables)
    if _canonical(problem.to_data()) != _json(path.parent.parent.parent/'polynomial_problem.json'):
        raise AnalysisError('Direct polynomial problem differs from source replay')
    values = {sp.Symbol(n):rational(v) for n,v in checked['exact_values'].items()}
    if checked['method'] == 'exact_original_domain_farkas':
        if set(checked['exact_values']) != set(problem.decisions):
            raise AnalysisError('Direct template values missing')
        if any(prove_nonnegative(o.domain, sp.expand(o.conclusion.xreplace(values))) is None
               for o in problem.obligations):
            raise AnalysisError('Direct original-domain proof failed')
    else:
        plan = _json(path.with_name('encoding_plan.json'))
        order = plan['choices'][0]['order']
        model, rebuilt_plan = build_plan(problem.obligations, problem.decisions, problem.objective,
            StrategyRegistry(options.enabled_strategies), plan['requested_strategy'], order, 2*order,
            EncodingLimits(options.max_products,options.max_psd_dimension,options.max_decisions),
            fallback=options.strategy=='auto')
        if (_canonical(model.to_data()) != _json(path.with_name('conic_model.json'))
                or rebuilt_plan['choices'] != plan['choices']
                or not check_conic_values(model, checked['exact_values'])):
            raise AnalysisError('Direct conic certificate failed exact source replay')
    concrete = {name:sp.expand(p.xreplace(values)) for name,p in problem.expressions.items()}
    if {name:str(p) for name,p in concrete.items()} != certificate['polynomials']:
        raise AnalysisError('Direct polynomial values disagree')
    A = problem.objective.xreplace(values)
    if A != rational(bound['A_exact']) or A != rational(checked['bound_exact']) or A < 0:
        raise AnalysisError('Direct initial objective differs')
    if bound['event'] != 'K > n' or bound['time_unit'] != 'completed_loop_iterations':
        raise AnalysisError('Cannot compare bounds with different events/clocks')
    return concrete[kernel.header]


def _template(round_, seed, degree, config, limit, template_variables=None):
    variables = tuple(map(sp.Symbol, select_variables(round_.variables, template_variables)))
    omitted = set(round_.variables)-set(variables)
    if 'template' in config:
        data = config['template']
        coefficients = tuple(map(sp.Symbol, data['coefficients']))
        expression = parse_expression(data['expression'],round_.variables+coefficients)
        if expression.free_symbols & omitted:
            raise AnalysisError('Explicit Cauchy template uses an excluded tail variable')
        return EtaTemplate(expression,coefficients,
            tuple(parse_expression(e,coefficients) for e in data.get('nonnegative',())),
            tuple(parse_expression(e,coefficients) for e in data.get('equalities',())))
    if seed is not None:
        if seed.free_symbols & omitted:
            raise AnalysisError('Cauchy seed uses an excluded tail variable')
        powers = (set(sp.Poly(seed,*variables).monoms()) if variables else {()}) | {(0,)*len(variables)}
        powers = sorted(powers,key=lambda p:(sum(p),p))
    else:
        if math.comb(len(variables)+degree,degree) > limit:
            raise AnalysisError('Joint template coefficient budget exceeded')
        powers = total_degree_exponents(len(variables),degree)
    prefix = '__workflow_eta'
    while any(str(v).startswith(prefix) for v in (*round_.variables,*round_.law.symbols)):
        prefix += '_'
    coefficients = tuple(sp.Symbol(f'{prefix}_{i}') for i in range(len(powers)))
    eta = sum(c*sp.prod(v**p for v,p in zip(variables,exponents))
              for c,exponents in zip(coefficients,powers))
    return EtaTemplate(eta,coefficients)


def _scaled_basis(round_, eta):
    """Diagonal second-moment scaling; exact rational, invertible on the basis.

For a Bernoulli(1/100) monomial r this yields 10*r, reproducing the
notes' physical Z basis without a program-name or parameter special case.
"""
    monomials = round_.resolve_basis(eta)
    basis = []
    for monomial in monomials:
        second = sum(p*monomial.subs(dict(zip(round_.law.symbols,atom)),simultaneous=True)**2
                     for atom,p in round_.law.atoms)
        scale = rational(power_enclosure(second,sp.Rational(1,2),12)['upper']) if second else 1
        basis.append(sp.expand(monomial/scale))
    return tuple(basis)


def _guided_grid(round_, template, basis, norm_bounds, config, options):
    resolved = round_.resolve_basis(template.expression,basis)
    base = (tuple(map(rational,config['t_values'])) if 't_values' in config
            else automatic_t_grid(round_.law.norm_atoms(resolved),options.exponents,
                                  min(8,options.max_t_points)))
    guided = []
    if config.get('guided_t',True):
        for old_basis,B in norm_bounds:
            if tuple(old_basis) != tuple(map(str,resolved)):
                continue  # A norm parameter cannot be transferred across bases.
            if B > 0:
                t = rational(power_enclosure(B,sp.Rational(1,2),8)['upper'])
                guided.extend((t,t*sp.Rational(33,32),t*sp.Rational(31,32)))
    # Reserve space for the coarse grid: a neighborhood alone is not a search
    # of the wider feasible interval. No unknown point changes an endpoint.
    base = tuple(dict.fromkeys(base))
    if len(base) > options.max_t_points:
        raise AnalysisError('Explicit t grid exceeds workflow parameter budget')
    guided = [t for t in dict.fromkeys(guided) if t not in base and t>0]
    guided = guided[:options.max_t_points-len(base)]
    return tuple(guided)+base


def _append_cauchy(portfolio, result, artifact, stage):
    if result['status'] != 'proved':
        return
    for index,c in enumerate(result['candidates']):
        portfolio.append(_normalize(stage,c['eta'],c['prefactor_upper'],c['decay_upper'],c['k'],
            {'artifact':artifact,'candidate':index},identifier=f'{stage}:{artifact}:{index}',t=c.get('t')))
    if result.get('special_case') in ('initially_exited','one_step_termination'):
        C = 0 if result['special_case']=='initially_exited' else 1
        portfolio.append(_normalize(stage,'0' if not C else result['attempts'][0]['eta'],C,0,1,
            {'artifact':artifact,'special_case':result['special_case']},identifier=f'{stage}:{artifact}:degenerate'))


def _append_jensen(portfolio, exponents):
    """Certified 0<k<1 powers of an existing killed contraction certificate.

    These are conservative derived candidates, not a successful Cauchy solve.
    They cannot improve their parent after clipping; keep them explicitly named.
    """
    seeds = [c for c in portfolio if c['method']=='direct_polynomial']
    for seed in seeds:
        for k in sorted(set(exponents.candidates())):
            if not 0 < k < 1:
                continue
            C = rational(power_enclosure(rational(seed['prefactor_upper']),k,12)['upper'])
            rho = rational(power_enclosure(rational(seed['decay_upper']),k,12)['upper'])
            if rho >= 1:
                continue
            portfolio.append(_normalize('positive_jensen',seed['eta'],C,rho,k,
                {'seed':seed['id'],'rule':'Jensen_on_killed_potential'},
                identifier=f'positive_jensen:{seed["id"]}:{k}'))


def reciprocal_options(options, config):
    from contractive_tool.analysis.reciprocal import ReciprocalOptions
    settings = dict(config.get('reciprocal', {}))
    owned = {'limits', 'total_seconds', 'variables'}
    if owned & settings.keys():
        raise AnalysisError('Reciprocal budgets/variables are owned by solve options')
    defaults = {'variables':options.tail_variables, 'total_seconds':max(.001,options.reciprocal_seconds),
        'solver_seconds':options.per_attempt_seconds, 'repair_seconds':options.repair_seconds,
        'repair_relative_gap':options.repair_relative_gap, 'repair_max_solves':options.repair_max_solves,
        'limits':EncodingLimits(options.max_products,options.max_psd_dimension,options.max_decisions)}
    try:
        result = ReciprocalOptions(**(defaults | settings))
    except TypeError as error:
        raise AnalysisError(f'Invalid reciprocal settings: {error}') from error
    result.validate()
    return result


def _append_reciprocal(portfolio, result, artifact):
    if result['status'] != 'proved':
        return
    for index,c in enumerate(result['candidates']):
        if c['event'] != 'K > n' or c['time_unit'] != 'completed_loop_iterations':
            raise AnalysisError('Reciprocal event/clock mismatch')
        portfolio.append(_normalize('reciprocal',c['eta'],c['prefactor_upper'],c['decay_upper'],c['k'],
            {'artifact':artifact,'candidate':index},identifier=f'reciprocal:{artifact}:{index}'))
    if result.get('special_case') == 'initially_exited':
        portfolio.append(_normalize('reciprocal','0',0,0,1,
            {'artifact':artifact,'special_case':'initially_exited'},identifier=f'reciprocal:{artifact}:degenerate'))


def _run_reciprocal_branch(source, root, stages, portfolio, options, local, evidence):
    from contractive_tool.analysis.reciprocal import search_reciprocal
    from contractive_tool.analysis.reciprocal_verification import verify_result as verify_reciprocal
    stage = {'stage':'reciprocal','budget_seconds':options.reciprocal_seconds,
             'budget_policy':'independent additional soft budget; not consumed by positive searches'}
    stages.append(stage)
    if not options.reciprocal_seconds:
        stage.update(status='skipped',reason='disabled')
        return
    started = time.monotonic()
    try:
        round_ = prepare_random_round(source, invariant_evidence=evidence.to_data())
    except AnalysisError as error:
        stage.update(status='unsupported',reason=str(error),elapsed_seconds=time.monotonic()-started)
        return
    path = root/'analyses/tailbound/workflow/reciprocal'
    try:
        result = search_reciprocal(round_,options=local)
        _write(path/'result.json',result)
        check = verify_reciprocal(round_,result) if result['status']=='proved' else {'status':'not_proved'}
        _write(path/'independent_check.json',check)
        if result['status']=='proved' and check['status']!='proved':
            raise AnalysisError('Reciprocal independent verification failed')
        artifact = str((path/'result.json').relative_to(root))
        stage.update(status=result['status'],artifact=artifact,candidates=len(result['candidates']))
        _append_reciprocal(portfolio,result,artifact)
    except (AnalysisError,ValueError,ImportError) as error:
        stage.update(status='unknown',reason=str(error))
    stage['elapsed_seconds'] = time.monotonic()-started


def run_symbolic_workflow(source, out_dir, options, cfg, evidence, kernel, polynomial_runner, *, started=None):
    started = time.monotonic() if started is None else started
    deadline = started+options.total_seconds
    config,cauchy_options = workflow_config(options)
    reciprocal_local = reciprocal_options(options,config)
    direct_options = replace(options, total_seconds=max(0.001, options.total_seconds*config.get('direct_fraction',0.5)))
    direct = polynomial_runner(source,'tailbound',out_dir,options=direct_options,_prepared=(cfg,evidence))
    root = Path(direct['out_dir'])
    workflow_root = root/'analyses/tailbound/workflow'
    _write(workflow_root/'polynomial_summary.json',direct)
    portfolio, stages, seeds = [], [], []
    stages.append({'stage':'direct_polynomial','status':direct['status'],
        'budget_seconds':direct_options.total_seconds,'elapsed_seconds':direct['elapsed_seconds'],
        'stop_reason':direct['stop_reason'],'artifact':'analyses/tailbound/workflow/polynomial_summary.json'})
    for index,bound in enumerate(direct['proved_candidates']):
        eta = verify_direct_candidate(root,bound,cfg,evidence,kernel,direct_options)
        candidate = _normalize('direct_polynomial',eta,bound['A_exact'],bound['c'],1,
            {'certificate':bound['certificate']},identifier=f'direct:{index}')
        portfolio.append(candidate)
    if portfolio:
        winners = []
        for n in options.comparison_ns:
            winner = min(portfolio,key=lambda c:_bound_value(c,n,clipped=False))
            if winner not in winners:
                winners.append(winner)
        if direct.get('selection'):
            incumbent = next(c for c in portfolio if c['reference']['certificate']==direct['selection']['certificate'])
            if incumbent not in winners:
                winners.append(incumbent)
        for winner in winners[:config.get('max_fixed_seeds',3)]:
            seeds.append((parse_expression(winner['eta'],kernel.variables),winner))

    route = 'incumbent_fixed_then_joint' if seeds else 'joint_without_polynomial_certificate'
    round_ = None
    basis = None
    if direct['stop_reason'] in ('solver_failed','missing_backend'):
        stages.append({'stage':'cauchy_prepare','status':'skipped','reason':'backend_unavailable'})
    elif time.monotonic() >= deadline:
        stages.append({'stage':'cauchy_prepare','status':'skipped','reason':'time_budget'})
    else:
        try:
            round_ = prepare_random_round(source, invariant_evidence=evidence.to_data())
            basis = tuple(parse_expression(b,round_.law.symbols) for b in config['basis']) if 'basis' in config else None
        except AnalysisError as error:
            round_ = None
            stages.append({'stage':'cauchy_prepare','status':'unsupported','reason':str(error)})
    norm_bounds = []
    if round_ is not None:
        fixed_deadline = time.monotonic()+max(0,deadline-time.monotonic())*0.35
        for index,(eta,winner) in enumerate(seeds):
            stage = {'stage':'cauchy_fixed','seed':winner['id'],'eta':str(eta)}
            stages.append(stage)
            remaining = fixed_deadline-time.monotonic()
            if remaining <= 0:
                stage.update(status='skipped',reason='fixed_stage_budget')
                continue
            path = workflow_root/f'fixed_{index:03d}'
            local = replace(cauchy_options,total_seconds=remaining/max(1,len(seeds)-index))
            try:
                resolved_basis = basis if basis is not None else _scaled_basis(round_,eta)
                result = search_fixed_eta(round_,eta,basis=resolved_basis,options=local,out_dir=path)
                check = verify_result(round_,result) if result['status']=='proved' else {'status':'not_proved'}
                _write(path/'independent_check.json',check)
                if result['status']=='proved' and check['status']!='proved':
                    raise AnalysisError('Fixed Cauchy independent verification failed')
                artifact = str((path/'result.json').relative_to(root))
                stage.update(status=result['status'],artifact=artifact,elapsed_seconds=result['elapsed_seconds'],
                             candidates=len(result['candidates']))
                _append_cauchy(portfolio,result,artifact,'cauchy_fixed')
                norm_bounds.extend((a['basis'],rational(a['B'])) for a in result['attempts'] if a['status']=='proved')
            except (AnalysisError,ValueError,ImportError) as error:
                stage.update(status='unknown',reason=str(error))
        if not seeds:
            stages.append({'stage':'cauchy_fixed','status':'skipped','reason':'no_polynomial_certificate'})

        # Seed supports are parameterized, not frozen. If there is no incumbent,
        # generate ordinary total-degree templates and escalate on failure.
        template_specs = [(eta,int(sp.Poly(eta,*round_.variables).total_degree())) for eta,_ in seeds]
        if not template_specs:
            template_specs = [(None,d) for d in range(max(1,options.initial_degree),options.max_degree+1,options.degree_step)]
        if 'template' in config:
            template_specs = template_specs[:1]
        seen_templates = set()
        for index,(seed,degree) in enumerate(template_specs):
            stage = {'stage':'cauchy_joint','degree':degree,'seed_eta':None if seed is None else str(seed)}
            if time.monotonic() >= deadline:
                stages.append({**stage,'status':'skipped','reason':'time_budget'})
                break
            try:
                template = _template(round_,seed,degree,config,options.max_decisions,options.tail_variables)
                if str(template.expression) in seen_templates:
                    continue
                seen_templates.add(str(template.expression))
                stages.append(stage)
                resolved_basis = basis if basis is not None else _scaled_basis(round_,template.expression)
                grid = _guided_grid(round_,template,resolved_basis,norm_bounds,config,cauchy_options)
                stage['t_values'] = list(map(str,grid))
                stage['template'] = str(template.expression)
                path = workflow_root/f'joint_{index:03d}'
                local = replace(cauchy_options,total_seconds=max(0.001,deadline-time.monotonic()))
                result = search_template_eta(round_,template,t_values=grid,basis=resolved_basis,options=local,out_dir=path)
                check = verify_result(round_,result) if result['status']=='proved' else {'status':'not_proved'}
                _write(path/'independent_check.json',check)
                if result['status']=='proved' and check['status']!='proved':
                    raise AnalysisError('Joint Cauchy independent verification failed')
                artifact = str((path/'result.json').relative_to(root))
                stage.update(status=result['status'],artifact=artifact,elapsed_seconds=result['elapsed_seconds'],
                             candidates=len(result['candidates']))
                _append_cauchy(portfolio,result,artifact,'cauchy_joint')
                if result['status']=='proved' and not seeds and not options.continue_after_success:
                    break
            except (AnalysisError,ValueError,ImportError) as error:
                if stage not in stages:
                    stages.append(stage)
                stage.update(status='unknown',reason=str(error))
    before_jensen = len(portfolio)
    _append_jensen(portfolio,cauchy_options.exponents)
    stages.append({'stage':'positive_jensen','status':'proved' if len(portfolio)>before_jensen else 'skipped',
        'candidates':len(portfolio)-before_jensen,
        'rule':'derived 0<k<1 powers of verified direct potentials; no new state solve'})
    _run_reciprocal_branch(source,root,stages,portfolio,options,reciprocal_local,evidence)
    summary = deepcopy(direct)
    summary['polynomial_selection'] = direct['selection']
    summary['symbolic_workflow'] = {
        'schema_version':2,'route':route,'config':config,'direct_options':asdict(direct_options),
        'stages':stages,'candidates':portfolio,
        'branch_budgets':{'positive_seconds':options.total_seconds,
            'reciprocal_seconds':options.reciprocal_seconds,
            'policy':'independent additive soft budgets; verification may exceed optimizer budgets'},
        'integer_exponent_interpretation':'Direct polynomial V is eta=V,k=1; degree is not k.',
        'rational_pool_includes_integers':True,
        'optimality':'best certified bound among searched candidates, separately for each n',
        'comparisons':[compare_candidates(portfolio,n) for n in options.comparison_ns]}
    if portfolio:
        best = summary['symbolic_workflow']['comparisons'][0]['overall']
        summary.update(status='proved',termination='proved_almost_sure')
        legacy = next((b for b in direct['proved_candidates']
                       if b['certificate']==best['reference'].get('certificate')), {})
        summary['selection'] = {**legacy,**best,'A_exact':best['prefactor_upper'],'c':best['decay_upper'],
            'kernel':'symbolic','rule':'round_survival','clock':kernel.to_data()['clock'],
            'n_domain':'nonnegative integers',
            'selection_n':options.comparison_ns[0],'selection_policy':'best at the first comparison n; evaluate reselects for each n'}
    summary['elapsed_seconds'] = time.monotonic()-started
    summary['analysis_workflow'] = 'positive_and_reciprocal_symbolic'
    _write(root/'summary.json',summary)
    _write(workflow_root/'comparisons.json',summary['symbolic_workflow']['comparisons'])
    (workflow_root/'comparison.md').write_text(comparison_markdown(summary['symbolic_workflow']))
    # Rebind the existing manifest to all new files, excluding its own hash.
    from contractive_tool.analysis_pipeline import digest
    manifest = _json(root/'manifest.json')
    manifest['options'] = asdict(options)
    manifest['artifacts'] = {str(p.relative_to(root)):digest(p) for p in sorted(root.rglob('*'))
                             if p.is_file() and p != root/'manifest.json'}
    _write(root/'manifest.json',manifest)
    return summary


def verify_workflow(root):
    """Standalone replay of both proof families and the integer/rational ranking."""
    try:
        from contractive_tool.analysis_pipeline import SearchOptions
        from contractive_tool.cfg.builder import build_cfg
        from contractive_tool.frontend.parser import parse_file
        from contractive_tool.frontend.semantic import check_program
        from contractive_tool.analysis.invariant_certification import prepare_certified_program
        from contractive_tool.analysis.symbolic_rounds import prepare_symbolic_round_kernel
        from hashlib import sha256
        root = Path(root)
        summary,manifest = _json(root/'summary.json'),_json(root/'manifest.json')
        if summary['status'] != 'proved':
            raise AnalysisError('No proved symbolic workflow')
        source = Path(manifest['source'])
        if sha256(source.read_bytes()).hexdigest() != manifest['source_sha256']:
            raise AnalysisError('Source hash mismatch')
        workflow = summary['symbolic_workflow']
        cfg = build_cfg(check_program(parse_file(source)))
        evidence = prepare_certified_program(cfg, saved_evidence=_json(root/'analyses/tailbound/domain_evidence.json'))
        kernel = prepare_symbolic_round_kernel(cfg,evidence)
        options = SearchOptions(**workflow['direct_options'])
        options.validate()
        if options.tail_variables != manifest['options'].get('tail_variables'):
            raise AnalysisError('Tail variable selection differs from run options')
        direct = _json(root/'analyses/tailbound/workflow/polynomial_summary.json')
        rebuilt = []
        for index,bound in enumerate(direct['proved_candidates']):
            eta = verify_direct_candidate(root,bound,cfg,evidence,kernel,options)
            rebuilt.append(_normalize('direct_polynomial',eta,bound['A_exact'],bound['c'],1,
                {'certificate':bound['certificate']},identifier=f'direct:{index}'))
        round_ = None
        for stage in workflow['stages']:
            if stage['stage']=='positive_jensen':
                # Replay saved exponent configuration; the original config file
                # need not exist, and no external seeds are loaded.
                exponent_config = workflow['config'].get('exponents',{})
                exponents = ExponentOptions(**({'interval':('1/4','4'),'coarse_points':16,
                    'refinements':1} | exponent_config))
                _append_jensen(rebuilt,exponents)
                continue
            if stage['stage']=='reciprocal' and stage['status']=='proved':
                from contractive_tool.analysis.reciprocal_verification import verify_result as verify_reciprocal
                from contractive_tool.analysis.reciprocal import polynomial_template
                if round_ is None:
                    round_ = prepare_random_round(source, invariant_evidence=evidence.to_data())
                result = _json(root/stage['artifact'])
                requested = SearchOptions(**manifest['options'])
                local = reciprocal_options(requested,workflow['config'])
                template = polynomial_template(round_,local)
                if (not requested.reciprocal_seconds or result['options'] != _canonical(asdict(local))
                        or result['input'] != {'eta':str(template.expression),
                            'coefficients':list(map(str,template.coefficients))}):
                    raise AnalysisError('Reciprocal search settings/template differ from workflow')
                if verify_reciprocal(round_,result)['status']!='proved':
                    raise AnalysisError('Reciprocal artifact failed source replay')
                _append_reciprocal(rebuilt,result,stage['artifact'])
                continue
            if stage['stage'] not in ('cauchy_fixed','cauchy_joint') or stage['status']!='proved':
                continue
            if round_ is None:
                round_ = prepare_random_round(source, invariant_evidence=evidence.to_data())
            result = _json(root/stage['artifact'])
            if verify_result(round_,result)['status']!='proved':
                raise AnalysisError('Cauchy artifact failed source replay')
            if stage['stage']=='cauchy_fixed':
                seed = next(c for c in rebuilt if c['id']==stage['seed'])
                if seed['method']!='direct_polynomial' or result['input']['eta']!=seed['eta']:
                    raise AnalysisError('Fixed eta was not supplied by the direct phase')
            _append_cauchy(rebuilt,result,stage['artifact'],stage['stage'])
        if rebuilt != workflow['candidates']:
            raise AnalysisError('Portfolio differs from verified certificates')
        allowed = set(map(sp.Symbol, select_variables(kernel.variables, options.tail_variables)))
        if any(parse_expression(c['eta'],kernel.variables).free_symbols - allowed for c in rebuilt):
            raise AnalysisError('Portfolio uses an excluded tail variable')
        if [row['n'] for row in workflow['comparisons']] != manifest['options']['comparison_ns']:
            raise AnalysisError('Comparison horizons differ from run options')
        extended = workflow.get('schema_version',1) >= 2
        for row in workflow['comparisons']:
            if compare_candidates(rebuilt,row['n'],include_reciprocal=extended) != row:
                raise AnalysisError('Integer/rational comparison mismatch')
        best = workflow['comparisons'][0]['overall' if extended else 'rational']
        if best is None or any(summary['selection'].get(key) != value for key,value in best.items()):
            raise AnalysisError('Selected bound differs from verified ranking')
        return {'status':'proved','direct_certificates':len(direct['proved_candidates']),
                'portfolio_candidates':len(rebuilt),'comparisons_checked':len(workflow['comparisons']),
                'method':('source_replay_positive_and_reciprocal_exact_comparison' if extended
                          else 'source_replay_both_families_exact_comparison')}
    except (AnalysisError,KeyError,ValueError,TypeError,OSError,StopIteration) as error:
        return {'status':'verification_failed','reason':str(error)}
