"""Report and replay the retained paper runs without invoking synthesis."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT/'experiments/paper_tailbounds/manifest.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def envelope(candidates, n):
    value, candidate = min(
        ((Fraction(c['prefactor_upper'])*Fraction(c['decay_upper'])**n, c)
         for c in candidates), key=lambda item: (item[0], item[1]['id']))
    return {'n': n, 'bound_numeric': float(min(1, value)),
            'method': candidate['method'], 'k': candidate['k'],
            'prefactor_upper': candidate['prefactor_upper'],
            'decay_upper': candidate['decay_upper']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('report', 'verify', 'ablate'))
    parser.add_argument('--cases', nargs='+', help='Canonical labels such as K4 S7')
    parser.add_argument('--out', type=Path, help='Write JSON outside the original run bundles')
    args = parser.parse_args()
    rows = json.loads(INDEX.read_text())['examples']
    if args.cases:
        unknown = set(args.cases)-{row['label'] for row in rows}
        if unknown:
            parser.error(f'Unknown examples: {sorted(unknown)}')
        rows = [row for row in rows if row['label'] in args.cases]
    if args.command == 'ablate':
        rows = [row for row in rows if row['label'] in {'S7', 'K4'}]
    results = []
    failed = False
    for row in rows:
        run = ROOT/row['run']
        if (digest(ROOT/row['source']) != row['source_sha256'] or
                digest(run/'summary.json') != row['summary_sha256'] or
                digest(run/'shared/source.pp') != row['run_source_sha256']):
            raise ValueError(f"Stored source/summary hash changed: {row['label']}")
        summary = json.loads((run/'summary.json').read_text())
        result = {'label': row['label'], 'in_paper_table': row['in_paper_table']}
        if args.command == 'verify':
            from contractive_tool.analysis.symbolic_workflow import verify_workflow
            started = time.monotonic()
            result.update(verify_workflow(run))
            result['replay_seconds'] = time.monotonic()-started
            failed |= result['status'] != 'proved'
            print(f"{row['label']}: {result['status']} ({result['replay_seconds']:.2f}s)",
                  file=sys.stderr, flush=True)
        else:
            candidates = summary['symbolic_workflow']['candidates']
            if args.command == 'report':
                result.update(status=summary['status'], elapsed_seconds=row['elapsed_seconds'],
                              bounds=[envelope(candidates, n) for n in (10, 50, 100)])
            else:
                pools = {
                    'direct': [c for c in candidates if c['method'] == 'direct_polynomial'],
                    'all': candidates,
                    'integer_only': [c for c in candidates if Fraction(c['k']).denominator == 1],
                    'without_reciprocal': [c for c in candidates if c['method'] != 'reciprocal'],
                }
                result['ablations'] = {
                    name: [envelope(pool, n) for n in (20, 50, 100)]
                    for name, pool in pools.items() if pool}
        results.append(result)
    output = {'operation': args.command, 'source': str(INDEX.relative_to(ROOT)),
              'numeric_values_are_display_only': True, 'results': results}
    text = json.dumps(output, indent=2, ensure_ascii=False)+'\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end='')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
