"""Replay selected refinement certificates in ORIGINAL benchmark coordinates.

The standard backend and experimental rational recovery remain distinct. All
published new bounds must satisfy the source's full first-moment obligations.
"""
from functools import lru_cache
from pathlib import Path
import argparse
import hashlib
import json

import sympy as sp

from contractive_tool.assertion_pipeline import verify_assertion
from recover_univariate import build_cfg, check_program, parse_file, prepare_program, verify_raw
from scale_refinement_inputs import verify_conjugacy


def read(path):
    return json.loads(path.read_text())


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).parent/'refinement_20261109')
    args = parser.parse_args()
    root = args.root.resolve()
    baseline = read(root.parent/'results.json')
    baseline_path = root/'baseline_snapshot.json'
    if baseline_path.exists():
        assert read(baseline_path) == baseline, 'Baseline changed since first audit'
    else:
        write(baseline_path, baseline)
    old = {r['id']: r for r in baseline['cases']}
    equivalent = {r['id']: r for r in read(root/'scaled_inputs/equivalence.json')}
    conjugacy_checks = []

    @lru_cache(None)
    def original(case):
        item = equivalent[case]
        source = Path(item['original_source'])
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item['original_sha256'] == old[case]['source_sha256']
        cfg = build_cfg(check_program(parse_file(source)))
        return cfg, prepare_program(cfg)

    for case, item in equivalent.items():
        cfg, _ = original(case)
        source = Path(item['scaled_source'])
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item['scaled_sha256']
        scaled = build_cfg(check_program(parse_file(source)))
        check = verify_conjugacy(cfg, scaled, item['scales'])
        conjugacy_checks.append({'case': case, **check})
    write(root/'coordinate_replay.json', conjugacy_checks)

    candidates = []
    completions = {}
    run_rows = []
    for batch in ('pilot', 'scaled_pilot', 'matrix', 'm1dwalk', 'newton_c'):
        completions[batch] = read(root/batch/'completion.json')
        for path in sorted((root/batch).glob('*/result.json')):
            result = read(path)
            run_rows.append({'batch': batch, 'case': result['case'], 'degree': result['degree'],
                             'c': result['c'], 'status': result['status'],
                             'elapsed_seconds': result['elapsed_seconds'],
                             'record': str(path.relative_to(root))})
            run = path.parent/'run'
            if result['status'] == 'proved':
                replay = verify_assertion(run)
                assert replay['status'] == 'proved', (path, replay)
                cert_path = run/result['bound']['certificate']
                cert = read(cert_path)
                candidates.append({'case': result['case'], 'method': 'standard_backend',
                    'certificate': str(cert_path), 'raw_polynomials': cert['raw_polynomials'],
                    'c': cert['bound']['c'], 'degree': cert['bound']['degree'],
                    'A_exact': cert['bound']['A_exact'], 'positivity_margin': cert['context']['positivity_margin'],
                    'source': result['source'], 'source_sha256': result['source_sha256'], 'standard_replay': replay})
            recovery = run/'univariate_recovery.json'
            if recovery.exists() and read(recovery)['status'] == 'proved':
                candidates.append({**read(recovery), 'case': result['case'],
                    'method': 'rational_recovery', 'certificate': str(recovery)})
    for row in read(root/'m1dwalk_constructive/results.json'):
        path = Path(row['certificate'])
        candidates.append({**read(path), 'case': row['case'], 'method': 'restricted_quadratic',
                           'certificate': str(path)})

    def best(case, standard=False):
        choices = [c for c in candidates if c['case'] == case and
                   (not standard or c['method'] == 'standard_backend')]
        return min(choices, key=lambda c: sp.Rational(c['A_exact'])) if choices else None

    # Check both the best standard result and the best combined result per case,
    # plus every M1DWalk c-grid point used in the published comparison.
    selected = {c['certificate']: c for c in candidates if c['method'] == 'restricted_quadratic'}
    for case in equivalent:
        for c in (best(case), best(case, True)):
            if c:
                selected[c['certificate']] = c
    proofs = root/'original_certificates'
    proofs.mkdir(exist_ok=True)
    audited = {}
    for i, candidate in enumerate(selected.values()):
        case = candidate['case']
        item = equivalent[case]
        source = Path(candidate['source'])
        assert hashlib.sha256(source.read_bytes()).hexdigest() == candidate['source_sha256'] == item['scaled_sha256']
        # u_i = x_i / scale_i, with original program variable names retained.
        substitution = {sp.Symbol(n): sp.Symbol(n)/sp.Rational(v) for n, v in item['scales'].items()}
        raw = {loc: sp.expand(sp.sympify(expr).subs(substitution, simultaneous=True))
               for loc, expr in candidate['raw_polynomials'].items()}
        cfg, evidence = original(case)
        check = verify_raw(cfg, evidence, raw, sp.Rational(candidate['c']),
                           sp.Rational(candidate['positivity_margin']))
        assert check is not None, (case, candidate['certificate'])
        assert sp.Rational(check['A_exact']) == sp.Rational(candidate['A_exact'])
        dest = proofs/f"{i+1:02d}_{case}_{candidate['method']}.json"
        write(dest, {**check, 'case': case, 'source': item['original_source'],
                     'source_sha256': item['original_sha256'],
                     'raw_polynomials': {k: str(v) for k, v in raw.items()},
                     'positivity_margin': candidate['positivity_margin'], 'degree': candidate['degree'],
                     'candidate_method': candidate['method'], 'candidate_certificate': candidate['certificate']})
        audited[candidate['certificate']] = str(dest.relative_to(root))
        print(json.dumps({'original_replay': case, 'method': candidate['method'],
                          'A': check['A_numeric'], 'status': check['status']}), flush=True)

    def brief(candidate):
        if not candidate:
            return None
        return {k: candidate[k] for k in ('method', 'c', 'degree', 'A_exact', 'certificate')} | {
            'A_numeric': float(sp.Rational(candidate['A_exact'])),
            'original_replay': audited[candidate['certificate']]}

    rows = []
    for case, item in equivalent.items():
        before = old[case].get('bound')
        previous = sp.Rational(before['upper_bound_exact']) if before else sp.Integer(1)
        after = best(case)
        improved = bool(after is not None and sp.Rational(after['A_exact']) < previous)
        rows.append({'case': case, 'family': item['family'], 'paper_bound_direction': item['paper_bound_direction'],
            'old_status': old[case]['classification'],
            'old_upper_bound': str(previous) if before else None,
            'old_upper_bound_numeric': float(previous) if before else None,
            'old_degree': before['degree'] if before else None,
            'old_c': before['c'] if before else None,
            'best_standard': brief(best(case, True)), 'best_new': brief(after),
            'improved_over_old': improved,
            'retained_upper_bound_exact': str(min(previous, sp.Rational(after['A_exact']))) if after else str(previous)})
    report = {'scope': '18 degree-refinement cases plus 3 M1DWalk cases',
        'comparison': 'previous contractive_function records, not paper RepRSM bounds',
        'batches': completions, 'runs': run_rows, 'coordinate_replays': len(conjugacy_checks),
        'original_certificate_replays': len(audited), 'cases': rows,
        'improved_existing_cases': sum(r['improved_over_old'] and r['old_upper_bound'] is not None for r in rows),
        'new_nontrivial_cases': sum(r['improved_over_old'] and r['old_upper_bound'] is None for r in rows)}
    write(root/'comparison.json', report)
    print(json.dumps({k: report[k] for k in ('coordinate_replays', 'original_certificate_replays',
                                          'improved_existing_cases', 'new_nontrivial_cases')}), flush=True)


if __name__ == '__main__':
    main()
