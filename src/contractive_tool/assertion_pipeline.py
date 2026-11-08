"""Independent assertion search using shared polynomial/conic infrastructure.

No round-survival transformation, tail workflow, or exponent search is used.
"""
from dataclasses import asdict
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
import json
import time

import sympy as sp

from contractive_tool import __version__
from contractive_tool.analysis.assertion import make_assertion_problem, assertion_bound, evaluate_bound
from contractive_tool.analysis.semantics import prepare_program, prove_nonnegative
from contractive_tool.backends.cvxpy.builder import build
from contractive_tool.backends.cvxpy.certification import certify_candidate
from contractive_tool.cfg.builder import build_cfg
from contractive_tool.errors import AnalysisError
from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.semantic import check_program
from contractive_tool.pipeline import compile_to_cfg
from contractive_tool.positivity.base import EncodingLimits
from contractive_tool.positivity.registry import StrategyRegistry
from contractive_tool.positivity.selector import build_plan


def _key(bound):
    return sp.Rational(bound['upper_bound_exact']), sp.Rational(bound['A_exact']), sp.Rational(bound['c'])


def run_assertion_analysis(source, out_dir=None, *, options, model_only=False):
    from contractive_tool.analysis_pipeline import write_json, digest
    policy, explicit_cs = options.validate()
    margin = sp.Rational(options.assertion_margin)
    if not 0 < margin <= 1:
        raise AnalysisError('Assertion positivity margin must lie in (0,1]')
    # Fixed points near 1 target the initial probability, not minimum c.
    cs = explicit_cs or tuple(1-sp.Rational(1, 2**(i+6)) for i in range(options.max_c_steps))
    source = Path(source).resolve()
    if out_dir is None:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
        out_dir = Path('generated')/f'{source.stem}_assertion_violation_{stamp}'
    out_dir = Path(out_dir).resolve()
    if out_dir.exists() and any(out_dir.iterdir()):
        raise AnalysisError('Use a new or empty output directory')
    started = time.monotonic()
    deadline = started+options.total_seconds
    compile_to_cfg(source, out_dir/'shared')
    (out_dir/'shared/source.pp').write_bytes(source.read_bytes())
    root = out_dir/'analyses/assertion_violation'
    summary = {'schema_version': 1, 'goal': 'assertion_violation', 'rule': 'positive_first_moment',
        'status': 'unknown', 'selection': None, 'proved_candidates': [], 'degrees_attempted': [],
        'parameter_points': 0, 'attempt_count': 0, 'out_dir': str(out_dir),
        'termination': 'unknown', 'termination_assumed': False,
        'parameter_search': {'method': 'explicit_grid' if explicit_cs else 'near_one_grid',
                             'values': list(map(str, cs)), 'objective': 'minimum_verified_initial_expectation'}}
    history = []

    def finish():
        candidates = summary['proved_candidates']
        if candidates:
            summary['status'] = 'proved'
            summary['selection'] = min(candidates, key=_key)
            summary['nontrivial'] = bool(sp.Rational(summary['selection']['upper_bound_exact']) < 1)
            summary['pareto_candidates'] = [b for b in candidates if not any(
                sp.Rational(a['A_exact']) <= sp.Rational(b['A_exact']) and
                sp.Rational(a['c']) <= sp.Rational(b['c']) and
                (a['A_exact'], a['c']) != (b['A_exact'], b['c']) for a in candidates)]
        summary['elapsed_seconds'] = time.monotonic()-started
        write_json(root/'search_history.json', history)
        write_json(out_dir/'summary.json', summary)
        versions = {}
        for name in ('cvxpy', 'numpy', 'scipy', 'mosek'):
            try:
                versions[name] = metadata.version(name)
            except metadata.PackageNotFoundError:
                versions[name] = None
        write_json(out_dir/'manifest.json', {'tool_version': __version__, 'goal': 'assertion_violation',
            'source': str(source), 'source_sha256': digest(out_dir/'shared/source.pp'),
            'options': asdict(options), 'dependencies': versions, 'backend': 'cvxpy', 'solver': 'MOSEK',
            'mode': 'model_only' if model_only else 'solve',
            'budget_policy': 'cooperative symbolic/reconstruction deadline; MOSEK optimizer time limit',
            'artifacts': {str(p.relative_to(out_dir)): digest(p)
                          for p in sorted(out_dir.rglob('*')) if p.is_file()}})
        return summary

    try:
        cfg = build_cfg(check_program(parse_file(source)))
        if cfg.failure_terminal is None:
            raise AnalysisError('Source needs assert/refute to define the failure event')
        evidence = prepare_program(cfg)
    except AnalysisError as error:
        summary.update(status='unsupported', stop_reason='semantic_evidence_unavailable', diagnostic=str(error))
        return finish()
    write_json(root/'domain_evidence.json', evidence.to_data())
    write_json(root/'goal.json', {'goal': 'assertion_violation', 'rule': 'positive_first_moment',
        'event': 'tau_f < infinity', 'H': '1', 'k': '1', 'positivity_margin': str(margin),
        'failure_terminal': cfg.failure_terminal, 'normal_terminal': cfg.normal_terminal,
        'raw_terminal_values': {'normal': str(margin), 'failure': '1'},
        'theta_terminal_values': {'normal': '0', 'failure': '1'},
        'clock': 'pcfg_transition_after_initialization', 'prefix_steps': len(evidence.prefix),
        'termination_assumed': False, 'all_ordinary_transitions': True})
    registry = StrategyRegistry(options.enabled_strategies)
    limits = EncodingLimits(options.max_products, options.max_psd_dimension, options.max_decisions)
    stop = False
    for degree in policy.degrees():
        if time.monotonic() >= deadline:
            summary['stop_reason'] = 'time_budget'
            break
        summary['degrees_attempted'].append(degree)
        degree_candidates = []
        for ci, c in enumerate(cs):
            if time.monotonic() >= deadline or summary['parameter_points'] >= options.max_parameter_points:
                summary['stop_reason'] = ('time_budget' if time.monotonic() >= deadline else 'parameter_budget')
                stop = True
                break
            summary['parameter_points'] += 1
            point = root/'degrees'/str(degree)/f'c-{ci+1:03d}'
            try:
                problem = make_assertion_problem(cfg, evidence, degree, c, margin=margin,
                    max_decisions=options.max_decisions, template_variables=options.assertion_variables)
            except AnalysisError as error:
                history.append({'degree': degree, 'c': str(c), 'status': 'generation_failed', 'reason': str(error)})
                continue
            write_json(point/'polynomial_problem.json', problem.to_data())
            max_degree = max((int(sp.Poly(o.conclusion, *o.domain.variables).total_degree())
                              if o.domain.variables and o.conclusion != 0 else 0 for o in problem.obligations), default=0)
            attempts, plans = 0, set()
            point_proved = False
            minimum_order = max(1, (max_degree+1)//2)
            if minimum_order > options.max_order:
                history.append({'degree': degree, 'c': str(c), 'status': 'generation_failed',
                                'reason': 'Residual degree exceeds max_order'})
            for order in range(minimum_order, options.max_order+1):
                strategies = [options.strategy]+(list(registry.known) if options.strategy == 'auto' else [])
                for strategy in strategies:
                    if attempts >= options.max_attempts_per_point or point_proved or stop:
                        break
                    if time.monotonic() >= deadline:
                        summary['stop_reason'], stop = 'time_budget', True
                        break
                    row = {'degree': degree, 'c': str(c), 'order': order, 'strategy': strategy,
                           'status': 'generation_failed'}
                    try:
                        model, plan = build_plan(problem.obligations, problem.decisions, problem.objective,
                            registry, strategy, order, 2*order, limits, fallback=options.strategy == 'auto')
                        key = json.dumps(plan['choices'], sort_keys=True)
                        if key in plans:
                            continue
                        plans.add(key)
                        attempts += 1
                        summary['attempt_count'] += 1
                        attempt = point/'attempts'/f'{attempts:03d}'
                        row['path'] = str(attempt.relative_to(out_dir))
                        write_json(attempt/'encoding_plan.json', plan)
                        write_json(attempt/'conic_model.json', model.to_data())
                        built = build(model)
                        if model_only:
                            row['status'] = 'not_solved'
                            history.append(row)
                            summary.update(status='not_solved', stop_reason='model_only',
                                           model=str(attempt/'conic_model.json'))
                            return finish()
                        remaining = deadline-time.monotonic()
                        if remaining <= 0:
                            summary['stop_reason'], stop = 'time_budget', True
                            row['status'] = 'unknown'
                        else:
                            from contractive_tool.backends.cvxpy.mosek_solver import solve
                            solved = solve(built, time_limit=min(remaining, options.per_attempt_seconds),
                                           verbose=options.verbose)
                            (attempt/'solver.log').write_text(solved.pop('log'), encoding='utf-8')
                            write_json(attempt/'solver.json', solved)
                            row.update(status=solved['status'], raw_status=solved['raw_status'])
                            if solved.get('values') is not None:
                                # A low-denominator feasible reconstruction can have a much
                                # worse objective. Try finer rationals/repair before accepting it.
                                a = float(problem.objective.xreplace(
                                    {sp.Symbol(n): v for n, v in solved['values'].items()}))
                                cap = sp.Rational(str(a + max(1e-4, abs(a)*options.repair_relative_gap)))
                                verified, audit = certify_candidate(model, problem, solved['values'],
                                    options=options, deadline=deadline, bounded_reconstruction=True,
                                    reconstruction_objective_cap=cap)
                                if audit is not None:
                                    write_json(attempt/'repair.json', audit)
                                write_json(attempt/'verification.json', verified)
                                row['status'] = verified['status']
                                if verified['status'] == 'proved':
                                    bound = assertion_bound(problem, verified)
                                    bound['certificate'] = str((attempt/'certificate.json').relative_to(out_dir))
                                    sub = {sp.Symbol(n): sp.Rational(verified['exact_values'][n]) for n in problem.decisions}
                                    write_json(attempt/'certificate.json', {'bound': bound,
                                        'raw_polynomials': {loc: str(expr.xreplace(sub)) for loc, expr in problem.expressions.items()},
                                        'verification_method': verified['method'], 'context': problem.context,
                                        'encoding': {'strategy': strategy, 'order': order}})
                                    degree_candidates.append(bound)
                                    summary['proved_candidates'].append(bound)
                                    point_proved = True
                            if solved['status'] == 'solver_failed':
                                summary.update(stop_reason='solver_failed', diagnostic=solved.get('diagnostic'))
                                stop = True
                    except (AnalysisError, ImportError, ValueError) as error:
                        row['diagnostic'] = f'{type(error).__name__}: {error}'
                        if 'path' not in row:
                            attempts += 1
                        if isinstance(error, ImportError):
                            summary['stop_reason'], stop = 'missing_backend', True
                    history.append(row)
                if attempts >= options.max_attempts_per_point or point_proved or stop:
                    break
            if stop:
                break
        if stop:
            break
        if (not options.continue_after_success and any(
                sp.Rational(b['upper_bound_exact']) < 1 for b in degree_candidates)):
            summary['stop_reason'] = 'first_nontrivial_degree'
            break
    summary.setdefault('stop_reason', 'max_degree')
    summary['status'] = ('solver_failed' if summary['stop_reason'] in ('solver_failed', 'missing_backend')
                         else 'no_certificate_found')
    return finish()


def verify_assertion(artifacts):
    """Rebuild source obligations and the cone, then check rational witnesses."""
    from contractive_tool.analysis_pipeline import SearchOptions, digest
    from contractive_tool.backends.cvxpy.verification import check_conic_values
    root = Path(artifacts).resolve()

    def artifact(relative):
        path = (root/relative).resolve()
        if not path.is_relative_to(root):
            raise AnalysisError('Artifact path escapes result directory')
        return path

    def read(relative):
        return json.loads(artifact(relative).read_text())

    try:
        summary, manifest = read('summary.json'), read('manifest.json')
        if summary['status'] != 'proved' or summary['goal'] != 'assertion_violation':
            raise AnalysisError('No proved assertion result')
        if digest(artifact('shared/source.pp')) != manifest['source_sha256']:
            raise AnalysisError('Source digest mismatch')
        options = SearchOptions(**manifest['options'])
        options.validate()
        cfg = build_cfg(check_program(parse_file(artifact('shared/source.pp'))))
        evidence = prepare_program(cfg)
        limits = EncodingLimits(options.max_products, options.max_psd_dimension, options.max_decisions)
        registry = StrategyRegistry(options.enabled_strategies)
        candidates = summary['proved_candidates']
        if not candidates:
            raise AnalysisError('Missing assertion certificates')
        for candidate in candidates:
            cert_path = artifact(candidate['certificate'])
            cert = json.loads(cert_path.read_text())
            verified = json.loads(cert_path.with_name('verification.json').read_text())
            if verified['status'] != 'proved':
                raise AnalysisError('Missing exact verification')
            problem = make_assertion_problem(cfg, evidence, candidate['degree'], candidate['c'],
                margin=options.assertion_margin, max_decisions=options.max_decisions,
                template_variables=options.assertion_variables)
            encoding = cert['encoding']
            model, _ = build_plan(problem.obligations, problem.decisions, problem.objective,
                registry, encoding['strategy'], encoding['order'], 2*encoding['order'], limits,
                fallback=options.strategy == 'auto')
            if json.loads(json.dumps(model.to_data())) != json.loads(cert_path.with_name('conic_model.json').read_text()):
                raise AnalysisError('Rebuilt conic model differs from artifact')
            sub = {sp.Symbol(n): sp.Rational(verified['exact_values'][n]) for n in problem.decisions}
            if verified['method'] == 'exact_original_domain_farkas':
                if any(prove_nonnegative(o.domain, sp.expand(o.conclusion.xreplace(sub))) is None
                       for o in problem.obligations):
                    raise AnalysisError('Original-domain identity failed')
            elif not check_conic_values(model, verified['exact_values']):
                raise AnalysisError('Exact conic certificate failed')
            if problem.objective.xreplace(sub) != sp.Rational(verified['bound_exact']):
                raise AnalysisError('Initial objective mismatch')
            bound = assertion_bound(problem, verified)
            bound['certificate'] = candidate['certificate']
            if candidate != bound or cert['bound'] != bound or cert['context'] != problem.context:
                raise AnalysisError('Assertion bound metadata mismatch')
            if cert['raw_polynomials'] != {loc: str(expr.xreplace(sub)) for loc, expr in problem.expressions.items()}:
                raise AnalysisError('Raw polynomial mismatch')
        if summary['selection'] != min(candidates, key=_key):
            raise AnalysisError('Incorrect assertion selection')
        return {'status': 'proved', 'goal': 'assertion_violation', 'certificates': len(candidates),
                'method': 'source_replay_full_first_moment_exact_certificates'}
    except (OSError, KeyError, TypeError, ValueError, AnalysisError, sp.PolynomialError) as error:
        return {'status': 'verification_failed', 'reason': str(error)}


def evaluate_assertion(artifacts, *, event='eventual', n=None, clock='after_initialization'):
    checked = verify_assertion(artifacts)
    if checked['status'] != 'proved':
        raise AnalysisError(f"Assertion verification failed: {checked.get('reason')}")
    summary = json.loads((Path(artifacts)/'summary.json').read_text())
    results = [evaluate_bound(b, event, n, clock) for b in summary['proved_candidates']]
    return min(results, key=lambda b: sp.Rational(b['upper_bound_exact']))
