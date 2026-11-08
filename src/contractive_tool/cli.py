from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import sympy as sp

from contractive_tool.analysis_pipeline import SearchOptions, run_analysis
from contractive_tool.errors import AnalysisError, FrontendError
from contractive_tool.frontend.ast import ast_to_data
from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.semantic import check_program
from contractive_tool.pipeline import compile_to_cfg


def _parser():
    parser = argparse.ArgumentParser(prog='contractive')
    commands = parser.add_subparsers(dest='command', required=True)
    parse = commands.add_parser('parse', help='parse and check a source program')
    parse.add_argument('source', type=Path)
    parse.add_argument('--out', type=Path, required=True)
    cfg = commands.add_parser('cfg', help='emit the grouped pCFG')
    cfg.add_argument('source', type=Path)
    cfg.add_argument('--out-dir', type=Path)
    defaults = SearchOptions()
    for name in ('solve', 'analyze', 'build-model'):
        command = commands.add_parser(name, help='search uniform polynomial certificates' if name=='solve'
                                      else 'generate polynomial obligations/conic model without solving')
        command.add_argument('source', type=Path)
        command.add_argument('--goal', choices=('tailbound','assertion_violation'), required=True)
        command.add_argument('--out-dir', type=Path)
        for field in ('initial_degree','max_degree','degree_step','max_order','max_attempts_per_point',
                      'max_parameter_points','max_c_steps','max_products','max_psd_dimension','max_decisions',
                      'repair_max_solves'):
            command.add_argument('--'+field.replace('_','-'), type=int, default=getattr(defaults,field))
        for field in ('total_seconds','per_attempt_seconds','repair_seconds','repair_relative_gap'):
            command.add_argument('--'+field.replace('_','-'), type=float, default=getattr(defaults,field),
                                 help='positive search soft budget; reciprocal budget is additional'
                                      if field=='total_seconds' else None)
        command.add_argument('--c-values', nargs='+', default=None,
                             help='explicit c grid; defaults: tail bisection, assertion near-one grid')
        command.add_argument('--assertion-margin', default=defaults.assertion_margin,
                             help='positive rational lower bound for raw assertion eta (H=1)')
        command.add_argument('--assertion-variables', nargs='+', default=None,
                             help='restrict assertion templates to these program variables; default: all')
        command.add_argument('--tail-variables', nargs='+', default=None,
                             help='restrict tailbound templates to these program variables; default: all')
        command.add_argument('--continue-after-success', action='store_true')
        command.add_argument('--strategy', choices=('auto','putinar','schmudgen','handelman'), default='auto')
        command.add_argument('--enabled-strategies', nargs='+', choices=('putinar','schmudgen','handelman'),
                             default=list(defaults.enabled_strategies))
        command.add_argument('--family', choices=('polynomial','fractional_power'), default='polynomial')
        command.add_argument('--tail-rule', choices=('auto','round_survival','late_bad_exit'), default='auto',
                             help='auto tries Boolean then symbolic round kernels, then late_bad_exit with diagnostics')
        command.add_argument('--symbolic-workflow', action=argparse.BooleanOptionalAction, default=True,
                             help='run positive-power and independently budgeted reciprocal searches on symbolic rounds')
        command.add_argument('--reciprocal-seconds', type=float, default=defaults.reciprocal_seconds,
                             help='additional independent reciprocal soft budget on symbolic rounds; 0 disables')
        command.add_argument('--workflow-config', type=str,
                             help='optional positive/reciprocal workflow settings JSON; no fixed eta seed input')
        command.add_argument('--comparison-n', dest='comparison_ns', type=int, nargs='+', default=[5,20,100],
                             help='round counts for positive integer/noninteger and reciprocal comparisons')
    strategies = commands.add_parser('strategies', help='query optional positivity plugins')
    strategies.add_argument('operation', choices=('list',))
    strategies.add_argument('--json', action='store_true')
    evaluate = commands.add_parser('evaluate', help='evaluate an already proved uniform bound; no new solve')
    evaluate.add_argument('artifacts', type=Path)
    evaluate.add_argument('--n', type=int)
    evaluate.add_argument('--event', choices=('eventual','late_failure','point_failure'), default='eventual')
    evaluate.add_argument('--clock', choices=('after_initialization','program_entry'), default='after_initialization')
    verify = commands.add_parser('verify', help='independently replay assertion or symbolic tail certificates without solving')
    verify.add_argument('artifacts', type=Path)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        if args.command == 'strategies':
            from contractive_tool.positivity.registry import StrategyRegistry
            result = StrategyRegistry().snapshot()
        elif args.command == 'verify':
            summary = json.loads((args.artifacts/'summary.json').read_text())
            if summary.get('goal') == 'assertion_violation':
                from contractive_tool.assertion_pipeline import verify_assertion
                result = verify_assertion(args.artifacts)
            else:
                from contractive_tool.analysis.symbolic_workflow import verify_workflow
                result = verify_workflow(args.artifacts)
        elif args.command == 'evaluate':
            if args.n is not None and not 0 <= args.n <= 10000:
                raise AnalysisError('n must be an integer in [0,10000] for numeric evaluation')
            summary = json.loads((args.artifacts/'summary.json').read_text())
            if summary.get('status') != 'proved' or not summary.get('selection'):
                raise AnalysisError('Artifact has no proved uniform bound')
            if summary.get('goal') != 'assertion_violation' and args.n is None:
                raise AnalysisError('Tail evaluation requires --n')
            if summary.get('goal') == 'assertion_violation':
                from contractive_tool.assertion_pipeline import evaluate_assertion
                result = evaluate_assertion(args.artifacts, event=args.event, n=args.n, clock=args.clock)
            elif 'symbolic_workflow' in summary:
                from contractive_tool.analysis.symbolic_workflow import compare_candidates, verify_workflow
                checked = verify_workflow(args.artifacts)
                if checked['status'] != 'proved':
                    raise AnalysisError(f"Workflow verification failed: {checked.get('reason')}")
                extended = summary['symbolic_workflow'].get('schema_version',1) >= 2
                comparison = compare_candidates(summary['symbolic_workflow']['candidates'],args.n,
                                                include_reciprocal=extended)
                best = comparison['overall' if extended else 'rational']
                result = {'status':'proved','n':args.n,'upper_bound_exact':best['upper_bound_exact'],
                          'upper_bound_numeric':best['upper_bound_numeric'],'expression':best['expression'],
                          'numeric_is_display_only':True,'event':best['event'],'time_unit':best['time_unit'],
                          'comparison':comparison}
            else:
                bound = summary['selection']
                value = sp.Rational(bound['A_exact']) * sp.Rational(bound['c'])**args.n
                result = {'status':'proved','n':args.n,'upper_bound_exact':str(min(sp.Integer(1),value)),
                          'upper_bound_numeric':float(min(sp.Integer(1),value)),
                          'numeric_is_display_only':True,'expression':bound['expression'], 'event':bound['event'],
                          'time_unit':bound['time_unit']}
        elif args.command == 'parse':
            checked = check_program(parse_file(args.source))
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps(ast_to_data(checked.ast),indent=2,sort_keys=True)+'\n')
            result = {'status':'ok','ast':str(args.out.resolve())}
        elif args.command == 'cfg':
            result = {'status':'ok',**compile_to_cfg(args.source,args.out_dir or Path('generated')/args.source.stem)}
        else:
            fields = {field:getattr(args,field) for field in SearchOptions.__dataclass_fields__ if hasattr(args,field)}
            for field in ('c_values','enabled_strategies','comparison_ns','assertion_variables','tail_variables'):
                if fields[field] is not None:
                    fields[field] = tuple(fields[field])
            result = run_analysis(args.source,args.goal,args.out_dir,options=SearchOptions(**fields),
                                  model_only=args.command!='solve')
        print(json.dumps(result,sort_keys=True))
        return 3 if result.get('status') in {'solver_failed','unsupported','verification_failed'} else 0
    except (AnalysisError,FrontendError,OSError,ValueError,KeyError) as error:
        print(str(error),file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
