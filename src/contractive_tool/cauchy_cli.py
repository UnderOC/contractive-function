"""Standalone experimental Cauchy entry point; default CLI remains unchanged."""
import argparse
import json
from pathlib import Path

import sympy as sp

from contractive_tool.analysis.cauchy import (
    CauchyOptions, ExponentOptions, EtaTemplate, search_fixed_eta, search_template_eta, evaluate)
from contractive_tool.analysis.random_rounds import prepare_random_round
from contractive_tool.analysis.cauchy_verification import verify_result
from contractive_tool.analysis.cauchy_expressions import parse_expression
from contractive_tool.errors import AnalysisError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    run = commands.add_parser('run')
    run.add_argument('source', type=Path)
    run.add_argument('--config', type=Path, required=True)
    run.add_argument('--mode', choices=('fixed', 'template', 'both'), default='both')
    run.add_argument('--out-dir', type=Path, required=True)
    for name in ('verify', 'evaluate'):
        command = commands.add_parser(name)
        command.add_argument('artifact', type=Path, help='result.json or its containing directory')
        if name == 'evaluate':
            command.add_argument('--n', type=int, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'run':
            if args.out_dir.exists() and any(args.out_dir.iterdir()):
                raise AnalysisError('Use a new or empty output directory')
            config = json.loads(args.config.read_text())
            round_ = prepare_random_round(args.source)
            basis = tuple(parse_expression(b, round_.law.symbols) for b in config['basis']) if 'basis' in config else None
            exponents = ExponentOptions(**config.get('exponents', {}))
            options = CauchyOptions(exponents=exponents, **config.get('options', {}))
            summaries = {}
            for mode in ('fixed', 'template') if args.mode == 'both' else (args.mode,):
                path = args.out_dir/mode
                if mode == 'fixed':
                    result = search_fixed_eta(round_, parse_expression(config['fixed_eta'], round_.variables),
                                              basis=basis, options=options, out_dir=path)
                else:
                    data = config['template']
                    coefficients = tuple(map(sp.Symbol, data['coefficients']))
                    template = EtaTemplate(parse_expression(data['expression'], round_.variables+coefficients),
                        coefficients,
                        tuple(parse_expression(e, coefficients) for e in data.get('nonnegative', ())),
                        tuple(parse_expression(e, coefficients) for e in data.get('equalities', ())))
                    result = search_template_eta(round_, template, t_values=config.get('t_values'),
                                                 basis=basis, options=options, out_dir=path)
                checked = verify_result(round_, result) if result['status'] == 'proved' else {'status': 'not_proved'}
                (path/'independent_check.json').write_text(json.dumps(checked, indent=2)+'\n')
                summaries[mode] = {'status': result['status'], 'check': checked,
                                   'candidates': len(result['candidates']),
                                   'elapsed_seconds': result['elapsed_seconds'], 'artifact': str(path/'result.json')}
                print(json.dumps({mode: summaries[mode]}), flush=True)
            (args.out_dir/'summary.json').write_text(json.dumps(summaries, indent=2)+'\n')
            return 0 if all(row['check']['status'] == 'proved' for row in summaries.values()) else 3
        path = args.artifact/'result.json' if args.artifact.is_dir() else args.artifact
        result = json.loads(path.read_text())
        round_ = prepare_random_round(result['round']['evidence']['source'])
        checked = verify_result(round_, result)
        if checked['status'] != 'proved':
            print(json.dumps(checked))
            return 3
        print(json.dumps(checked if args.command == 'verify' else evaluate(result, args.n)))
        return 0
    except (AnalysisError, OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'status': 'error', 'reason': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
