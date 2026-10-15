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
                      'max_parameter_points','max_c_steps','max_products','max_psd_dimension','max_decisions'):
            command.add_argument('--'+field.replace('_','-'), type=int, default=getattr(defaults,field))
        for field in ('total_seconds','per_attempt_seconds'):
            command.add_argument('--'+field.replace('_','-'), type=float, default=getattr(defaults,field))
        command.add_argument('--c-values', nargs='+', default=None,
                             help='explicit grid override for reproducing previous runs; default is bisection')
        command.add_argument('--continue-after-success', action='store_true')
        command.add_argument('--strategy', choices=('auto','putinar','schmudgen','handelman'), default='auto')
        command.add_argument('--enabled-strategies', nargs='+', choices=('putinar','schmudgen','handelman'),
                             default=list(defaults.enabled_strategies))
        command.add_argument('--family', choices=('polynomial','fractional_power'), default='polynomial')
        command.add_argument('--tail-rule', choices=('auto','round_survival','late_bad_exit'), default='auto',
                             help='auto tries Boolean then symbolic round kernels, then late_bad_exit with diagnostics')
    strategies = commands.add_parser('strategies', help='query optional positivity plugins')
    strategies.add_argument('operation', choices=('list',))
    strategies.add_argument('--json', action='store_true')
    evaluate = commands.add_parser('evaluate', help='evaluate an already proved uniform bound; no new solve')
    evaluate.add_argument('artifacts', type=Path)
    evaluate.add_argument('--n', type=int, required=True)
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        if args.command == 'strategies':
            from contractive_tool.positivity.registry import StrategyRegistry
            result = StrategyRegistry().snapshot()
        elif args.command == 'evaluate':
            if not 0 <= args.n <= 10000:
                raise AnalysisError('n must be an integer in [0,10000] for numeric evaluation')
            summary = json.loads((args.artifacts/'summary.json').read_text())
            if summary.get('status') != 'proved' or not summary.get('selection'):
                raise AnalysisError('Artifact has no proved uniform bound')
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
            for field in ('c_values','enabled_strategies'):
                if fields[field] is not None:
                    fields[field] = tuple(fields[field])
            result = run_analysis(args.source,args.goal,args.out_dir,options=SearchOptions(**fields),
                                  model_only=args.command!='solve')
        print(json.dumps(result,sort_keys=True))
        return 3 if result.get('status') in {'solver_failed','unsupported'} else 0
    except (AnalysisError,FrontendError,OSError,ValueError,KeyError) as error:
        print(str(error),file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
