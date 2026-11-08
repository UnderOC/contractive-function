"""Reproduce standalone reciprocal experiments on unmodified existing inputs."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import sympy as sp

from contractive_tool.analysis.reciprocal import evaluate


PROJECT = Path(__file__).resolve().parents[1]
CASES = (
    ('kelly_auto', 'kelly_double_bound.pp', []),
    ('kelly_fixed', 'kelly_double_bound.pp', ['--eta', 'wealth']),
    ('kelly_refined', 'kelly_double_bound.pp', ['--growth-values', '33/32', '67/64', '133/128']),
    ('kelly_unbounded', 'kelly_unbounded.pp', []),
    ('halving', 'tests/fixtures/halving.pp', []),
    ('geometric_exit', 'tests/fixtures/geometric_exit.pp', []),
    ('RCD', 'RCD_example.pp', []),
    ('cauchy_notes', 'examples/cauchy_notes.pp', []),
    ('qlearning', 'qlearning.pp', []),
    ('coupon2', 'tailbound_benchmark_pack/pp/01_coupon2.pp', []),
    ('uniform', 'uniform_multiplicative.pp', []),
)


def check_reference(name, result):
    """Independent exact survival propagation, only for these benchmark checks."""
    if name not in ('kelly_auto', 'kelly_fixed', 'kelly_refined', 'geometric_exit'):
        return None
    alive = {sp.Integer(1): sp.Integer(1)}
    observations = []
    for n in range(101):
        truth = sp.Rational(1, 2)**n if name == 'geometric_exit' else sum(alive.values())
        upper = sp.Rational(evaluate(result, n)['upper_bound_exact'])
        if truth > upper:
            raise AssertionError(f'{name}: bound below true survival probability at n={n}')
        if n in (0, 5, 20, 100):
            observations.append({'n': n, 'true_tail_exact': str(truth), 'true_tail_approx': float(truth),
                                 'certificate_upper_exact': str(upper)})
        if name != 'geometric_exit':
            next_alive = {}
            for wealth, probability in alive.items():
                for factor, weight in ((sp.Rational(6, 5), sp.Rational(3, 5)),
                                       (sp.Rational(4, 5), sp.Rational(2, 5))):
                    new = factor*wealth
                    if sp.Rational(1, 2) <= new < 2:
                        next_alive[new] = next_alive.get(new, 0)+weight*probability
            alive = next_alive
    return {'status': 'passed', 'horizons': '0..100 inclusive', 'observations': observations,
            'note': 'finite-horizon regression only; the uniform theorem uses the exact conic certificates'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    root = args.out_dir.resolve()
    if root.exists() and any(root.iterdir()):
        parser.error('Use a new or empty output directory')
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, source, extra in CASES:
        command = [sys.executable, '-m', 'contractive_tool.reciprocal_cli', 'run',
                   str(PROJECT/source), '--out-dir', str(root/name),
                   '--total-seconds', '30', '--solver-seconds', '10', *extra]
        try:
            process = subprocess.run(command, text=True, capture_output=True, timeout=90, cwd=PROJECT)
        except subprocess.TimeoutExpired:
            row = {'name': name, 'source': source, 'status': 'external_timeout', 'command': command}
        else:
            (root/(name+'.log')).write_text(process.stdout+process.stderr)
            path = root/name/'result.json'
            result = json.loads(path.read_text()) if path.exists() else {'status': 'error'}
            row = {'name': name, 'source': source, 'status': result['status'],
                   'returncode': process.returncode, 'command': command,
                   'reason': result.get('reason'), 'elapsed_seconds': result.get('elapsed_seconds'),
                   'candidates': len(result.get('candidates', []))}
            if result['status'] == 'proved':
                row['independent_check'] = result['independent_check']
                row['bounds'] = {str(n): evaluate(result, n) for n in (0, 5, 20, 100, 500, 1000)}
                reference = check_reference(name, result)
                if reference is not None:
                    (root/name/'reference_check.json').write_text(json.dumps(reference, indent=2)+'\n')
                    row['reference_check'] = 'passed'
        rows.append(row)
        (root/'summary.json').write_text(json.dumps(rows, indent=2)+'\n')
        print(json.dumps({k: v for k, v in row.items() if k not in ('command', 'bounds')}), flush=True)
    return 1 if any(r['status'] in ('error', 'external_timeout') for r in rows) else 0


if __name__ == '__main__':
    raise SystemExit(main())
