from common import *

RECIPES=[]
def add(op,fn,method,transform,lesson):RECIPES.append(candidate(op,SELECT,fn,method,transform,lesson))


def new_dedup(s):
    a=s.index('        let mut merged:')
    return s[:a]+'''        intervals.dedup_by(|current,previous| {
            if current.start_ns<=previous.end_ns {
                previous.end_ns=previous.end_ns.max(current.end_ns);true
            } else {false}
        });
        Ok(Self{intervals})
    }'''
add('interval_new','new','coalesce intervals with Vec deduplication',new_dedup,
    'The earlier manual in-place merge lost; test the library compaction implementation instead.')
add('interval_new','new','order equal-start intervals by their ends',lambda s:replace(s,
    'intervals.sort_unstable_by_key(|v| v.start_ns);','intervals.sort_unstable_by_key(|v| (v.start_ns,v.end_ns));'),
    'Tie ordering may change merge locality without changing the canonical union.')
add('interval_new','new','use stable adaptive interval sorting',lambda s:replace(s,
    'intervals.sort_unstable_by_key(|v| v.start_ns);','intervals.sort_by_key(|v| v.start_ns);'),
    'Already ordered interval runs may favor adaptive stable sorting; preserve merging semantics.')
for cap in (128,512,2048):
    add('interval_new','new',f'bound initial merge capacity to {cap} intervals',
        lambda s,c=cap:replace(s,'let mut merged: Vec<Interval> = Vec::new();',f'let mut merged: Vec<Interval> = Vec::with_capacity(intervals.len().min({c}));'),
        'Exact input-sized reservation failed earlier; measure bounded capacity sweeps with eventual growth intact.')
add('interval_new','new','return already canonical interval buffers without copying',lambda s:replace(s,
    '        intervals.sort_unstable_by_key',
    '''        if intervals.windows(2).all(|w|w[0].end_ns<w[1].start_ns) {return Ok(Self{intervals});}
        intervals.sort_unstable_by_key'''),
    'The old sortedness-only check still copied all intervals; this verifies non-overlap and transfers the owned buffer.')
RECIPES += [hint('interval_new',SELECT,'new',k) for k in ('always','never')]
def new_pending(s):
    a=s.index('        let mut merged:')
    return s[:a]+'''        let mut merged=Vec::new();
        let mut pending:Option<Interval>=None;
        for interval in intervals {
            match pending.as_mut() {
                Some(last) if interval.start_ns<=last.end_ns => last.end_ns=last.end_ns.max(interval.end_ns),
                _ => {if let Some(last)=pending.replace(interval) {merged.push(last);}},
            }
        }
        if let Some(last)=pending {merged.push(last);}
        Ok(Self{intervals:merged})
    }'''
add('interval_new','new','keep the active merge interval in a local slot',new_pending,
    'Avoid repeatedly borrowing the output vector tail during merging; retain one active interval and original order.')


add('interval_contains','contains','use binary search on interval start keys',lambda s:change_between(s,
    '        let i =','    }','''        let i=match self.intervals.binary_search_by_key(&t,|v|v.start_ns) {
            Ok(i)=>return t<self.intervals[i].end_ns,Err(i)=>i,
        };
        i>0 && t<self.intervals[i-1].end_ns
'''),'Compare the binary-search primitive while keeping the successful outer extent rejection.')
def contains_manual(s,unroll):
    a=s.index('        let i =')
    step='''            if low<high {let middle=low+(high-low)/2;
                if self.intervals[middle].start_ns<=t {low=middle+1;} else {high=middle;}}
'''
    return s[:a]+'''        let (mut low,mut high)=(0,self.intervals.len());
        while low<high {
'''+step*unroll+'''        }
        low>0 && t<self.intervals[low-1].end_ns
    }'''
add('interval_contains','contains','walk binary-search bounds explicitly',lambda s:contains_manual(s,1),
    'Measure explicit bounds against the partition_point implementation on both small and large sets.')
add('interval_contains','contains','partition interval end times before checking the start',
    lambda s:change_between(s,'        let i =','    }','''        let i=self.intervals.partition_point(|v|v.end_ns<=t);
        self.intervals.get(i).is_some_and(|v|v.start_ns<=t)
'''),'The half-open endpoint can select the candidate directly in canonical disjoint sets.')
for n in (2,4):
    add('interval_contains','contains',f'unroll interval binary search by {n} steps',lambda s,n=n:contains_manual(s,n),
        'Measure bounded branch scheduling rather than reintroducing the previously rejected extent changes.')
add('interval_contains','contains','binary-search by complete interval containment',lambda s:change_between(s,
    '        let i =','    }','''        self.intervals.binary_search_by(|v| {
            if t<v.start_ns {std::cmp::Ordering::Greater}
            else if t>=v.end_ns {std::cmp::Ordering::Less}
            else {std::cmp::Ordering::Equal}
        }).is_ok()
'''),'Use one search result to decide membership instead of re-indexing a predecessor.')
add('interval_contains','contains','linearly search small interval sets after extent rejection',
    lambda s:replace(s,'        let i =',
        '        if self.intervals.len()<=16 {return self.intervals.iter().any(|v|v.start_ns<=t && t<v.end_ns);}\n        let i ='),
    'Small sets have different branch costs; a dedicated fixed small-set benchmark prevents extrapolation.')
RECIPES += [hint('interval_contains',SELECT,'contains',k) for k in ('always','never')]
add('interval_contains','contains','load outer interval bounds together',lambda s:change_between(s,
    '        if self.intervals.first()','        let i =','''        let Some((first,last))=self.intervals.first().zip(self.intervals.last()) else {return false;};
        if t<first.start_ns || t>=last.end_ns {return false;}
'''),'Preserve extent rejection while reducing repeated optional access to the interval slice.')


add('interval_mask','mask','seed the mask cursor with a prefix search',lambda s:replace(s,
    'let mut index = 0;','let mut index=times.first().map_or(0,|&t|self.intervals.partition_point(|v|v.end_ns<=t));'),
    'The prior linear sweep helped; late query grids can skip an irrelevant prefix once.')
def mask_collect(s):
    a=s.index('        let mut result =')
    return s[:a]+'''        let mut index=0;
        times.iter().map(|&t| {
            while index<self.intervals.len() && self.intervals[index].end_ns<=t {index+=1;}
            index<self.intervals.len() && self.intervals[index].start_ns<=t
        }).collect()
    }'''
add('interval_mask','mask','collect ordered masks through an exact-size iterator',mask_collect,
    'The old prefilled-vector variant failed; test iterator collection with the successful monotone cursor.')
add('interval_mask','mask','recognize empty interval masks before ordering checks',lambda s:replace(s,
    '        if times.windows(2)', '        if self.intervals.is_empty() {return vec![false;times.len()];}\n        if times.windows(2)'),
    'No quality exclusions is a common empty-set case; avoid scanning target order when every answer is false.')
add('interval_mask','mask','use the slice sortedness primitive for mask dispatch',lambda s:replace(s,
    'times.windows(2).any(|w| w[1] < w[0])','!times.is_sorted()'),
    'Keep the original unordered-query fallback; compare only dispatch code generation.')
def mask_fill_runs(s):
    a=s.index('        let mut result =')
    return s[:a]+'''        let mut result=vec![false;times.len()];
        let mut cursor=0;
        for interval in &self.intervals {
            cursor+=times[cursor..].partition_point(|&t|t<interval.start_ns);
            let end=cursor+times[cursor..].partition_point(|&t|t<interval.end_ns);
            result[cursor..end].fill(true);cursor=end;
            if cursor==times.len() {break;}
        }
        result
    }'''
add('interval_mask','mask','fill interval-aligned runs in the mask output',mask_fill_runs,
    'Bulk boolean fills may reduce per-target work for dense runs; unordered targets retain independent membership checks.')
def mask_cached(s):
    return replace(s,'return times.iter().map(|&t| self.contains(t)).collect();','''let mut last:Option<(i64,bool)>=None;
            return times.iter().map(|&t| {
                if let Some((prior,value))=last {if prior==t {return value;}}
                let value=self.contains(t);last=Some((t,value));value
            }).collect();''')
add('interval_mask','mask','reuse consecutive unordered duplicate membership queries',mask_cached,
    'Reuse only identical input timestamps, never infer temporal ordering in the unordered fallback.')
def mask_repeat(s):
    s=replace(s,'        for &t in times {','''        for (i,&t) in times.iter().enumerate() {
            if i>0 && t==times[i-1] {result.push(result[i-1]);continue;}''')
    return s
add('interval_mask','mask','reuse repeated ordered mask answers',mask_repeat,
    'The repeat branch preserves one output per query and does not collapse timestamps.')
RECIPES += [hint('interval_mask',SELECT,'mask',k) for k in ('always','never')]
def mask_peek(s):
    a=s.index('        let mut result =')
    return s[:a]+'''        let mut intervals=self.intervals.iter().peekable();
        times.iter().map(|&t| {
            while intervals.peek().is_some_and(|v|v.end_ns<=t) {intervals.next();}
            intervals.peek().is_some_and(|v|v.start_ns<=t)
        }).collect()
    }'''
add('interval_mask','mask','walk mask intervals with a peekable iterator',mask_peek,
    'Replace indexed sweep bounds with a cached next-interval reference; preserve original query order.')


def intersection_skip(s,threshold):
    return replace(s,'            let a = self.intervals[i];',f'''            if i+{threshold}<self.intervals.len() && self.intervals[i+{threshold}].end_ns<=other.intervals[j].start_ns {{
                i+=self.intervals[i..].partition_point(|v|v.end_ns<=other.intervals[j].start_ns);
                if i==self.intervals.len() {{break;}}
            }}
            if j+{threshold}<other.intervals.len() && other.intervals[j+{threshold}].end_ns<=self.intervals[i].start_ns {{
                j+=other.intervals[j..].partition_point(|v|v.end_ns<=self.intervals[i].start_ns);
                if j==other.intervals.len() {{break;}}
            }}
            let a = self.intervals[i];''')
for threshold in (4,16,64):
    add('interval_intersection','intersection',f'skip disjoint interior prefixes beyond {threshold} intervals',
        lambda s,n=threshold:intersection_skip(s,n),'Conditional initial skipping helped; interior skipping must also preserve dense-case throughput.')
add('interval_intersection','intersection','advance both intersection cursors at equal ends',lambda s:replace(s,
    '''            if a.end_ns < b.end_ns {
                i += 1;
            } else {
                j += 1;
            }''','''            i+=usize::from(a.end_ns<=b.end_ns);
            j+=usize::from(b.end_ns<=a.end_ns);'''),
    'Equal endpoints need no second empty comparison; measure a branchless dual-cursor update.')
for cap in (64,512):
    add('interval_intersection','intersection',f'bound initial intersection output capacity at {cap}',
        lambda s,c=cap:replace(s,'let mut result = Vec::new();',f'let mut result = Vec::with_capacity((self.intervals.len()+other.intervals.len()).min({c}));'),
        'Input-sized reservation previously regressed; test small bounded capacities across dense and late overlap.')
add('interval_intersection','intersection','return immediately for globally disjoint sets',lambda s:replace(s,
    '        let (mut i, mut j) =', '''        if self.intervals.last().zip(other.intervals.first()).is_some_and(|(a,b)|a.end_ns<=b.start_ns)
            || other.intervals.last().zip(self.intervals.first()).is_some_and(|(b,a)|b.end_ns<=a.start_ns) {return Self::default();}
        let (mut i, mut j) ='''),
    'Outer bounds can prove no overlap without constructing or walking output intervals.')
RECIPES += [hint('interval_intersection',SELECT,'intersection',k) for k in ('always','never')]
def intersection_peek(s):
    a=s.index('        let mut result =')
    return s[:a]+'''        let mut left=self.intervals[i..].iter().peekable();
        let mut right=other.intervals[j..].iter().peekable();
        let mut result=Vec::new();
        while let (Some(a),Some(b))=(left.peek().copied(),right.peek().copied()) {
            let start_ns=a.start_ns.max(b.start_ns);let end_ns=a.end_ns.min(b.end_ns);
            if start_ns<end_ns {result.push(Interval{start_ns,end_ns});}
            if a.end_ns<b.end_ns {left.next();} else {right.next();}
        }
        Self{intervals:result}
    }'''
add('interval_intersection','intersection','merge intersection tails through peekable iterators',intersection_peek,
    'Keep the accepted initial prefix search; replace only the subsequent indexed merge walk.')


add('interval_difference','difference','clone the input when exclusions are empty',lambda s:replace(s,
    '        let mut result =','        if other.intervals.is_empty() {return self.clone();}\n        let mut result ='),
    'An empty exclusion set is an identity transformation; include it as an explicit benchmark.')
add('interval_difference','difference','clone globally disjoint interval differences',lambda s:replace(s,
    '        let mut result =', '''        if self.intervals.last().zip(other.intervals.first()).is_some_and(|(a,b)|a.end_ns<=b.start_ns)
            || other.intervals.last().zip(self.intervals.first()).is_some_and(|(b,a)|b.end_ns<=a.start_ns) {return self.clone();}
        let mut result ='''),
    'Retain the linear difference algorithm while detecting identity results from global bounds.')
add('interval_difference','difference','seed the exclusion cursor by prefix search',lambda s:replace(s,
    'let mut j = 0;','let mut j=self.intervals.first().map_or(0,|a|other.intervals.partition_point(|b|b.end_ns<=a.start_ns));'),
    'Avoid an irrelevant leading exclusion prefix without restarting searches for each input interval.')
def difference_get(s):
    return replace(s,'''            while k < other.intervals.len() && other.intervals[k].start_ns < a.end_ns {
                let b = other.intervals[k];''','''            while let Some(b)=other.intervals.get(k).filter(|b|b.start_ns<a.end_ns) {''')
add('interval_difference','difference','combine exclusion bounds checks and interval access',difference_get,
    'Read each next exclusion through one optional slice access instead of separate bounds and indexing.')
for divisor in (0,2,4):
    cap='self.intervals.len()' if divisor==0 else f'self.intervals.len()+other.intervals.len()/{divisor}'
    add('interval_difference','difference',f'reserve difference storage with exclusion fraction {0 if divisor==0 else 1/divisor}',
        lambda s,c=cap:replace(s,'self.intervals.len() + other.intervals.len()',c),
        'The full upper-bound reserve helped earlier; tune wasted capacity while retaining normal vector growth.')
RECIPES += [hint('interval_difference',SELECT,'difference',k) for k in ('always','never')]
def difference_peek(s):
    return body(s,'''        let mut result=Vec::with_capacity(self.intervals.len()+other.intervals.len());
        let mut exclusions=other.intervals.iter().peekable();
        for a in &self.intervals {
            while exclusions.peek().is_some_and(|b|b.end_ns<=a.start_ns) {exclusions.next();}
            let mut cursor=a.start_ns;
            while let Some(b)=exclusions.peek().copied().filter(|b|b.start_ns<a.end_ns) {
                if cursor<b.start_ns {result.push(Interval{start_ns:cursor,end_ns:b.start_ns});}
                cursor=cursor.max(b.end_ns);
                if cursor>=a.end_ns {break;}
                exclusions.next();
            }
            if cursor<a.end_ns {result.push(Interval{start_ns:cursor,end_ns:a.end_ns});}
        }
        Self{intervals:result}''')
add('interval_difference','difference','use one persistent exclusion iterator for differences',difference_peek,
    'The previous monotone cursor fixed quadratic work; keep that complexity while eliminating separate j/k indices.')


add('interval_affected_centers','affected_centers','return unchanged intervals for zero context',lambda s:replace(s,
    '        let mut merged:', '        if history_ns==0 && future_ns==0 {return Ok(self.clone());}\n        let mut merged:'),
    'Identity context expansion needs no per-interval arithmetic; keep validation of negative context first.')
def affected_bounds(s):
    anchor='        let mut merged:'
    s=replace(s,anchor,'''        if let (Some(lo),Some(hi))=(self.intervals.iter().map(|v|v.start_ns).min(),self.intervals.iter().map(|v|v.end_ns).max()) {
            lo.checked_sub(future_ns).ok_or(Error::Overflow)?;
            hi.checked_add(history_ns).ok_or(Error::Overflow)?;
        }
'''+anchor)
    s=replace(s,'v.start_ns.checked_sub(future_ns).ok_or(Error::Overflow)?','v.start_ns-future_ns')
    return replace(s,'v.end_ns.checked_add(history_ns).ok_or(Error::Overflow)?','v.end_ns+history_ns')
add('interval_affected_centers','affected_centers','prevalidate context arithmetic against global extrema',affected_bounds,
    'Check all extrema, not just endpoints, then perform equivalent bounded additions in the merge loop.')
def affected_dedup(s):
    a=s.index('        let mut merged:')
    return s[:a]+'''        let mut intervals=self.intervals.clone();
        for v in &mut intervals {
            v.start_ns=v.start_ns.checked_sub(future_ns).ok_or(Error::Overflow)?;
            v.end_ns=v.end_ns.checked_add(history_ns).ok_or(Error::Overflow)?;
        }
        intervals.dedup_by(|current,previous| {
            if current.start_ns<=previous.end_ns {previous.end_ns=previous.end_ns.max(current.end_ns);true} else {false}
        });
        Ok(Self{intervals})
    }'''
add('interval_affected_centers','affected_centers','compact expanded intervals in the cloned input buffer',affected_dedup,
    'Reuse owned storage via library compaction rather than re-sorting expanded intervals.')
def affected_pending(s):
    a=s.index('        let mut merged:')
    return s[:a]+'''        let mut merged=Vec::with_capacity(self.intervals.len());
        let mut pending:Option<Interval>=None;
        for v in &self.intervals {
            let interval=Interval{start_ns:v.start_ns.checked_sub(future_ns).ok_or(Error::Overflow)?,
                end_ns:v.end_ns.checked_add(history_ns).ok_or(Error::Overflow)?};
            match pending.as_mut() {
                Some(last) if interval.start_ns<=last.end_ns => last.end_ns=last.end_ns.max(interval.end_ns),
                _ => {if let Some(last)=pending.replace(interval) {merged.push(last);}},
            }
        }
        if let Some(last)=pending {merged.push(last);}
        Ok(Self{intervals:merged})
    }'''
add('interval_affected_centers','affected_centers','keep the expanding merge frontier in a local slot',affected_pending,
    'Use one active interval to avoid repeated output-tail access without changing chronological merging.')
add('interval_affected_centers','affected_centers','check context endpoints with wide arithmetic',lambda s:replace(replace(s,
    'v.start_ns.checked_sub(future_ns).ok_or(Error::Overflow)?',
    'i64::try_from(i128::from(v.start_ns)-i128::from(future_ns)).map_err(|_|Error::Overflow)?'),
    'v.end_ns.checked_add(history_ns).ok_or(Error::Overflow)?',
    'i64::try_from(i128::from(v.end_ns)+i128::from(history_ns)).map_err(|_|Error::Overflow)?'),
    'Measure arithmetic lowering while retaining exact overflow behavior for extreme timestamps.')
for cap in (16,256):
    add('interval_affected_centers','affected_centers',f'reserve {cap} intervals when the first expanded pair overlaps',
        lambda s,c=cap:replace(s,'Vec::with_capacity(self.intervals.len())',f'''Vec::with_capacity(if self.intervals.get(1).is_some_and(|next|
            i128::from(self.intervals[0].end_ns)+i128::from(history_ns)>=i128::from(next.start_ns)-i128::from(future_ns)) {{self.intervals.len().min({c})}} else {{self.intervals.len()}})'''),
        'Expanded contexts may merge thousands of exclusions into one; include merged and unmerged workloads.')
RECIPES += [hint('interval_affected_centers',SELECT,'affected_centers',k) for k in ('always','never')]
add('interval_affected_centers','affected_centers','merge context expansion through a fallible fold',lambda s:change_between(s,
    '        let mut merged:', '        Ok(Self { intervals: merged })','''        let merged=self.intervals.iter().try_fold(Vec::<Interval>::with_capacity(self.intervals.len()),|mut merged,v| {
            let interval=Interval{start_ns:v.start_ns.checked_sub(future_ns).ok_or(Error::Overflow)?,end_ns:v.end_ns.checked_add(history_ns).ok_or(Error::Overflow)?};
            if let Some(last)=merged.last_mut() {if interval.start_ns<=last.end_ns {last.end_ns=last.end_ns.max(interval.end_ns);return Ok(merged);}}
            merged.push(interval);Ok::<_,Error>(merged)
        })?;
'''),'Retain a single ordered pass and the successful capacity bound while testing ownership-aware fold code generation.')
