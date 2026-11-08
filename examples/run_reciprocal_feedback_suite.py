"""Compare the original grid workflow with the complete reciprocal feedback route."""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path
import subprocess
import sys

import sympy as sp

from contractive_tool.analysis.reciprocal import evaluate
from run_reciprocal_suite import CASES, PROJECT, check_reference


EXTRA_CASES = (
    ('kelly_K3', 'contractive_examples/kelly/K3_optimal_fraction_reciprocal.pp', []),
    ('kelly_K4', 'contractive_examples/kelly/K4_periodic_contribution_reciprocal.pp', []),
    ('rcd_04', 'contractive_examples/rcd/rcd_04_reciprocal_anisotropic.pp', ['--degree', '2']),
    ('rcd_05', 'contractive_examples/rcd/rcd_05_reciprocal_random_step.pp', ['--degree', '2']),
    ('qlearning_Q4', 'contractive_examples/qlearning/Q4_reciprocal_underestimate.pp', []),
    ('qlearning_Q5', 'contractive_examples/qlearning/Q5_reciprocal_noisy_progress.pp', []),
)


def log_envelope(result, n):
    if result.get('special_case') == 'initially_exited':
        return None
    def log_rational(value):
        value = sp.Rational(value)
        return math.log(int(value.p))-math.log(int(value.q))
    return min(0.0, min(log_rational(c['prefactor_upper'])+n*log_rational(c['decay_upper'])
                        for c in result['candidates']))


def check_k4_reference(results):
    """Independent rational propagation for the existing affine Kelly K4 loop."""
    alive = {Fraction(1): 1}
    rows = []
    for n in range(21):
        truth = Fraction(sum(alive.values()), 5**n)
        bounds = {mode: evaluate(result, n)['upper_bound_exact'] for mode, result in results.items()}
        if any(truth > Fraction(bound) for bound in bounds.values()):
            raise AssertionError(f'K4 bound below exact tail at n={n}')
        rows.append({'n': n, 'true_tail_exact': str(truth), 'true_tail_approx': float(truth),
                     'bounds': bounds, 'states': len(alive)})
        if n == 20:
            break
        next_alive = {}
        for wealth, mass in alive.items():
            for multiplier, weight in ((Fraction(5, 4), 4), (Fraction(7, 8), 1)):
                value = multiplier*wealth+Fraction(1, 8)
                if 1 <= value < 4:
                    next_alive[value] = next_alive.get(value, 0)+weight*mass
        alive = next_alive
    return {'status': 'passed', 'method': 'independent_fraction_state_propagation', 'horizons': '0..20', 'rows': rows}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, required=True)
    parser.add_argument('--names', nargs='+')
    args = parser.parse_args()
    root = args.out_dir.resolve()
    if root.exists() and any(root.iterdir()):
        parser.error('Use a new or empty output directory')
    root.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, source, extra in (*CASES, *EXTRA_CASES):
        if args.names and name not in args.names:
            continue
        row = {'name': name, 'source': source, 'modes': {}}
        proved_results = {}
        for mode, flags in (('baseline', ['--no-adaptive-k', '--feedback-points', '0']),
                            ('feedback', ['--feedback-points', '12'])):
            out = root/name/mode
            command = [sys.executable, '-m', 'contractive_tool.reciprocal_cli', 'run', str(PROJECT/source),
                '--out-dir', str(out), '--total-seconds', '60', '--solver-seconds', '10',
                '--feedback-seconds', '40', *flags, *extra]
            try:
                run = subprocess.run(command, text=True, capture_output=True, cwd=PROJECT, timeout=150)
            except subprocess.TimeoutExpired:
                summary = {'status': 'external_timeout', 'command': command}
            else:
                (root/name).mkdir(exist_ok=True)
                (root/name/(mode+'.log')).write_text(run.stdout+run.stderr)
                result = json.loads((out/'result.json').read_text()) if (out/'result.json').exists() else {'status': 'error'}
                summary = {'status': result['status'], 'command': command, 'returncode': run.returncode,
                           'reason': result.get('reason'), 'elapsed_seconds': result.get('elapsed_seconds'),
                           'candidates': len(result.get('candidates', []))}
                if result['status'] == 'proved':
                    proved_results[mode] = result
                    summary['independent_check'] = result['independent_check']
                    summary['bounds'] = {str(n): evaluate(result, n) for n in (0, 20, 100, 500, 1000)}
                    summary['log_bounds_approx'] = {str(n): log_envelope(result, n) for n in (20, 100, 1000)}
                    reference = check_reference(name, result)
                    if reference is not None:
                        (out/'reference_check.json').write_text(json.dumps(reference, indent=2)+'\n')
                        summary['reference_check'] = 'passed'
            row['modes'][mode] = summary
            print(json.dumps({'name': name, 'mode': mode, 'status': summary['status'],
                              'elapsed_seconds': summary.get('elapsed_seconds')}), flush=True)
        if name == 'kelly_K4' and proved_results:
            reference = check_k4_reference(proved_results)
            (root/name/'reference_check.json').write_text(json.dumps(reference, indent=2)+'\n')
            row['reference_check'] = 'passed'
        rows.append(row)
        (root/'comparison.json').write_text(json.dumps(rows, indent=2)+'\n')
    return int(any(m['status'] in ('error', 'external_timeout') for r in rows for m in r['modes'].values()))


if __name__ == '__main__':
    raise SystemExit(main())
