"""Run every inventory entry in an isolated process; preserve all diagnostics.

Timeout is an external wall budget, never a proof of infeasibility. No production
analysis options or implementations are changed by this experiment runner.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parent


def worker(source, out, profile):
    from contractive_tool.analysis_pipeline import SearchOptions,run_analysis
    from contractive_tool.assertion_pipeline import verify_assertion
    if profile in ('baseline', 'diagnostic'):
        opts=SearchOptions(initial_degree=1,max_degree=1 if profile=='diagnostic' else 2,c_values=('9999/10000',),
            max_parameter_points=2,max_attempts_per_point=1,max_order=2,max_products=128,
            max_psd_dimension=30,max_decisions=5000,total_seconds=25,per_attempt_seconds=8,
            repair_seconds=3,repair_max_solves=1,verbose=profile=='diagnostic')
    else:
        opts=SearchOptions(initial_degree=1,max_degree=3,c_values=('999/1000','99999/100000'),
            max_parameter_points=6,max_attempts_per_point=2,max_order=2,max_products=256,
            max_psd_dimension=40,max_decisions=8000,total_seconds=75,per_attempt_seconds=12,
            repair_seconds=5,repair_max_solves=1,continue_after_success=True,verbose=False)
    result=run_analysis(source,'assertion_violation',out,options=opts)
    if result['status']=='proved':
        checked=verify_assertion(out)
        (out/'independent_check.json').write_text(json.dumps(checked,indent=2)+'\n')
    print(json.dumps(result),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile',choices=('baseline','retry','diagnostic'),default='baseline')
    parser.add_argument('--jobs',type=int,default=2)
    parser.add_argument('--only',nargs='*')
    parser.add_argument('--label',default=None)
    parser.add_argument('--worker',nargs=2,metavar=('SOURCE','OUT'))
    args=parser.parse_args()
    if args.worker:
        worker(Path(args.worker[0]),Path(args.worker[1]),args.profile);return
    inventory=json.loads((ROOT/'inventory.json').read_text())
    if args.only:inventory=[r for r in inventory if r['id'] in args.only or r['family'] in args.only]
    label=args.label or (args.profile+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    run=ROOT/'runs'/label
    run.mkdir(parents=True,exist_ok=False)
    timeout=120 if args.profile=='retry' else 60
    rows=[]
    metadata={'profile':args.profile,'jobs':args.jobs,'per_case_wall_timeout':timeout,
              'python':sys.executable,'inventory_sha256':hashlib.sha256((ROOT/'inventory.json').read_bytes()).hexdigest()}
    (run/'run_config.json').write_text(json.dumps(metadata,indent=2)+'\n')

    def execute(item):
        start=time.monotonic();out=run/item['id'];log=run/(item['id']+'.log')
        command=[sys.executable,str(Path(__file__).resolve()),'--profile',args.profile,
                 '--worker',str(ROOT/item['source']),str(out)]
        env={**os.environ,'PYTHONUNBUFFERED':'1','OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1'}
        killed=False
        with log.open('w') as stream:
            process=subprocess.Popen(command,cwd=PROJECT,stdout=stream,stderr=subprocess.STDOUT,env=env,start_new_session=True)
            try:code=process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();code=process.returncode;killed=True
        row={**item,'command':command,'returncode':code,'wall_seconds':time.monotonic()-start,
             'run':str(out.relative_to(ROOT)),'log':str(log.relative_to(ROOT))}
        summary_path=out/'summary.json'
        if summary_path.exists():
            summary=json.loads(summary_path.read_text());bound=summary.get('selection')
            row.update(status=summary['status'],stop_reason=summary.get('stop_reason'),
                diagnostic=summary.get('diagnostic'),degrees=summary.get('degrees_attempted'),
                attempts=summary.get('attempt_count'),bound=bound)
            check=out/'independent_check.json'
            row['independent_check']=json.loads(check.read_text()) if check.exists() else None
            if summary['status']=='proved':
                row['classification']='verified_nontrivial' if bound['upper_bound_numeric']<1 else 'verified_trivial'
                if row['independent_check'] is None or row['independent_check']['status']!='proved':row['classification']='replay_incomplete'
            else:row['classification']=summary['status']
            hist=out/'analyses/assertion_violation/search_history.json'
            if hist.exists():
                history=json.loads(hist.read_text());row['attempt_statuses']={}
                for h in history:
                    row['attempt_statuses'][h['status']]=row['attempt_statuses'].get(h['status'],0)+1
                row['attempt_diagnostics']=sorted({h.get('diagnostic') or h.get('reason') for h in history if h.get('diagnostic') or h.get('reason')})
        else:
            row.update(status='wall_timeout' if killed else 'process_error',classification='wall_timeout' if killed else 'process_error',
                       diagnostic=log.read_text()[-1800:])
        return row

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures=[pool.submit(execute,item) for item in inventory]
        for f in as_completed(futures):
            row=f.result();rows.append(row)
            (run/'results.json').write_text(json.dumps(sorted(rows,key=lambda r:r['id']),indent=2)+'\n')
            print(row['id'],row['classification'],round(row['wall_seconds'],2),
                  row.get('bound',{}).get('upper_bound_numeric') if row.get('bound') else '',flush=True)
    print('Results:',run/'results.json',flush=True)


if __name__=='__main__':main()
