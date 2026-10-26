from common import *

RECIPES=[]
def add(op,fn,method,transform,lesson):RECIPES.append(candidate(op,QUALITY,fn,method,transform,lesson))


def mad_binary(s):
    return body(s,'''    let split=sorted.partition_point(|&v|v<=center);
    let left=|i:usize|(sorted[split-1-i]-center).abs();
    let right=|i:usize|(sorted[split+i]-center).abs();
    let kth=|k:usize| {
        let (mut low,mut high)=((k+1).saturating_sub(sorted.len()-split),(k+1).min(split));
        loop {
            let i=low+(high-low)/2;let j=k+1-i;
            let al=if i>0 {left(i-1)} else {f64::NEG_INFINITY};
            let ar=if i<split {left(i)} else {f64::INFINITY};
            let bl=if j>0 {right(j-1)} else {f64::NEG_INFINITY};
            let br=if j<sorted.len()-split {right(j)} else {f64::INFINITY};
            if al>br {high=i-1;} else if bl>ar {low=i+1;} else {return al.max(bl);}
        }
    };
    let n=sorted.len();
    if n.is_multiple_of(2) {kth(n/2-1)/2.0+kth(n/2)/2.0} else {kth(n/2)}''')
add('inspect_signal','sorted_mad','binary-select MAD across the two ordered deviation halves',mad_binary,
    'The accepted merge avoids a second sort; now select its middle rank without visiting half the window.')
add('inspect_signal','median','bypass sorting for already ordered finite Hampel samples',lambda s:replace(s,
    'values.sort_unstable_by(f64::total_cmp);',
    'if !values.is_sorted_by(|a,b|a.total_cmp(b).is_le()) {values.sort_unstable_by(f64::total_cmp);}'),
    'Smooth windows often arrive ordered; retain full sorting for other distributions and include random/constant inputs.')
def mad_indices(s):
    a=s.index('    for _ in');b=s.index('    if sorted.len()',a)
    return s[:a]+'''    for _ in 0..=sorted.len()/2 {
        previous=current;
        if left>0 && (right==sorted.len() || (sorted[left-1]-center).abs()<=(sorted[right]-center).abs()) {
            left-=1;current=(sorted[left]-center).abs();
        } else {current=(sorted[right]-center).abs();right+=1;}
    }
'''+s[b:]
add('inspect_signal','sorted_mad','merge MAD deviations with explicit exhausted-side checks',mad_indices,
    'Remove per-step Option construction from the successful sorted-deviation merge.')
def mad_peek(s):
    return body(s,'''    let split=sorted.partition_point(|&v|v<=center);
    let mut left=sorted[..split].iter().rev().map(|v|(v-center).abs()).peekable();
    let mut right=sorted[split..].iter().map(|v|(v-center).abs()).peekable();
    let (mut previous,mut current)=(0.0,0.0);
    for _ in 0..=sorted.len()/2 {
        previous=current;
        current=match(left.peek(),right.peek()) {
            (Some(a),Some(b)) if a<=b => left.next().unwrap(),
            (Some(_),None)=>left.next().unwrap(),
            (_,Some(_))=>right.next().unwrap(),_=>unreachable!(),
        };
    }
    if sorted.len().is_multiple_of(2) {previous/2.0+current/2.0} else {current}''')
add('inspect_signal','sorted_mad','cache each MAD frontier deviation in peekable iterators',mad_peek,
    'Each absolute deviation need only be calculated when its frontier advances.')
def quality_sliding(s):
    s=replace(s,'                for i in start..end {',
        '                values.clear();\n                let (mut loaded_a,mut loaded_b)=(start,start);\n                for i in start..end {')
    a=s.index('                    values.clear();');b=s.index('                    if values.len() < 3',a)
    s=s[:a]+'''                    for j in loaded_a..a.min(loaded_b) {
                        let old=signal.row(j)[channel];
                        if old.is_finite() {let index=values.binary_search_by(|v|v.total_cmp(&old)).expect("tracked finite sample");values.remove(index);}
                    }
                    for j in loaded_b.max(a)..b {
                        let value=signal.row(j)[channel];
                        if value.is_finite() {let index=values.partition_point(|v|v.total_cmp(&value).is_lt());values.insert(index,value);}
                    }
                    loaded_a=a;loaded_b=b;
'''+s[b:]
    return s
add('inspect_signal','inspect_signal','maintain a sorted Hampel window by insertion and removal',quality_sliding,
    'Adjacent windows overlap heavily; retain gap boundaries, finite filtering, sample limits and exact median ordering.')
def quality_prefix_search(s):
    s=replace(s,'                for i in start..end {','                let (mut previous_a,mut previous_b)=(start,start);\n                for i in start..end {')
    s=replace(s,'let a = start + times[start..end].partition_point(|&t| i128::from(t) < low);',
        'let a=previous_a+times[previous_a..end].partition_point(|&t|i128::from(t)<low);\n                    previous_a=a;')
    return replace(s,'let b = start + times[start..end].partition_point(|&t| i128::from(t) <= high);',
        'let b=previous_b+times[previous_b..end].partition_point(|&t|i128::from(t)<=high);\n                    previous_b=b;')
add('inspect_signal','inspect_signal','restrict Hampel boundary searches to unconsumed suffixes',quality_prefix_search,
    'Use monotonic window bounds without repeating the earlier full linear-cursor candidate.')
def quality_column(s):
    a=s.index('        if let Some(window) = config.hampel_window_ns {');b=s.index('        if let Some(duration)',a)
    chunk=s[a:b].replace('            let mut start = 0;',
        '            let column:Vec<_>=signal.values().chunks_exact(signal.channels()).map(|row|row[channel]).collect();\n            let mut start = 0;',1)
    chunk=chunk.replace('signal.row(i)[channel]','column[i]').replace('signal.row(j)[channel]','column[j]')
    return s[:a]+chunk+s[b:]
add('inspect_signal','inspect_signal','extract only active Hampel channels into contiguous scratch',quality_column,
    'Avoid the prior FIR-wide transpose cost: allocate one channel only when the expensive window detector is enabled.')
RECIPES += [hint('inspect_signal',QUALITY,'inspect_signal',k) for k in ('always','never')]
add('inspect_signal','emit','mark singleton quality spans by direct index',lambda s:replace(s,
    'report.flagged_samples[start..end].fill(true);',
    'if end==start+1 {report.flagged_samples[start]=true;} else {report.flagged_samples[start..end].fill(true);}'),
    'Point anomalies dominate many reports; retain multi-sample range marking for derivative and flatline issues.')


add('gate','gate','skip code-policy iteration for issue-free reports',lambda s:replace(
    replace(s,'    for code in &policy.reject_codes {','    if !report.all_codes.is_empty() {\n    for code in &policy.reject_codes {'),
    '    Ok(GateDecision {','    }\n    Ok(GateDecision {'),
    'The pass case has no issue codes; avoid repeated searches without allocating a reason buffer.')
def gate_bitmap(s,bits):
    init='    let mut present=0u16;\n    for code in &report.all_codes {present|=1u16<<(*code as usize);}\n' if bits else '    let mut present=[false;10];\n    for code in &report.all_codes {present[*code as usize]=true;}\n'
    s=replace(s,'    for code in &policy.reject_codes {',init+'    for code in &policy.reject_codes {')
    return replace(s,'report.all_codes.contains(code)',
        '(present & (1u16<<(*code as usize)))!=0' if bits else 'present[*code as usize]')
for bits in (False,True):
    add('gate','gate','index present quality codes with '+('a bit mask' if bits else 'a stack bitmap'),
        lambda s,b=bits:gate_bitmap(s,b),'The code enum has ten fixed variants; preserve duplicate policy reasons and their original order.')
add('gate','gate','reserve the exact number of rejection reasons',lambda s:replace(s,'let mut reasons = Vec::new();',
    '''let count=usize::from(report.time.samples<policy.min_samples)+usize::from(fraction>policy.max_flagged_fraction)
        +policy.reject_codes.iter().filter(|code|report.all_codes.contains(code)).count();
    let mut reasons=Vec::with_capacity(count);'''),
    'The earlier unconditional reserve slowed passing reports; exact zero capacity keeps them allocation-free.')
add('gate','gate','reserve a bounded estimate only for likely rejection reasons',lambda s:replace(s,
    'let mut reasons = Vec::new();',
    '''let count=usize::from(report.time.samples<policy.min_samples)+usize::from(fraction>policy.max_flagged_fraction)
        +policy.reject_codes.len().min(report.all_codes.len());
    let mut reasons=Vec::with_capacity(count);'''),
    'Avoid a second membership pass; capacity is a hint, so duplicate policy codes remain intact.')
NAMES='["NonFinite","BelowRange","AboveRange","ClockReversal","DuplicateTime","Gap","Rate","Acceleration","Spike","Flatline"]'
def gate_names(s):
    a=s.index('                match code {');b=s.index('                .to_owned()',a)
    return s[:a]+f'                {NAMES}[*code as usize]\n'+s[b:]
add('gate','gate','look up static issue names by their enum discriminant',gate_names,
    'The earlier switch replaced Debug formatting; compare a fixed table without changing spelling or reason ownership.')
add('gate','gate','return an empty decision immediately for fully passing policies',lambda s:replace(s,
    '    let mut reasons =',
    '''    if report.time.samples>=policy.min_samples && fraction<=policy.max_flagged_fraction
        && policy.reject_codes.iter().all(|code|!report.all_codes.contains(code)) {
        return Ok(GateDecision{passed:true,reasons:Vec::new(),flagged_fraction:fraction});
    }
    let mut reasons ='''),'Measure an explicit pass fast path while retaining the complete reason construction on failure.')
RECIPES += [hint('gate',QUALITY,'gate',k) for k in ('always','never')]
def gate_chain(s):
    frozen=original(QUALITY);start,end=function_span(frozen,'gate');s=frozen[start:end]
    a=s.index('    let mut reasons =');b=s.index('    Ok(GateDecision {',a)
    return s[:a]+f'''    let reasons:Vec<String>=(report.time.samples<policy.min_samples).then_some("too_few_samples").into_iter()
        .chain((fraction>policy.max_flagged_fraction).then_some("flagged_fraction"))
        .chain(policy.reject_codes.iter().filter(|code|report.all_codes.contains(code)).map(|code|{NAMES}[*code as usize]))
        .map(str::to_owned).collect();
'''+s[b:]
add('gate','gate','collect ordered rejection reasons through chained iterators',gate_chain,
    'Keep the same policy order and duplicate behavior while comparing iterator allocation and branch scheduling.')
