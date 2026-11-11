"""Isolated fixed-point experiments; preserve old results and exact replay status."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def worker(config_path):
    from contractive_tool.analysis_pipeline import SearchOptions, run_analysis
    from contractive_tool.assertion_pipeline import verify_assertion
    task = json.loads(config_path.read_text())
    out = Path(task['out'])
    options = SearchOptions(**task['options'])
    summary = run_analysis(task['source'], 'assertion_violation', out, options=options)
    if summary['status'] == 'proved':
        write(out / 'independent_check.json', verify_assertion(out))
    print(json.dumps({'status': summary['status'], 'selection': summary.get('selection')}), flush=True)


def execute(task):
    config = Path(task['config'])
    write(config, task)
    start = time.monotonic()
    command = [sys.executable, str(Path(__file__).resolve()), '--worker', str(config)]
    env = {**os.environ, 'PYTHONPATH': str(PROJECT / 'src'), 'PYTHONUNBUFFERED': '1',
           'OMP_NUM_THREADS': '1', 'OPENBLAS_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1'}
    timed_out = False
    with Path(task['log']).open('w') as log:
        process = subprocess.Popen(command, cwd=PROJECT, env=env, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            code = process.wait(timeout=task['wall_seconds'])
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            code = process.wait()
            timed_out = True
    out = Path(task['out'])
    row = {**task, 'elapsed_seconds': time.monotonic()-start,
           'returncode': code, 'wall_timeout': timed_out}
    summary = out / 'summary.json'
    if summary.exists():
        data = json.loads(summary.read_text())
        row.update(status=data['status'], stop_reason=data.get('stop_reason'),
                   bound=data.get('selection'), diagnostic=data.get('diagnostic'))
    else:
        row['status'] = 'wall_timeout' if timed_out else 'process_error'
    checked = out / 'independent_check.json'
    if checked.exists():
        row['independent_check'] = json.loads(checked.read_text())
    if row['status'] == 'proved' and row.get('independent_check', {}).get('status') != 'proved':
        row['status'] = 'replay_incomplete'
    hist = out / 'analyses/assertion_violation/search_history.json'
    if hist.exists():
        row['search_history'] = json.loads(hist.read_text())
    row['solver_results'] = []
    for path in sorted(out.glob('analyses/assertion_violation/degrees/*/*/attempts/*/solver.json')):
        data = json.loads(path.read_text())
        row['solver_results'].append({'path': str(path), **{k: data.get(k) for k in
            ('status', 'raw_status', 'objective', 'diagnostic', 'elapsed_seconds')}})
    row['stage_files'] = {name: len(list(out.rglob(name))) for name in
        ('polynomial_problem.json', 'conic_model.json', 'solver.json', 'verification.json', 'certificate.json')}
    if code and not timed_out:
        row['error_tail'] = Path(task['log']).read_text()[-3000:]
    write(config.with_name('result.json'), row)
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--worker', type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--jobs', type=int, default=4)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker)
        return
    from contractive_tool.analysis_pipeline import SearchOptions
    root = args.out.resolve()
    root.mkdir(parents=True, exist_ok=False)
    inventory = {r['id']: r for r in json.loads((ROOT / 'inventory.json').read_text())}
    plan = json.loads(args.plan.read_text())
    tasks = []
    for i, spec in enumerate(plan):
        source = Path(spec['source_override']).resolve() if spec.get('source_override') else ROOT / inventory[spec['case']]['source']
        options = asdict(SearchOptions(initial_degree=spec['degree'], max_degree=spec['degree'],
            c_values=(spec['c'],), max_parameter_points=1, max_attempts_per_point=1,
            max_order=max(2, (spec['degree']+1)//2), strategy='putinar',
            max_products=512, max_psd_dimension=100, max_decisions=50000,
            total_seconds=180, per_attempt_seconds=40, repair_seconds=25,
            repair_relative_gap=0.001, repair_max_solves=2, continue_after_success=True,
            verbose=True))
        options.update(spec.get('options', {}))
        SearchOptions(**options).validate()
        if inventory[spec['case']]['family'] == 'M1DWalk':
            p = Fraction(inventory[spec['case']]['parameters']['p'])
            assert Fraction(spec['c'])**4 > 1-p, 'M1DWalk c violates the necessary condition'
        folder = root / f'{i+1:03d}_{spec["case"]}_d{spec["degree"]}'
        task = {**spec, 'source': str(source.resolve()),
            'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'options': options, 'out': str(folder/'run'), 'config': str(folder/'task.json'),
            'log': str(folder/'worker.log'), 'wall_seconds': spec.get('wall_seconds', 240)}
        tasks.append(task)
    write(root/'plan.json', {'started_utc': datetime.now(timezone.utc).isoformat(),
                            'python': sys.executable, 'jobs': args.jobs, 'tasks': tasks})
    rows = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(execute, t) for t in tasks]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            write(root/'results.json', rows)
            print(json.dumps({'case': row['case'], 'degree': row['degree'], 'c': row['c'],
                'status': row['status'], 'A': (row.get('bound') or {}).get('A_numeric'),
                'elapsed_seconds': round(row['elapsed_seconds'], 2), 'stages': row['stage_files']}), flush=True)
    write(root/'completion.json', {'completed_utc': datetime.now(timezone.utc).isoformat(),
                                  'tasks': len(rows), 'statuses': {s: sum(r['status']==s for r in rows)
                                  for s in sorted({r['status'] for r in rows})}})


if __name__ == '__main__':
    main()
