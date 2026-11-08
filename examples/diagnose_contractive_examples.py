"""Read-only source-preparation diagnostics, separately from timed synthesis."""
import argparse
import json
from pathlib import Path

from contractive_tool.cfg.builder import build_cfg
from contractive_tool.frontend.parser import parse_file
from contractive_tool.frontend.semantic import check_program
from contractive_tool.analysis.semantics import prepare_program
from contractive_tool.analysis.random_rounds import _invariant_prover,prepare_random_round
from contractive_tool.errors import AnalysisError

PROJECT=Path(__file__).resolve().parents[1]


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args()
    for row in json.loads((args.root/'results.json').read_text()):
        if row['workflow_present'] and not any(s['status']=='unsupported' for s in row['stages']):continue
        data={'source':row['source'],'source_changed':False,'synthesis_rerun':False}
        source=PROJECT/row['source']
        def record(domain,expression,label):
            try:return _invariant_prover(domain,expression,label)
            except AnalysisError as error:
                data['failed_invariant_obligation']={'label':label,'expression':str(expression),
                    'domain':domain.to_data(),'error':str(error)}
                raise
        try:
            cfg=build_cfg(check_program(parse_file(source)))
            evidence=prepare_program(cfg,invariant_prover=record)
            data['invariant_preparation']='passed'
        except AnalysisError as error:
            data['invariant_preparation']='unsupported';data['invariant_error']=str(error)
        try:
            prepare_random_round(source)
            data['finite_random_round']='supported'
        except AnalysisError as error:
            data['finite_random_round']='unsupported';data['finite_random_round_error']=str(error)
        (args.root/row['name']/'diagnostic.json').write_text(json.dumps(data,indent=2)+'\n')
        print(json.dumps({'name':row['name'],**data}),flush=True)


if __name__=='__main__':main()
