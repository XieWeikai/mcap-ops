#!/usr/bin/env python3
"""Ten measured alternatives for each of thirty operators, authored locally."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'benchmarks/ten_rounds'))
import common


def run(*args):subprocess.run(args,cwd=ROOT,check=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--only',required=True);p.add_argument('--retry',action='store_true')
    args=p.parse_args();groups={}
    for file in sorted((ROOT/'benchmarks/ten_rounds').glob('group_*.py')):
        spec=importlib.util.spec_from_file_location(file.stem,file);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        for recipe in module.RECIPES:groups.setdefault(recipe['operator'],[]).append(recipe)
    for op in args.only.split(','):
        assert len(groups[op])==10,(op,len(groups.get(op,[])))
        for number,recipe in enumerate(groups[op],1):
            label=f'ten-{op.replace("_","-")}-{number:02d}'
            reports=ROOT/'docs/performance/per-op10'
            if (reports/'results'/f'{label}.json').exists():continue
            trial=ROOT/'.artifacts/rsi/trials'/label
            print('BEGIN',op,number,recipe['method'],flush=True)
            if not trial.exists():
                sources={name:(ROOT/name).read_text() for name in recipe['paths']};old=dict(sources)
                recipe['apply'](sources)
                if sources==old:raise RuntimeError(f'no-op candidate {label}; choose a genuinely different hypothesis')
                for name,text in sources.items():(ROOT/name).write_text(text)
            elif not args.retry:raise RuntimeError(f'incomplete trial needs --retry: {label}')
            command=[sys.executable,'scripts/rsi_trial.py',label,'--series','per-op10',
                     '--cases',recipe['cases'],'--paths',*recipe['paths']]
            if recipe.get('python'):command.append('--python')
            if args.retry:command.append('--retry')
            run(*command)
            audit=json.loads((trial/'audit.json').read_text());accepted=audit['performance_gate']
            decision=[sys.executable,'scripts/rsi_decide.py',label,'--series','per-op10','--operator',op,
                '--round',str(number),'--method',recipe['method'],'--hotspot',recipe['hotspot'],
                '--complexity','Bounded operator-local change. No new unsafe code, runtime dependencies or relaxed checks. '+recipe['lesson'],
                '--reason',('Accept: every paired block >=8%, representative regression <=3%, correctness passed. ' if accepted else
                            'Reject: performance or resource gate failed; restore last accepted state. ')+recipe['lesson']]
            if accepted:decision.append('--accept')
            run(*decision)
            if accepted:
                run('git','add',*recipe['paths'],f'docs/performance/per-op10/results/{label}.json',f'docs/performance/per-op10/data/{label}.json')
                run('git','commit','-F',str(trial/'commit-message.txt'))
                run('ssh','reference-linux',f'cd . && cp .artifacts/rsi/bin/{label} .artifacts/rsi/bin/accepted && cp python/mcap_ops/_native.abi3.so .artifacts/rsi/python/accepted/mcap_ops/_native.abi3.so && cp python/mcap_ops/__init__.py .artifacts/rsi/python/accepted/mcap_ops/__init__.py')
            print('END',op,number,'accepted' if accepted else 'rejected',flush=True)
            rows=[json.loads(x.read_text()) for x in (reports/'results').glob('*.json')]
            (ROOT/'.artifacts/rsi/per-op10-status.json').write_text(json.dumps({'complete':len(rows),'target':300,
                'accepted':sum(x['decision']=='accepted' for x in rows),'last':label},indent=2)+'\n')


if __name__=='__main__':main()
