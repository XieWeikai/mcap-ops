from common import *

RECIPES=[]


def add(op,fn,method,transform,lesson):
    RECIPES.append(candidate(op,TIME,fn,method,transform,lesson))


def strict_chunks(s,width):
    checks=' | '.join(f'(a[{i}] >= b[{i}])' for i in range(width))
    return body(s,'''    let bad = if times.len()<2 {false} else {
        let mut left=times[..times.len()-1].chunks_exact(@W@);
        let mut right=times[1..].chunks_exact(@W@);
        let mut bad=false;
        for (a,b) in left.by_ref().zip(right.by_ref()) {
            if @CHECK@ {bad=true;break;}
        }
        bad || left.remainder().iter().zip(right.remainder()).any(|(a,b)|a>=b)
    };
    if bad {return Err(invalid("source timestamps must be strictly increasing; inspect before resolving duplicates or reversals"));}
    Ok(())'''.replace('@W@',str(width)).replace('@CHECK@',checks))


for width in (4,8,16):
    add('require_strict','require_strict',f'check timestamp order in {width}-pair early-exit blocks',
        lambda s,w=width:strict_chunks(s,w),'Full-slice boolean reduction was slower; retain early exit between small fixed blocks.')
add('require_strict','require_strict','scan adjacent timestamp pairs in reverse order',
    lambda s:replace(s,'times.iter().zip(times.iter().skip(1)).any(|(a, b)| b <= a)',
        'times.windows(2).rev().any(|w| w[1] <= w[0])'),'Reverse streaming may improve late violation detection without changing the generic error.')
add('require_strict','require_strict','locate the first invalid timestamp pair explicitly',
    lambda s:replace(s,'times.iter().zip(times.iter().skip(1)).any(|(a, b)| b <= a)',
        'times.windows(2).position(|w| w[1] <= w[0]).is_some()'),'Measure position-based early-exit code generation; no checks are removed.')
add('require_strict','require_strict','check order with a scalar cursor',lambda s:body(s,'''    let mut i=1;
    while i<times.len() {
        if times[i]<=times[i-1] {return Err(invalid("source timestamps must be strictly increasing; inspect before resolving duplicates or reversals"));}
        i+=1;
    }
    Ok(())'''),'Keep branchy early exit rather than the rejected full reduction.')
add('require_strict','require_strict','use a fallible fold for timestamp order validation',lambda s:body(s,'''    times.iter().zip(times.iter().skip(1)).try_for_each(|(a,b)| {
        if b<=a {Err(invalid("source timestamps must be strictly increasing; inspect before resolving duplicates or reversals"))} else {Ok(())}
    })'''),'An alternative branch structure keeps the exact error contract.')
RECIPES += [hint('require_strict',TIME,'require_strict',k) for k in ('always','never')]
add('require_strict','require_strict','zip offset timestamp slices after a short-input guard',
    lambda s:replace(s,'times.iter().zip(times.iter().skip(1)).any(|(a, b)| b <= a)',
        'times.len() >= 2 && times[..times.len()-1].iter().zip(&times[1..]).any(|(a,b)| b<=a)'),
    'Slice offsets avoid the skip adaptor while preserving empty and singleton behavior.')


for capacity in (256,1024,4096):
    add('uniform_grid','uniform_grid',f'bound initial grid capacity at {capacity} points',
        lambda s,c=capacity:replace(s,'let mut result = Vec::new();',f'let mut result = Vec::with_capacity(max_points.min({c}));'),
        'Exact-capacity arithmetic failed the prior gate; sweep bounded growth budgets instead of allocating max_points.')
def grid_narrow(s):
    s=replace(s,'let fraction = period_num % rate;','let fraction = (period_num % rate) as u64;')
    s=replace(s,'let mut residual = rate / 2;','let rate = u64::from(rate_num);\n    let mut residual = rate / 2;')
    return s
add('uniform_grid','uniform_grid','keep rational-grid residual arithmetic in u64',grid_narrow,
    'The residual is below twice a u32 rate; wide timestamp arithmetic remains unchanged.')
add('uniform_grid','uniform_grid','advance the grid with a branchless rational carry',
    lambda s:replace(s,'''        if residual >= rate {
            t += 1;
            residual -= rate;
        }''','''        let carry=i128::from(residual>=rate);
        t+=carry;
        residual-=carry*rate;'''),'Measure branch removal only for bounded residuals, unlike the failed validation-wide reduction.')
def grid_integer(s):
    return replace(s,'    let mut residual = rate / 2;', '''    if fraction == 0 {
        let mut t=i128::from(start);
        while t<i128::from(end) {
            if result.len()==max_points {return Err(invalid("grid exceeds max_points"));}
            result.push(i64::try_from(t).map_err(|_| Error::Overflow)?);
            t+=whole;
        }
        return Ok(result);
    }
    let mut residual = rate / 2;''')
add('uniform_grid','uniform_grid','specialize integer-period grids before the recurrence',grid_integer,
    'The existing recurrence succeeded; test whether integer rates can omit residual work entirely.')
def grid_fill(s):
    s=replace(s,'    let mut result = Vec::new();','''    let count=(((i128::from(end)-i128::from(start))*rate-rate/2).max(0)+period_num-1)/period_num;
    if count>max_points as i128 {return Err(invalid("grid exceeds max_points"));}
    let mut result=vec![0;count as usize];''')
    a=s.index('    for i in 0..=max_points {')
    return s[:a]+'''    for value in &mut result {
        *value=i64::try_from(t).map_err(|_| Error::Overflow)?;
        t+=whole;residual+=fraction;
        if residual>=rate {t+=1;residual-=rate;}
    }
    Ok(result)
}'''
add('uniform_grid','uniform_grid','fill an exactly sized grid buffer without push checks',grid_fill,
    'The earlier reserve-only candidate failed; this also removes per-point length/capacity checks.')
RECIPES += [hint('uniform_grid',TIME,'uniform_grid',k) for k in ('always','never')]
def grid_while(s):
    s=replace(s,'    for i in 0..=max_points {','    loop {')
    s=replace(s,'if i == max_points {','if result.len() == max_points {')
    return replace(s,'    unreachable!()\n','')
add('uniform_grid','uniform_grid','terminate grid generation from output length and endpoint',grid_while,
    'Avoid a second loop counter while keeping the max_points error and half-open endpoint.')


add('map_clock','map_clock','copy clock-identity inputs directly',lambda s:replace(s,'    if rate_ppb == 0 {',
    '    if rate_ppb == 0 && offset == 0 {return Ok(times.to_vec());}\n    if rate_ppb == 0 {'),
    'The zero-drift fast path helped earlier; distinguish the frequent identity transform with an explicit benchmark.')
def clock_copy(s):
    a=s.index('        return times');b=s.index('    let scale',a)
    return s[:a]+'''        let mut result=times.to_vec();
        for value in &mut result {*value=value.checked_add(offset).ok_or(Error::Overflow)?;}
        return Ok(result);
    }
'''+s[b:]
add('map_clock','map_clock','apply pure clock offsets in a cloned output buffer',clock_copy,
    'In-place checked updates improved batch expansion; test that ownership strategy for clock offsets.')
def clock_bounds(s):
    a=s.index('        return times');b=s.index('    let scale',a)
    return s[:a]+'''        if let (Some(&low),Some(&high))=(times.iter().min(),times.iter().max()) {
            low.checked_add(offset).ok_or(Error::Overflow)?;
            high.checked_add(offset).ok_or(Error::Overflow)?;
        }
        return Ok(times.iter().map(|&t|t+offset).collect());
    }
'''+s[b:]
add('map_clock','map_clock','validate offset extrema once before vectorizable addition',clock_bounds,
    'Retain overflow detection for every possible input; measure an extrema prescan against per-element checked addition.')
def clock_push(s):
    a=s.index('    times\n        .iter()',s.index('    let scale'))
    s=s[:a]+s[a:].replace('    times\n        .iter()\n        .map(|&t| {','    let mut result=Vec::with_capacity(times.len());\n    for &t in times {',1)
    s=replace(s,'''            i64::try_from(i128::from(origin) + rounded + i128::from(offset))
                .map_err(|_| Error::Overflow)
        })
        .collect()''','''            result.push(i64::try_from(i128::from(origin) + rounded + i128::from(offset))
                .map_err(|_| Error::Overflow)?);
    }
    Ok(result)''')
    return s
add('map_clock','map_clock','reserve and push nonzero-drift clock outputs',clock_push,
    'Separate allocation strategy from the earlier rejected narrow-arithmetic algorithm.')
def clock_isolate(s):
    a=s.index('    let scale')
    return s[:a]+'''    #[inline(never)]
    fn drift(times:&[i64],origin:i64,offset:i64,rate_ppb:i64)->Result<Vec<i64>> {
'''+s[a:-1]+'''    }
    drift(times,origin,offset,rate_ppb)
}'''
add('map_clock','map_clock','isolate wide drift arithmetic from the offset fast path',clock_isolate,
    'Prior drift changes unexpectedly slowed offsets; separate code generation without altering arithmetic.')
add('map_clock','map_clock','hoist the clock output origin and offset sum',lambda s:replace(
    replace(s,'    times\n        .iter()', '    let output_origin=i128::from(origin)+i128::from(offset);\n    times\n        .iter()'),
    'i128::from(origin) + rounded + i128::from(offset)','output_origin + rounded'),
    'Keep i128 arithmetic but remove repeated invariant additions; differential edge cases cover overflow behavior.')
def clock_unsigned(s):
    old='''            let rounded = if delta >= 0 {
                (delta + 500_000_000) / 1_000_000_000
            } else {
                -((-delta + 500_000_000) / 1_000_000_000)
            };'''
    return replace(s,old,'''            let rounded = if let Some(magnitude)=delta.checked_abs().and_then(|v|v.checked_add(500_000_000)) {
                let q=(magnitude as u128/1_000_000_000) as i128;
                if delta<0 {-q} else {q}
            } else if delta>=0 {(delta+500_000_000)/1_000_000_000}
            else {-((-delta+500_000_000)/1_000_000_000)};''')
add('map_clock','map_clock','divide representable drift magnitudes as unsigned integers',clock_unsigned,
    'Do not reuse the rejected narrow-correction formula; retain the original overflow fallback and tie direction.')
RECIPES += [hint('map_clock',TIME,'map_clock',k) for k in ('always','never')]
def clock_blocks(s):
    a=s.index('        return times');b=s.index('    let scale',a)
    return s[:a]+'''        let mut result=times.to_vec();
        let mut chunks=result.chunks_exact_mut(4);
        for row in chunks.by_ref() {
            row[0]=row[0].checked_add(offset).ok_or(Error::Overflow)?;
            row[1]=row[1].checked_add(offset).ok_or(Error::Overflow)?;
            row[2]=row[2].checked_add(offset).ok_or(Error::Overflow)?;
            row[3]=row[3].checked_add(offset).ok_or(Error::Overflow)?;
        }
        for value in chunks.into_remainder() {*value=value.checked_add(offset).ok_or(Error::Overflow)?;}
        return Ok(result);
    }
'''+s[b:]
add('map_clock','map_clock','unroll pure offset updates in four-element blocks',clock_blocks,
    'Measure bounded loop unrolling separately from allocation and arithmetic changes.')


add('inspect_time','inspect_time','reserve the maximum positive-interval count',lambda s:replace(s,
    'let mut positive = Vec::new();','let mut positive = Vec::with_capacity(times.len().saturating_sub(1));'),
    'Keep the successful uniform fast path; bound fallback allocation by the actual input length.')
def time_two_bins(s):
    s=replace(s,'''    positive.sort_unstable();
    let median = quantile(&positive, 0.5);''','''    let minimum=positive.iter().min().copied();
    let maximum=positive.iter().max().copied();
    let two_bins=minimum.zip(maximum).filter(|&(lo,hi)|positive.iter().all(|&v|v==lo || v==hi));
    let (median,p95)=if let Some((lo,hi))=two_bins {
        let lows=positive.iter().filter(|&&v|v==lo).count();
        let q=|p:f64| {
            let index=(positive.len()-1) as f64*p;
            let a=if (index.floor() as usize)<lows {lo} else {hi} as f64;
            let b=if (index.ceil() as usize)<lows {lo} else {hi} as f64;
            Some(a+(b-a)*(index-index.floor()))
        };
        (q(0.5),q(0.95))
    } else {
        positive.sort_unstable();(quantile(&positive,0.5),quantile(&positive,0.95))
    };''')
    s=replace(s,'positive_interval_min_ns: positive.first().copied(),','positive_interval_min_ns: minimum,')
    s=replace(s,'positive_interval_max_ns: positive.last().copied(),','positive_interval_max_ns: maximum,')
    return replace(s,'positive_interval_p95_ns: quantile(&positive, 0.95),','positive_interval_p95_ns: p95,')
add('inspect_time','inspect_time','summarize two-valued interval distributions without sorting',time_two_bins,
    'Quickselect lost on low-cardinality jitter; explicitly exploit exactly two interval values and retain full-sort fallback.')
add('inspect_time','inspect_time','skip fallback sorting when intervals are already ordered',
    lambda s:replace(s,'    positive.sort_unstable();','    if !positive.is_sorted() {positive.sort_unstable();}'),
    'Measure an ordering check on nonuniform intervals rather than repeating the rejected percentile-selection algorithm.')
add('inspect_time','inspect_time','zip the uniform-clock comparison pass',
    lambda s:replace(s,'''times
                .windows(2)
                .all(|w| i128::from(w[1]) - i128::from(w[0]) == dt)''',
        '''times.iter().zip(times.iter().skip(1)).all(|(&a,&b)|i128::from(b)-i128::from(a)==dt)'''),
    'Zipped adjacency helped strict validation; apply it only to the established uniform fast path.')
add('inspect_time','inspect_time','zip interval statistics input pairs',lambda s:replace(
    replace(s,'for pair in times.windows(2) {','for (&a,&b) in times.iter().zip(times.iter().skip(1)) {'),
    'let dt = i128::from(pair[1]) - i128::from(pair[0]);','let dt = i128::from(b)-i128::from(a);'),
    'Preserve the exact positive interval and error semantics while changing fallback iteration.')
add('inspect_time','inspect_time','compare stable adaptive sorting for jitter statistics',lambda s:replace(s,
    'positive.sort_unstable();','positive.sort();'),'Ordered/repeated interval runs may favor a stable adaptive sort; measure instead of assuming quickselect is faster.')
def time_fill(s):
    s=replace(s,'let mut positive = Vec::new();','let mut positive=vec![0;times.len().saturating_sub(1)];\n    let mut used=0;')
    s=replace(s,'positive.push(i64::try_from(dt).map_err(|_| Error::Overflow)?);',
        'positive[used]=i64::try_from(dt).map_err(|_| Error::Overflow)?;\n            used+=1;')
    return replace(s,'    positive.sort_unstable();','    positive.truncate(used);\n    positive.sort_unstable();')
add('inspect_time','inspect_time','fill a bounded interval buffer then truncate it',time_fill,
    'Test removal of Vec push bookkeeping while retaining every duplicate, reversal and overflow check.')
RECIPES += [hint('inspect_time',TIME,'inspect_time',k) for k in ('always','never')]
add('inspect_time','quantile','specialize the exact median quantile index',lambda s:replace(s,'    let index =',
    '''    if q==0.5 {let n=sorted.len();return Some(if n.is_multiple_of(2) {
        sorted[n/2-1] as f64+(sorted[n/2] as f64-sorted[n/2-1] as f64)*0.5
    } else {sorted[n/2] as f64});}
    let index ='''),'Specialize median indexing after sorting; keep the same interpolation arithmetic for even counts.')


add('align_timestamps','align_timestamps','start alignment at the first relevant source prefix',
    lambda s:replace(s,'let mut next = 0;',
        'let mut next=target.first().map_or(0,|&t|source.partition_point(|&v|v<=t));'),
    'Prior output rewrites failed; avoid scanning an irrelevant initial source prefix and include sparse targets.')
add('align_timestamps','align_timestamps','binary-search only highly sparse target grids',
    lambda s:replace(s,'''        while next < source.len() && source[next] <= t {
            next += 1;
        }''','''        if target.len()<source.len()/64 {
            next=source.partition_point(|&v|v<=t);
        } else {
            while next<source.len() && source[next]<=t {next+=1;}
        }'''),'A monotone walk is best for dense grids; sparse MCAP queries can skip large spans.')
add('align_timestamps','align_timestamps','reuse alignment results for repeated targets',
    lambda s:replace(s,'    for (i, &t) in target.iter().enumerate() {',
    '''    for (i, &t) in target.iter().enumerate() {
        if i>0 && t==target[i-1] {
            result.indices[i]=result.indices[i-1];result.offsets_ns[i]=result.offsets_ns[i-1];result.valid[i]=result.valid[i-1];continue;
        }'''),'Target duplicates are valid; include a repeated-target case and preserve every output position.')
def align_distances(s):
    a=s.index('        let past =');b=s.index('        if let Some(index)',a)
    return s[:a]+'''        let past=next.checked_sub(1).map(|j|(j,i128::from(t)-i128::from(source[j])))
            .filter(|&(_,d)|d<=i128::from(max_past_ns));
        let future=(nearest && next<source.len()).then_some(next)
            .map(|j|(j,i128::from(source[j])-i128::from(t)))
            .filter(|&(_,d)|d<=i128::from(max_future_ns));
        let chosen=match(past,future) {
            (Some((a,da)),Some((b,db)))=>Some(if da<=db {a} else {b}),
            (Some((a,_)),None)=>Some(a),(None,Some((b,_)))=>Some(b),_=>None,
        };
'''+s[b:]
add('align_timestamps','align_timestamps','carry candidate distances through alignment selection',align_distances,
    'Compute each exact i128 distance once rather than recomputing it after tolerance filtering.')
def align_checked(s):
    s=replace(s,'i128::from(t) - i128::from(source[j]) <= i128::from(max_past_ns)',
        't.checked_sub(source[j]).is_some_and(|d|d<=max_past_ns)')
    return replace(s,'i128::from(source[j]) - i128::from(t) <= i128::from(max_future_ns)',
        'source[j].checked_sub(t).is_some_and(|d|d<=max_future_ns)')
add('align_timestamps','align_timestamps','use checked narrow differences for tolerance rejection',align_checked,
    'An overflowed positive distance necessarily exceeds an i64 tolerance; tie comparison stays wide.')
add('align_timestamps','align_timestamps','cast only offsets proven within signed tolerance',
    lambda s:replace(s,'''i64::try_from(i128::from(source[index]) - i128::from(t))
                .map_err(|_| Error::Overflow)?''','(i128::from(source[index])-i128::from(t)) as i64'),
    'A selected offset is bounded by a nonnegative i64 tolerance; retain the preceding checked selection.')
add('align_timestamps','align_timestamps','use the slice sortedness primitive for target validation',
    lambda s:replace(s,'target.windows(2).any(|w| w[1] < w[0])','!target.is_sorted()'),
    'Ordered targets permit equality; compare the library predicate without altering source strictness.')
RECIPES += [hint('align_timestamps',TIME,'align_timestamps',k) for k in ('always','never')]
add('align_timestamps','align_timestamps','advance alignment with a sliced lookahead iterator',
    lambda s:replace(s,'''        while next < source.len() && source[next] <= t {
            next += 1;
        }''','''        next+=source[next..].iter().take_while(|&&v|v<=t).count();'''),
    'Retain the monotone cursor while moving its end-bound checks into a borrowed slice.')


def batch_unroll(s,width):
    old='''        for value in &mut result[index..index + count] {
            *value = time.checked_add(*value).ok_or(Error::Overflow)?;
        }'''
    assigns='\n'.join(f'            row[{i}]=time.checked_add(row[{i}]).ok_or(Error::Overflow)?;' for i in range(width))
    return replace(s,old,f'''        let mut chunks=result[index..index+count].chunks_exact_mut({width});
        for row in chunks.by_ref() {{
{assigns}
        }}
        for value in chunks.into_remainder() {{*value=time.checked_add(*value).ok_or(Error::Overflow)?;}}''')
for width in (4,8):
    add('expand_batch_timestamps','expand_batch_timestamps',f'unroll checked batch addition by {width}',
        lambda s,w=width:batch_unroll(s,w),'The copied-buffer strategy succeeded; test bounded unrolling without changing overflow detection.')
def batch_fixed(s):
    return replace(s,'    let mut index = 0;', '''    if let Some(&width)=counts.first() {
        if width>0 && counts.iter().all(|&v|v==width) {
            for (&time,row) in message_times.iter().zip(result.chunks_exact_mut(width)) {
                for value in row {*value=time.checked_add(*value).ok_or(Error::Overflow)?;}
            }
            return Ok(result);
        }
    }
    let mut index = 0;''')
add('expand_batch_timestamps','expand_batch_timestamps','specialize batches with a common positive width',batch_fixed,
    'Nested sensor batches often have a fixed count; keep the general counts fallback and validation.')
def batch_split(s):
    s=replace(s,'    let mut index = 0;','    let mut remaining=result.as_mut_slice();')
    s=replace(s,'        for value in &mut result[index..index + count] {',
        '        let (row,tail)=remaining.split_at_mut(count);\n        remaining=tail;\n        for value in row {')
    return replace(s,'        index += count;','')
add('expand_batch_timestamps','expand_batch_timestamps','split the output tail once per batch',batch_split,
    'Replace cumulative index arithmetic with disjoint mutable slices of validated lengths.')
add('expand_batch_timestamps','expand_batch_timestamps','fallibly iterate each batch slice',
    lambda s:replace(s,'''        for value in &mut result[index..index + count] {
            *value = time.checked_add(*value).ok_or(Error::Overflow)?;
        }''','''        result[index..index+count].iter_mut().try_for_each(|value| {
            *value=time.checked_add(*value).ok_or(Error::Overflow)?;Ok(())
        })?;'''),'Compare iterator control flow on the accepted in-place implementation, rather than the old push path.')
def batch_overflow(s):
    return replace(s,'''        for value in &mut result[index..index + count] {
            *value = time.checked_add(*value).ok_or(Error::Overflow)?;
        }''','''        let mut overflow=0i64;
        for value in &mut result[index..index+count] {
            let sum=time.wrapping_add(*value);
            overflow|=(time^sum)&(*value^sum);
            *value=sum;
        }
        if overflow<0 {return Err(Error::Overflow);}''')
add('expand_batch_timestamps','expand_batch_timestamps','accumulate batch overflow flags while adding',batch_overflow,
    'Return the same overflow error before exposing any result; a local bit reduction may permit vectorization.')
add('expand_batch_timestamps','expand_batch_timestamps','skip additions for zero-origin message batches',
    lambda s:replace(s,'        for value in &mut result[index..index + count] {',
        '        if time==0 {index+=count;continue;}\n        for value in &mut result[index..index + count] {'),
    'The output already contains copied offsets, so a zero timestamp needs no arithmetic.')
RECIPES += [hint('expand_batch_timestamps',TIME,'expand_batch_timestamps',k) for k in ('always','never')]
add('expand_batch_timestamps','expand_batch_timestamps','zip original offsets with batch output slices',
    lambda s:replace(s,'''        for value in &mut result[index..index + count] {
            *value = time.checked_add(*value).ok_or(Error::Overflow)?;
        }''','''        for (value,&offset) in result[index..index+count].iter_mut().zip(&offsets[index..index+count]) {
            *value=time.checked_add(offset).ok_or(Error::Overflow)?;
        }'''),'Measure separate immutable reads and mutable writes while retaining checked addition.')
