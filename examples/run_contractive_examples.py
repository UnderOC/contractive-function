"""Run the 15 packaged programs under the previous Kelly workflow settings.

Runs sequentially so timings do not include contention between benchmark jobs.
Existing human witnesses are never loaded into synthesis. Each successful
workflow is separately replayed by the public verify CLI.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import time

PROJECT=Path(__file__).resolve().parents[1]
NS=(5,10,20,50,100,200,500,1000)


def write(path,data):
    path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')


def launch(command, log, timeout):
    start=time.monotonic()
    with log.open('w') as stream:
        try:
            process=subprocess.run(command,cwd=PROJECT,stdout=stream,stderr=subprocess.STDOUT,
                                   timeout=timeout)
            return {'returncode':process.returncode,'wall_seconds':time.monotonic()-start}
        except subprocess.TimeoutExpired:
            return {'returncode':None,'status':'external_timeout','wall_seconds':time.monotonic()-start}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir',type=Path,required=True)
    parser.add_argument('--cases',nargs='+',help='Optional exact source stems; default: all packaged examples')
    args=parser.parse_args()
    root=args.out_dir.resolve()
    if root.exists() and any(root.iterdir()):
        parser.error('Use a new or empty output directory')
    root.mkdir(parents=True,exist_ok=True)
    config=json.loads((PROJECT/'examples/tailbound_comparison.json').read_text())
    write(root/'workflow.json',config)
    rows=[]
    sources=sorted((PROJECT/'contractive_examples').glob('*/*.pp'))
    if args.cases:
        unknown=set(args.cases)-{s.stem for s in sources}
        if unknown:
            parser.error(f'Unknown examples: {sorted(unknown)}')
        sources=[s for s in sources if s.stem in args.cases]
    write(root/'protocol.json',{'sources':[str(s.relative_to(PROJECT)) for s in sources],
        'positive_seconds':180,'reciprocal_seconds':120,'feedback_seconds':90,'feedback_points':24,
        'initial_degree':2,'max_degree':4,'max_c_steps':12,'per_attempt_seconds':10,'repair_seconds':5,
        'comparison_ns':NS,'sequential':True,'external_solve_timeout':600,'external_verify_timeout':180,
        'variables':'all source variables; no extra round counter in these examples',
        'input_witnesses_used':False,'workflow_config':config})
    for source in sources:
        name=source.stem
        case=root/name;case.mkdir()
        command=[sys.executable,'-m','contractive_tool','solve',str(source),'--goal','tailbound',
            '--initial-degree','2','--max-degree','4','--max-c-steps','12',
            '--total-seconds','180','--reciprocal-seconds','120','--per-attempt-seconds','10',
            '--repair-seconds','5','--comparison-n',*map(str,NS),
            '--workflow-config',str(root/'workflow.json'),'--out-dir',str(case/'run')]
        print(json.dumps({'event':'start','case':name}),flush=True)
        row={'name':name,'family':source.parent.name,'source':str(source.relative_to(PROJECT)),
            'source_sha256':sha256(source.read_bytes()).hexdigest(),'command':command}
        row.update(launch(command,case/'solve.log',600))
        summary_path=case/'run/summary.json'
        summary=json.loads(summary_path.read_text()) if summary_path.exists() else {}
        row['summary_status']=summary.get('status')
        if row.get('status')!='external_timeout':
            row['status']=summary.get('status','error')
            if row['returncode'] not in (0,3): row['status']='error'
        row.update(diagnostic=summary.get('diagnostic'),stop_reason=summary.get('stop_reason'),
                   elapsed_seconds=summary.get('elapsed_seconds'),
                   degrees_attempted=summary.get('degrees_attempted'),
                   workflow_present='symbolic_workflow' in summary)
        workflow=summary.get('symbolic_workflow',{})
        row['stages']=workflow.get('stages',[])
        row['candidate_counts']={method:sum(c['method']==method for c in workflow.get('candidates',[]))
                                 for method in sorted({c['method'] for c in workflow.get('candidates',[])})}
        # Summary already stores exact full comparisons; retain links and concise
        # measurements here instead of duplicating huge rational evaluations.
        row['comparisons']=[{'n':r['n'],**{k:None if not r.get(k) else
            {field:r[k][field] for field in ('id','method','eta','k','prefactor_upper','decay_upper','upper_bound_numeric')}
            for k in ('integer','noninteger','cauchy_integer','reciprocal','overall')}}
            for r in workflow.get('comparisons',[])]
        for stage in row['stages']:
            if stage['stage']=='reciprocal' and stage.get('artifact'):
                result=json.loads((case/'run'/stage['artifact']).read_text())
                row['reciprocal_search']={key:result.get(key) for key in
                    ('stop_reason','feedback_stop_reason','elapsed_seconds')}
                row['reciprocal_search'].update(attempts=len(result['attempts']),
                    feedback_iterations=len(result.get('feedback_history',[])),
                    improved_iterations=[h['iteration'] for h in result.get('feedback_history',[]) if h.get('improved')])
        if row['status']=='proved' and workflow:
            check_command=[sys.executable,'-m','contractive_tool','verify',str(case/'run')]
            row['verification_process']=launch(check_command,case/'verify.log',180)
            try:
                row['verification']=json.loads((case/'verify.log').read_text())
            except ValueError:
                row['verification']={'status':'verification_error'}
        if sha256(source.read_bytes()).hexdigest()!=row['source_sha256']:
            raise RuntimeError('Source changed during experiment')
        write(case/'measurement.json',row)
        rows.append(row);write(root/'results.json',rows)
        print(json.dumps({'event':'finish','case':name,'status':row['status'],
            'wall_seconds':row['wall_seconds'],'methods':row['candidate_counts'],
            'verification':row.get('verification',{}).get('status')}),flush=True)
    return int(any(r['status'] in ('error','external_timeout') or
        (r['status']=='proved' and
         (r.get('verification',{}).get('status')!='proved' or
          r.get('verification_process',{}).get('returncode')!=0)) for r in rows))


if __name__=='__main__':
    raise SystemExit(main())
