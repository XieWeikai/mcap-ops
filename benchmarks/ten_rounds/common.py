"""Bounded alternatives to the campaign baseline; measurements compare last accepted state."""
import re
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from rsi_batch import function_span

BASE='9de19ead5df7444a9074c71028129b88970ba6ba'
TIME='crates/core/src/time.rs'
FILTER='crates/core/src/filter.rs'
QUALITY='crates/core/src/quality.rs'
SAMPLE='crates/core/src/sampling.rs'
SELECT='crates/core/src/selection.rs'
IMAGE='crates/io/src/image_ops.rs'
MCAP='crates/io/src/mcap_ops.rs'
VIDEO='crates/io/src/video.rs'
PYTHON='crates/python/src/lib.rs'
CASES={
 'require_strict':'require_strict', 'uniform_grid':'uniform_grid.integer,uniform_grid.rational',
 'map_clock':'map_clock.identity,map_clock.offset,map_clock.drift',
 'inspect_time':'inspect_time.uniform,inspect_time.jitter',
 'align_timestamps':'align_timestamps.previous,align_timestamps.nearest,align_timestamps.sparse,align_timestamps.repeated',
 'expand_batch_timestamps':'expand_batch_timestamps',
 'resample':'resample.previous,resample.nearest,resample.linear,resample.slerp',
 'history_windows':'history_windows.separate,history_windows.overlap',
 'inspect_signal':'inspect_signal.basic,inspect_signal.hampel,inspect_signal.wide_hampel,inspect_signal.random_hampel,inspect_signal.constant_hampel',
 'gate':'gate.pass,gate.fail','ema':'ema.uniform,ema.jitter','lowpass_taps':'lowpass_taps',
 'fir':'fir.scalar,fir.vector,fir.short_scalar,fir.short_vector,fir.small_scalar,fir.small_vector,fir.wide,fir.gapped',
 'unwrap_angles':'unwrap_angles','interval_new':'interval_new','interval_contains':'interval_contains',
 'interval_mask':'interval_mask.ordered,interval_mask.shuffled',
 'interval_intersection':'interval_intersection.dense,interval_intersection.late',
 'interval_difference':'interval_difference','interval_affected_centers':'interval_affected_centers',
 'raw_reader':'raw_reader.chunked,raw_reader.linear,raw_reader.topics', 'mcap_inspect':'mcap_inspect',
 'json_decode':'json_decode','mcap_read_signal':'mcap_read_signal',
 'image_decode':'image_decode.png,image_decode.jpeg',
 'image_quality':'image_quality.gradient,image_quality.noise',
 'image_transform':'image_transform.gradient,image_transform.noise',
 'video_probe':'video_probe,video_validate','video_validate':'video_validate',
 'python_bridge':'python.resample.previous,python.resample.linear,python.history_windows,python.ema,python.fir,python.unwrap_angles,python.read_json_signal',
}


def replace(s,old,new):
    assert s.count(old)==1,(old,s.count(old))
    return s.replace(old,new,1)


def original(path):
    return subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT,text=True)


def replace_function(source,name,revised):
    start,end=function_span(source,name)
    # Only discard this campaign's explicit inlining hint, never unrelated attributes.
    prefix=source[:start]
    m=re.search(r'#\[inline(?:\((?:always|never)\))?\]\s*$',prefix)
    if m:start=m.start()
    return source[:start]+revised+source[end:]


def candidate(op,path,function,method,transform,lesson,hotspot=None):
    def apply(sources):
        base=original(path)
        start,end=function_span(base,function)
        value=transform(base[start:end])
        sources[path]=replace_function(sources[path],function,value)
    return dict(operator=op,paths=[path],apply=apply,method=method,lesson=lesson,
                hotspot=hotspot or lesson,cases=CASES[op])


def hint(op,path,function,kind):
    return candidate(op,path,function,f'measure {kind} inlining for {op}',
        lambda s:f'#[inline({kind})]\n'+s,
        'Combined-build differences in the prior campaign require measuring code generation; keep identical semantics and flags.')


def body(s,new):
    return s[:s.index('{')+1]+'\n'+new+'\n}'


def change_between(s,start,end,new):
    a=s.index(start);b=s.index(end,a)
    return s[:a]+new+s[b:]
