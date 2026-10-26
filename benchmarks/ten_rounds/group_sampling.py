from common import *

RECIPES=[]
def add(op,fn,method,transform,lesson):RECIPES.append(candidate(op,SAMPLE,fn,method,transform,lesson))


add('resample','resample','seed resampling at the first target support prefix',lambda s:replace(s,
    'let mut right = 0;', 'let mut right=target.first().map_or(0,|&t|times.partition_point(|&v|v<t));'),
    'Avoid walking irrelevant earlier samples while retaining strict source validation and all provenance.')
def sample_repeat(s):
    return replace(s,'    for (i, &t) in target.iter().enumerate() {', '''    for (i, &t) in target.iter().enumerate() {
        if i>0 && t==target[i-1] {
            let d=signal.channels();let (past,tail)=out.values.split_at_mut(i*d);
            tail[..d].copy_from_slice(&past[(i-1)*d..]);
            out.status[i]=out.status[i-1];out.source_left[i]=out.source_left[i-1];out.source_right[i]=out.source_right[i-1];
            out.alpha[i]=out.alpha[i-1];out.uses_future[i]=out.uses_future[i-1];continue;
        }''')
add('resample','resample','reuse sampled values and provenance for duplicate targets',sample_repeat,
    'History deduplication helped earlier; direct resampling also permits identical adjacent target times.')
def slerp_exact(s):
    return replace(s,'    let (na, nb) =', '''    if std::ptr::eq(a,b) {
        let na=norm(a);if (na-1.0).abs()>0.01 {return None;}
        let mut q=[0.0;4];for j in 0..4 {q[j]=a[j]/na;}
        let n=norm(&q);for value in &mut q {*value/=n;}return Some(q);
    }
    let (na, nb) =''')
add('resample','slerp','normalize exact quaternion samples without duplicating endpoint work',slerp_exact,
    'Only identical borrowed endpoint slices take this path; both normalization steps and invalid-quaternion behavior remain.')
def slerp_reciprocal(s):
    s=replace(s,'    let mut qa =','    let (inverse_a,inverse_b)=(1.0/na,1.0/nb);\n    let mut qa =')
    s=replace(s,'a[j] / na','a[j] * inverse_a');s=replace(s,'b[j] / nb','b[j] * inverse_b')
    s=replace(s,'    let n = norm(&q);','    let inverse=1.0/norm(&q);')
    return replace(s,'*v /= n;','*v *= inverse;')
add('resample','slerp','reuse bounded quaternion normalization reciprocals',slerp_reciprocal,
    'Endpoint norms are validated near one; compare f64 results without changing quaternion validity thresholds.')
add('resample','resample','infer interpolation input finiteness from the computed output',lambda s:replace(s,
    'all_finite &= x.is_finite() & y.is_finite() & value.is_finite();','all_finite &= value.is_finite();'),
    'A NaN or infinite endpoint cannot yield a finite weighted sum under IEEE arithmetic, including zero-weight endpoints.')
def sample_unsigned(s):
    s=s.replace('i128::from(t) - i128::from(times[a])','t.abs_diff(times[a])')
    s=s.replace('i128::from(times[b]) - i128::from(t)','times[b].abs_diff(t)')
    s=s.replace('i128::from(times[b]) - i128::from(times[a])','times[b].abs_diff(times[a])')
    s=s.replace('> i128::from(options.max_gap_ns)','> options.max_gap_ns as u64')
    s=s.replace('(t.abs_diff(times[a])).abs() > i128::from(options.max_age_ns)',
                't.abs_diff(times[a]) > options.max_age_ns as u64')
    return s
add('resample','resample','use unsigned support distances on ordered resampling brackets',sample_unsigned,
    'Ordered brackets prove the direction of each difference; preserve full-range integer distances and causal policies.')
def sample_zero(sources):
    text=sources[SAMPLE]
    a,b=function_span(text,'empty');empty=text[a:b]
    empty=replace(empty,'values: vec![f64::NAN; size]','values: vec![0.0; size]')
    text=replace_function(text,'empty',empty)
    a,b=function_span(text,'resample');s=text[a:b]
    s=replace(s,'''        let Some((a, b, alpha)) = support else {
            continue;''','''        let Some((a, b, alpha)) = support else {
            out.values[i*signal.channels()..(i+1)*signal.channels()].fill(f64::NAN);
            continue;''')
    s=replace(s,'''            out.status[i] = status as u8;
            continue;''','''            out.status[i] = status as u8;
            out.values[i*signal.channels()..(i+1)*signal.channels()].fill(f64::NAN);
            continue;''')
    s=replace(s,'''                out.status[i] = Status::NonFinite as u8;
                continue;''','''                out.status[i] = Status::NonFinite as u8;
                values.fill(f64::NAN);
                continue;''')
    s=replace(s,'''                    out.status[i] = Status::InvalidQuaternion as u8;
                    continue;''','''                    out.status[i] = Status::InvalidQuaternion as u8;
                    values.fill(f64::NAN);
                    continue;''')
    sources[SAMPLE]=replace_function(text,'resample',s)
RECIPES.append(dict(operator='resample',paths=[SAMPLE],apply=sample_zero,cases=CASES['resample'],
    method='allocate sampled values as zeroed storage and fill only invalid rows with NaNs',
    lesson='Every valid row is fully written; retain NaNs for each missing, future, stale, gap, non-finite and invalid-quaternion outcome.',
    hotspot='Sampled output initialization writes a full NaN buffer before valid interpolation overwrites it.'))
RECIPES += [hint('resample',SAMPLE,'resample',k) for k in ('always','never')]
def sample_status_zip(s):
    frozen=original(SAMPLE);a,b=function_span(frozen,'resample');s=frozen[a:b]
    s=replace(s,'    for (i, &t) in target.iter().enumerate() {',
        '    for (i,(&t,out_status)) in target.iter().zip(out.status.iter_mut()).enumerate() {')
    return s.replace('out.status[i]','*out_status')
add('resample','resample','zip target timestamps with mutable sample statuses',sample_status_zip,
    'Remove separate status-vector indexing while leaving values, timestamps and provenance unchanged.')


add('history_windows','history_windows','stably merge-sort history request timestamps',lambda s:replace(s,
    'requests.sort_unstable_by_key(|&(t, index)| (t, index));','requests.sort_by_key(|&(t,_)|t);'),
    'Removing tie keys alone failed earlier; stable adaptive sorting may exploit the nearly ordered offset streams.')
def history_heap(s):
    a=s.index('    let mut requests =');b=s.index('    let mut sorted =',a)
    return s[:a]+'''    let mut requests=Vec::with_capacity(size);
    let mut heap=std::collections::BinaryHeap::with_capacity(offsets.len());
    if let Some(&first)=centers.first() {
        for (j,&offset) in offsets.iter().enumerate() {
            heap.push(std::cmp::Reverse((first.checked_add(offset).ok_or(Error::Overflow)?,j,0usize,j)));
        }
    }
    while let Some(std::cmp::Reverse((time,dest,i,j)))=heap.pop() {
        requests.push((time,dest));
        if i+1<centers.len() {heap.push(std::cmp::Reverse((centers[i+1].checked_add(offsets[j]).ok_or(Error::Overflow)?,(i+1)*offsets.len()+j,i+1,j)));}
    }
'''+s[b:]
add('history_windows','history_windows','merge sorted history offset streams with a bounded heap',history_heap,
    'Each fixed offset gives an ordered center stream; merge K streams instead of sorting all M requests.')
def history_heads(s):
    a=s.index('    let mut requests =');b=s.index('    let mut sorted =',a)
    return s[:a]+'''    let mut requests=Vec::with_capacity(size);
    let mut positions=vec![0usize;offsets.len()];
    while requests.len()<size {
        let mut best:Option<(i64,usize,usize)>=None;
        for (j,(&offset,&i)) in offsets.iter().zip(&positions).enumerate() {
            if i<centers.len() {
                let item=(centers[i].checked_add(offset).ok_or(Error::Overflow)?,i*offsets.len()+j,j);
                if best.is_none_or(|v|item<v) {best=Some(item);}
            }
        }
        let (time,dest,j)=best.unwrap();requests.push((time,dest));positions[j]+=1;
    }
'''+s[b:]
add('history_windows','history_windows','merge history streams by scanning their current heads',history_heads,
    'For short history contexts, a small head scan can beat heap maintenance and whole-request sorting.')
def history_no_indices(s):
    s=replace(s,'    let mut sample_indices = Vec::with_capacity(requests.len());\n','')
    s=replace(s,'        sample_indices.push(sorted.len() - 1);\n','')
    return replace(s,'    for (&index, &(time, dest)) in sample_indices.iter().zip(&requests) {',
        '''    let mut index=0;
    for &(time,dest) in &requests {
        if sampled.timestamps[index]!=time {index+=1;}''')
add('history_windows','history_windows','scatter history samples with a monotone unique index',history_no_indices,
    'The accepted deduplication makes sample_indices reconstructible; avoid storing one extra usize per request.')
def history_hash(s):
    a=s.index('    requests.sort_unstable_by_key');b=s.index('    let sampled =',a)
    s=s[:a]+'''    let mut indices=std::collections::HashMap::with_capacity(requests.len());
    for &(time,_) in &requests {indices.entry(time).or_insert(0usize);}
    let mut sorted:Vec<_>=indices.keys().copied().collect();sorted.sort_unstable();
    for (i,time) in sorted.iter().enumerate() {*indices.get_mut(time).unwrap()=i;}
'''+s[b:]
    return replace(s,'    for (&index, &(time, dest)) in sample_indices.iter().zip(&requests) {',
        '    for &(time,dest) in &requests {\n        let index=indices[&time];')
add('history_windows','history_windows','sort unique history times and index requests by hash',history_hash,
    'Heavily overlapping windows have far fewer unique times; deterministic sorting and destination scatter preserve output order.')
add('history_windows','history_windows','compare history separation using unsigned spans',lambda s:replace(s,
    '''i128::from(w[0]) + i128::from(*offsets.last().unwrap())
            <= i128::from(w[1]) + i128::from(offsets[0])''',
    'w[1].abs_diff(w[0])>=offsets.last().unwrap().abs_diff(offsets[0])'),
    'Strict centers and ordered nonpositive offsets allow an equivalent full-range span comparison.')
def history_dest(s):
    s=replace(s,'for (i, &center) in centers.iter().enumerate() {','for &center in centers {')
    s=replace(s,'for (j, &offset) in offsets.iter().enumerate() {','for &offset in offsets {')
    return replace(s,'i * offsets.len() + j,','requests.len(),')
add('history_windows','history_windows','derive flat history destinations from request length',history_dest,
    'The generation order is already step-major; avoid repeated index multiplication without changing shape.')
RECIPES += [hint('history_windows',SAMPLE,'history_windows',k) for k in ('always','never')]
def history_owned(sources):
    text=sources[SAMPLE];a,b=function_span(text,'empty');empty=text[a:b]
    owned=replace(empty,'fn empty(target: &[i64], channels: usize)','fn empty_owned(target: Vec<i64>, channels: usize)')
    owned=replace(owned,'timestamps: target.to_vec(),','timestamps: target,')
    owned=owned.replace('target.len()','count')
    owned=owned.replace('{\n','{\n        let count=target.len();\n',1)
    borrowed='''fn empty(target:&[i64],channels:usize)->Result<Self> {
        target.len().checked_mul(channels).ok_or(Error::Overflow)?;
        Self::empty_owned(target.to_vec(),channels)
    }
    '''
    text=replace_function(text,'empty',borrowed+owned)
    text=replace(text,'Sampled::empty(&vec![0; size], signal.channels())?',
        'Sampled::empty_owned(vec![0; size], signal.channels())?')
    sources[SAMPLE]=text
RECIPES.append(dict(operator='history_windows',paths=[SAMPLE],apply=history_owned,cases=CASES['history_windows'],
    method='move the history timestamp buffer into empty sampled storage',
    lesson='The overlapping path currently allocates a zero timestamp vector and immediately clones it; transfer its ownership instead.',
    hotspot='History result initialization duplicates a temporary target buffer.'))
