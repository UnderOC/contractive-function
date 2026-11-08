"""Standalone reciprocal tail analysis; deliberately absent from main dispatch."""
import argparse
import json
from pathlib import Path

from contractive_tool.analysis.cauchy_expressions import parse_expression
from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.analysis.reciprocal import ReciprocalOptions, evaluate, search_reciprocal
from contractive_tool.analysis.reciprocal_verification import verify_result
from contractive_tool.errors import AnalysisError, FrontendError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    run = commands.add_parser('run')
    run.add_argument('source', type=Path)
    run.add_argument('--out-dir', type=Path, required=True)
    run.add_argument('--eta', help='Optional fixed polynomial denominator; otherwise synthesize coefficients')
    run.add_argument('--degree', type=int, default=1)
    run.add_argument('--variables', nargs='+')
    run.add_argument('--growth-values', nargs='+', default=list(ReciprocalOptions().growth_values))
    run.add_argument('--support-values', nargs='+', default=['1/2'])
    run.add_argument('--moment-values', nargs='+', default=[], help='Fixed D seeds for matrix synthesis')
    run.add_argument('--matrix-degree', type=int, default=0)
    run.add_argument('--k-values', nargs='+', default=list(ReciprocalOptions().k_values))
    run.add_argument('--no-adaptive-k', action='store_true')
    run.add_argument('--k-upper', default='8')
    run.add_argument('--target-ns', nargs='+', type=int, default=[20, 100, 1000])
    run.add_argument('--feedback-points', type=int, default=12)
    run.add_argument('--feedback-seconds', type=float, default=60)
    run.add_argument('--feedback-step', default='1/4')
    run.add_argument('--epsilon', default='1/1000')
    run.add_argument('--scalar-strategy', choices=['constant_sos', 'sos'], default='constant_sos')
    run.add_argument('--scalar-order', type=int, default=2)
    run.add_argument('--total-seconds', type=float, default=120)
    run.add_argument('--solver-seconds', type=float, default=30)
    for name in ('verify', 'evaluate'):
        command = commands.add_parser(name)
        command.add_argument('artifact', type=Path)
        if name == 'evaluate':
            command.add_argument('--n', type=int, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'run':
            if args.out_dir.exists() and (not args.out_dir.is_dir() or any(args.out_dir.iterdir())):
                raise AnalysisError('Use a new or empty output directory')
            options = ReciprocalOptions(degree=args.degree, variables=args.variables,
                growth_values=args.growth_values, support_values=args.support_values, k_values=args.k_values,
                moment_values=args.moment_values, matrix_multiplier_degree=args.matrix_degree,
                adaptive_k=not args.no_adaptive_k, k_upper=args.k_upper, target_ns=args.target_ns,
                feedback_points=args.feedback_points, feedback_seconds=args.feedback_seconds,
                feedback_step=args.feedback_step,
                epsilon=args.epsilon, scalar_strategy=args.scalar_strategy, scalar_order=args.scalar_order,
                total_seconds=args.total_seconds, solver_seconds=args.solver_seconds)
            options.validate()
            try:
                round_ = prepare_random_round(args.source)
            except AnalysisError as error:
                result = {'status': 'unsupported', 'reason': str(error), 'source': str(args.source.resolve())}
            else:
                eta = None if args.eta is None else parse_expression(args.eta, round_.variables)
                result = search_reciprocal(round_, eta=eta, options=options)
                if result['status'] == 'proved':
                    checked = verify_result(round_, result)
                    if checked['status'] != 'proved':
                        raise AnalysisError(f'Internal replay failed: {checked}')
                    result['independent_check'] = checked
            args.out_dir.mkdir(parents=True, exist_ok=True)
            (args.out_dir/'result.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
            summary = {k: result[k] for k in ('status', 'reason', 'elapsed_seconds', 'independent_check') if k in result}
            summary['artifact'] = str(args.out_dir/'result.json')
            summary['candidates'] = len(result.get('candidates', []))
            print(json.dumps(summary))
            return 0 if result['status'] == 'proved' else 3
        path = args.artifact/'result.json' if args.artifact.is_dir() else args.artifact
        result = json.loads(path.read_text())
        if result['status'] != 'proved':
            print(json.dumps({'status': 'not_proved', 'reason': result['status']}))
            return 3
        round_ = prepare_random_round(result['round']['evidence']['source'])
        checked = verify_result(round_, result)
        if checked['status'] != 'proved':
            print(json.dumps(checked))
            return 3
        print(json.dumps(checked if args.command == 'verify' else evaluate(result, args.n)))
        return 0
    except (AnalysisError, FrontendError, OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({'status': 'error', 'reason': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
