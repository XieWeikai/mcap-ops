#!/usr/bin/env python3
"""Audit measured decisions, not attempted launches, for the 300-round campaign."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess

from report_rsi import EXPECTED

ROOT=Path(__file__).resolve().parents[1]
REPORT=ROOT/'docs/performance/per-op10'
BASE='9de19ead5df7444a9074c71028129b88970ba6ba'


def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true');args=parser.parse_args()
    rows=[];seen=set();history=git('log','--format=%H%x09%s').splitlines()
    for path in sorted((REPORT/'results').glob('*.json')):
        row=json.loads(path.read_text());key=(row['operator'],row['round'])
        assert key not in seen and row['operator'] in EXPECTED and 1<=row['round']<=10,key
        seen.add(key);assert row['series']=='per-op10'
        raw=REPORT/'data'/path.name
        assert hashlib.sha256(raw.read_bytes()).hexdigest()==row['measurement_sha256']
        data=json.loads(raw.read_text());assert len(data['runs'])>=4 and data['cpu']==12
        assert data['summary']==row['case_results']
        ratios=[]
        for block in data['runs']:
            assert set(block['before'])==set(block['after'])==set(row['cases'])
            ratios.append(math.exp(statistics.mean(math.log(block['after'][case]['median_ns']/block['before'][case]['median_ns']) for case in row['cases'])))
        gain=100*(1-statistics.median(ratios));worst=100*(1-max(ratios))
        assert abs(gain-row['geomean_latency_reduction_pct'])<1e-9
        assert abs(worst-row['worst_block_reduction_pct'])<1e-9
        if row['decision']=='accepted':
            assert row['performance_gate'] and gain>=8 and worst>=8
            assert min(value['latency_reduction_pct'] for value in data['summary'].values())>=-3
            assert row.get('png_max_growth_ratio',1)<=1.25
            marker=f"[RSI per-op10 round {row['round']}]"
            matches=[line.split('\t')[0] for line in history if marker in line and f"perf({row['operator']}):" in line]
            assert len(matches)==1,matches
            row['commit']=matches[0]
            body=git('show','-s','--format=%B',row['commit'])
            assert str(path.relative_to(ROOT)) in body and 'ns/op' in body and 'Correctness:' in body
        else:assert (REPORT/'rejected'/f"{row['label']}.patch").is_file()
        rows.append(row)
    if not args.partial:assert seen=={(op,r) for op in EXPECTED for r in range(1,11)},'incomplete 300-round coverage'
    manifest=REPORT/'evidence/manifest.json'
    if manifest.exists() and not args.partial:
        evidence={r['label']:r for r in json.loads(manifest.read_text())}
        assert set(evidence)=={r['label'] for r in rows}
        for row in rows:
            log=REPORT/'evidence'/f"{row['label']}.log"
            assert hashlib.sha256(log.read_bytes()).hexdigest()==row['validation_sha256']
            assert len(evidence[row['label']]['profiles'])>=2
    verification=REPORT/'final/verification.json'
    if verification.exists() and not args.partial:
        for name,digest in json.loads(verification.read_text())['source_sha256'].items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    accepted=sum(r['decision']=='accepted' for r in rows)
    # Pending candidates are intentionally excluded from the retained production diff.
    stats=[line.split('\t',2) for line in git('diff','--numstat',BASE,'HEAD','--','crates/core/src','crates/io/src','crates/python/src','python/mcap_ops').splitlines()]
    added=sum(int(v[0]) for v in stats);removed=sum(int(v[1]) for v in stats)
    text=['# Ten rounds per operator','',f"**{len(rows)}/300 measured decisions; {accepted} accepted, {len(rows)-accepted} rejected.**",'',
        f'Baseline source: `{BASE}`. Builds, profiles, tests and timing run only on reference-linux. '
        'Results use generated fixtures, CPU 12 affinity, four AB/BA paired blocks and seven calibrated samples per side.', '',
        'Acceptance requires >=8% latency reduction in every aggregate block, no representative case slower by >3%, '
        'correctness and complexity checks passing. PNG encoder choices additionally preserve decoded pixels and cap measured output growth at 1.25x.', '',
        f'Retained production diff: {len(stats)} files, +{added}/-{removed} lines (net {added-removed:+d}); pending candidates are excluded.', '',
        '| Operator | Completed | Accepted |','| --- | ---: | ---: |']
    for op in sorted(EXPECTED):
        selected=[r for r in rows if r['operator']==op]
        text.append(f"| `{op}` | {len(selected)}/10 | {sum(r['decision']=='accepted' for r in selected)} |")
    text+=['','Percentages below compare with each round\'s previously accepted state. '
           'They are medians of paired ratios, not ratios of separately displayed median timings. '
           'A parameter sweep is reported as a parameter sweep, not as distinct algorithms.','']
    for op in sorted(EXPECTED):
        selected=sorted((r for r in rows if r['operator']==op),key=lambda r:r['round'])
        if not selected:continue
        text += [f'## {op}','','| Round | Method | Decision | Gain | Worst block | Commit |','| ---: | --- | --- | ---: | ---: | --- |']
        for r in selected:
            text.append(f"| {r['round']} | {r['method']} | [{r['decision']}](results/{r['label']}.json) | {r['geomean_latency_reduction_pct']:+.2f}% | {r['worst_block_reduction_pct']:+.2f}% | `{r.get('commit','-')[:8]}` |")
        text.append('')
    for name in ('native','python'):
        path=REPORT/'final'/f'{name}.json'
        if not path.exists():continue
        data=json.loads(path.read_text())
        text += [f'## Final {name} comparison','','Both source states use the completed benchmark harness. Negative values are regressions.','',
                 '| Case | Before us | After us | Paired reduction |','| --- | ---: | ---: | ---: |']
        for case,v in sorted(data['summary'].items()):text.append(f"| `{case}` | {v['before_ns']/1000:.3f} | {v['after_ns']/1000:.3f} | {v['latency_reduction_pct']:+.2f}% |")
        text.append('')
    notes=REPORT/'final'/'notes.md'
    if notes.exists():text+=['## Verification and limitations','',notes.read_text().strip(),'']
    (REPORT/'RESULTS.md').write_text('\n'.join(text))
    (REPORT/'coverage.json').write_text(json.dumps({'baseline':BASE,'target':300,'completed':len(rows),'accepted':accepted,
        'rejected':len(rows)-accepted,'decisions':rows},indent=2)+'\n')
    print(f'Audited {len(rows)}/300 decisions: {accepted} accepted, {len(rows)-accepted} rejected')


if __name__=='__main__':main()
