"""Small pre-reviewed RSI candidates. Every candidate still needs measurement."""
import re


def replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"expected one occurrence: {old[:100]!r}")
    return text.replace(old, new, 1)


def strict1(s):
    return replace(s, "times.windows(2).any(|w| w[1] <= w[0])",
                   "times.iter().zip(times.iter().skip(1)).any(|(a,b)|b<=a)")


def strict2(s):
    start = s.index("if ")
    end = s.index(" {", start)
    return s[:start] + "if !times.windows(2).fold(true, |valid,w|valid & (w[1]>w[0]))" + s[end:]


def grid1(s):
    return replace(s, "let mut result = Vec::new();",
        "let estimate = ((i128::from(end)-i128::from(start))*rate+period_num-1)/period_num;\n"
        "let mut result = Vec::with_capacity(estimate.min(max_points as i128) as usize);")


def grid2(s):
    a = s.index("    for i in 0..=max_points")
    return s[:a] + '''    let whole = period_num / rate;
    let fraction = period_num % rate;
    let mut residual = rate / 2;
    let mut t = i128::from(start);
    for i in 0..=max_points {
        if t >= i128::from(end) { return Ok(result); }
        if i == max_points { return Err(invalid("grid exceeds max_points")); }
        result.push(i64::try_from(t).map_err(|_| Error::Overflow)?);
        t += whole;
        residual += fraction;
        if residual >= rate { t += 1; residual -= rate; }
    }
    unreachable!()
}'''


def clock1(s):
    a = s.index("    times\n")
    return s[:a] + '''    let mut result = Vec::with_capacity(times.len());
    for &t in times {
        let delta = (i128::from(t) - i128::from(origin)) * scale;
        let rounded = if delta >= 0 {(delta + 500_000_000)/1_000_000_000}
            else {-((-delta + 500_000_000)/1_000_000_000)};
        result.push(i64::try_from(i128::from(origin)+rounded+i128::from(offset)).map_err(|_|Error::Overflow)?);
    }
    Ok(result)
}'''


def clock2(s):
    anchor = "    let scale ="
    return replace(s, anchor, '''    if rate_ppb == 0 {
        return times.iter().map(|&t|t.checked_add(offset).ok_or(Error::Overflow)).collect();
    }
    let scale =''')


def time1(s):
    return replace(s, "let mut positive = Vec::new();",
                   "let mut positive = Vec::with_capacity(times.len().saturating_sub(1));")


def time2(s):
    anchor = "    let mut positive ="
    return replace(s, anchor, '''    if times.len() >= 2 {
        let dt = i128::from(times[1]) - i128::from(times[0]);
        if dt > 0 && times.windows(2).all(|w|i128::from(w[1])-i128::from(w[0])==dt) {
            let dt = i64::try_from(dt).map_err(|_|Error::Overflow)?;
            return Ok(TimeStats {
                samples:times.len(), first_ns:times.first().copied(), last_ns:times.last().copied(),
                reversals:0, duplicates:0,
                gaps:if dt > max_gap_ns {times.len()-1} else {0},
                positive_interval_min_ns:Some(dt),positive_interval_median_ns:Some(dt as f64),
                positive_interval_p95_ns:Some(dt as f64),positive_interval_max_ns:Some(dt),
                estimated_hz:Some(1e9/dt as f64),
            });
        }
    }
    let mut positive =''')


def align1(s):
    s = s.replace("vec![-1; target.len()]", "Vec::with_capacity(target.len())")
    s = s.replace("vec![0; target.len()]", "Vec::with_capacity(target.len())")
    s = s.replace("vec![false; target.len()]", "Vec::with_capacity(target.len())")
    s = replace(s, "for (i, &t) in target.iter().enumerate()", "for &t in target")
    start = s.index("        if let Some(index) = chosen")
    end = s.index("    Ok(result)", start)
    return s[:start] + '''        if let Some(index) = chosen {
            result.indices.push(index as i64);
            result.offsets_ns.push(i64::try_from(i128::from(source[index])-i128::from(t)).map_err(|_|Error::Overflow)?);
            result.valid.push(true);
        } else {
            result.indices.push(-1);result.offsets_ns.push(0);result.valid.push(false);
        }
    }
''' + s[end:]


def align2(s):
    s = replace(s, "i128::from(t) - i128::from(source[j]) <= i128::from(max_past_ns)",
                "t.abs_diff(source[j]) <= max_past_ns as u64")
    s = replace(s, "i128::from(source[j]) - i128::from(t) <= i128::from(max_future_ns)",
                "source[j].abs_diff(t) <= max_future_ns as u64")
    return replace(s, "i128::from(t) - i128::from(source[a]) <= i128::from(source[b]) - i128::from(t)",
                   "t.abs_diff(source[a]) <= source[b].abs_diff(t)")


def batch1(s):
    return replace(s, '''        for &offset in &offsets[index..index + count] {
            result.push(time.checked_add(offset).ok_or(Error::Overflow)?);
        }''', '''        for value in offsets[index..index+count].iter().map(|&offset|time.checked_add(offset).ok_or(Error::Overflow)) {
            result.push(value?);
        }''')


def batch2(s):
    a = s.index("        for ", s.index("    for (&time, &count)"))
    b = s.index("        index += count;", a)
    return s[:a] + '''        let batch = &offsets[index..index+count];
        if let (Some(&low), Some(&high)) = (batch.iter().min(),batch.iter().max()) {
            time.checked_add(low).ok_or(Error::Overflow)?;
            time.checked_add(high).ok_or(Error::Overflow)?;
            result.extend(batch.iter().map(|&offset|time+offset));
        }
''' + s[b:]


def new1(s):
    return replace(s,"let mut merged: Vec<Interval> = Vec::new();",
                   "let mut merged: Vec<Interval> = Vec::with_capacity(intervals.len());")


def new2(s):
    return replace(s,"intervals.sort_unstable_by_key(|v| v.start_ns);",
        "if !intervals.windows(2).all(|w|w[0].start_ns<=w[1].start_ns) { intervals.sort_unstable_by_key(|v| v.start_ns); }")


def contains1(s):
    return replace(s,"        let i =",'''        if self.intervals.first().is_none_or(|v|t<v.start_ns)
            || self.intervals.last().is_some_and(|v|t>=v.end_ns) {return false;}
        let i =''')


def contains2(s):
    a=s.index("        let i =")
    return s[:a]+'''        self.intervals.binary_search_by(|v|{
            if t<v.start_ns {std::cmp::Ordering::Greater}
            else if t>=v.end_ns {std::cmp::Ordering::Less}
            else {std::cmp::Ordering::Equal}
        }).is_ok()
    }'''


def mask1(s):
    return '''pub fn mask(&self,times:&[i64])->Vec<bool> {
        if times.windows(2).any(|w|w[1]<w[0]) {
            return times.iter().map(|&t|self.contains(t)).collect();
        }
        let mut result=Vec::with_capacity(times.len());let mut index=0;
        for &t in times {
            while index<self.intervals.len() && self.intervals[index].end_ns<=t {index+=1;}
            result.push(index<self.intervals.len() && self.intervals[index].start_ns<=t);
        }
        result
    }'''


def mask2(s):
    # Same ordered sweep, but fill a pre-sized output rather than pushing.
    candidate=mask1(s)
    candidate=candidate.replace("Vec::with_capacity(times.len())", "vec![false;times.len()]")
    candidate=candidate.replace("for &t in times {", "for (value,&t) in result.iter_mut().zip(times) {")
    candidate=candidate.replace("result.push(index<self.intervals.len() && self.intervals[index].start_ns<=t);",
                                "*value=index<self.intervals.len() && self.intervals[index].start_ns<=t;")
    return candidate


def intersection1(s):
    return replace(s,"let mut result = Vec::new();",
        "let mut result = Vec::with_capacity(self.intervals.len().max(other.intervals.len()));")


def intersection2(s):
    return replace(s,"let (mut i, mut j) = (0, 0);",'''let mut i=other.intervals.first().map_or(self.intervals.len(),
            |b|self.intervals.partition_point(|a|a.end_ns<=b.start_ns));
        let mut j=self.intervals.get(i).map_or(other.intervals.len(),
            |a|other.intervals.partition_point(|b|b.end_ns<=a.start_ns));''')


def difference1(s):
    return '''pub fn difference(&self,other:&Self)->Self {
        let mut result=Vec::new();let mut j=0;
        for a in &self.intervals {
            while j<other.intervals.len() && other.intervals[j].end_ns<=a.start_ns {j+=1;}
            let mut cursor=a.start_ns;let mut k=j;
            while k<other.intervals.len() && other.intervals[k].start_ns<a.end_ns {
                let b=other.intervals[k];
                if cursor<b.start_ns {result.push(Interval{start_ns:cursor,end_ns:b.start_ns});}
                cursor=cursor.max(b.end_ns);
                if cursor>=a.end_ns {break;}
                k+=1;
            }
            if cursor<a.end_ns {result.push(Interval{start_ns:cursor,end_ns:a.end_ns});}
            j=k;
        }
        Self{intervals:result}
    }'''


def difference2(s):
    return replace(s,"let mut result = Vec::new();",
        "let mut result = Vec::with_capacity(self.intervals.len()+other.intervals.len());")


def affected1(s):
    a=s.index("        Self::new(")
    return s[:a]+'''        let mut result=Vec::with_capacity(self.intervals.len());
        for v in &self.intervals {
            result.push(Interval{
                start_ns:v.start_ns.checked_sub(future_ns).ok_or(Error::Overflow)?,
                end_ns:v.end_ns.checked_add(history_ns).ok_or(Error::Overflow)?,
            });
        }
        Self::new(result)
    }'''


def affected2(s):
    a=s.index("        ",s.index("return Err("))
    # Preserve the checked argument guard, replace only construction.
    guard_end=s.index("\n        }",s.index("if history_ns"))+len("\n        }")
    return s[:guard_end]+'''
        let mut merged:Vec<Interval>=Vec::with_capacity(self.intervals.len());
        for v in &self.intervals {
            let interval=Interval{
                start_ns:v.start_ns.checked_sub(future_ns).ok_or(Error::Overflow)?,
                end_ns:v.end_ns.checked_add(history_ns).ok_or(Error::Overflow)?,
            };
            if let Some(last)=merged.last_mut() {
                if interval.start_ns<=last.end_ns {last.end_ns=last.end_ns.max(interval.end_ns);continue;}
            }
            merged.push(interval);
        }
        Ok(Self{intervals:merged})
    }'''


def recipe(op,file,function,cases,r1,r2,hotspot,methods):
    return dict(operator=op,path=file,function=function,cases=cases,rounds=[r1,r2],
                hotspot=hotspot,methods=methods,complexity="Small safe-Rust local change; unchanged interface and validation; no dependency or unsafe code")


TIME="crates/core/src/time.rs"
SELECTION="crates/core/src/selection.rs"
RECIPES=[
    recipe("require_strict",TIME,"require_strict","require_strict",strict1,strict2,
           "Validation performs a branch for every adjacent timestamp",
           ["zip adjacent timestamp iterators","use a vectorizable complete ordering reduction"]),
    recipe("uniform_grid",TIME,"uniform_grid","uniform_grid.integer,uniform_grid.rational",grid1,grid2,
           "Repeated Vec growth and per-point integer division in rational grid generation",
           ["reserve the bounded grid size","advance rational timestamps with quotient and remainder"]),
    recipe("map_clock",TIME,"map_clock","map_clock.offset,map_clock.drift",clock1,clock2,
           "Fallible collection grows Vec and applies wide division even to pure offsets",
           ["reserve clock-map output capacity","fast-path explicitly zero clock drift"]),
    recipe("inspect_time",TIME,"inspect_time","inspect_time.uniform,inspect_time.jitter",time1,time2,
           "Interval collection and ordering dominate time-statistic work",
           ["reserve interval storage","summarize exactly uniform timestamps without allocating intervals"]),
    recipe("align_timestamps",TIME,"align_timestamps","align_timestamps.previous,align_timestamps.nearest",align1,align2,
           "Output initialization and wide signed distance checks in the matching loop",
           ["build alignment outputs in one pass","use overflow-safe unsigned timestamp distances"]),
    recipe("expand_batch_timestamps",TIME,"expand_batch_timestamps","expand_batch_timestamps",batch1,batch2,
           "Checked per-sample addition and Vec push inside each known batch",
           ["express batch expansion as checked mapped iteration","check batch extrema before vectorizable additions"]),
    recipe("interval_new",SELECTION,"new","interval_new",new1,new2,
           "Repeated allocation and unnecessary sorting of already ordered intervals",
           ["reserve interval merge capacity","skip sorting already ordered interval starts"]),
    recipe("interval_contains",SELECTION,"contains","interval_contains",contains1,contains2,
           "Binary membership search includes queries outside the entire interval extent",
           ["reject queries outside the interval extent early","search disjoint interval containment directly"]),
    recipe("interval_mask",SELECTION,"mask","interval_mask.ordered,interval_mask.shuffled",mask1,mask2,
           "Each ordered query repeats a binary search through the same intervals",
           ["sweep ordered timestamp masks with a monotone cursor","write ordered masks into pre-sized output"]),
    recipe("interval_intersection",SELECTION,"intersection","interval_intersection.dense,interval_intersection.late",intersection1,intersection2,
           "Intersection grows outputs and scans non-overlapping leading intervals",
           ["reserve intersection output capacity","skip non-overlapping prefixes before intersection"]),
    recipe("interval_difference",SELECTION,"difference","interval_difference",difference1,difference2,
           "Difference restarts scanning the second interval set for every first-set interval",
           ["reuse a monotone interval subtraction cursor","reserve the bounded subtraction output"]),
    recipe("interval_affected_centers",SELECTION,"affected_centers","interval_affected_centers",affected1,affected2,
           "Fallible collection and repeated sorting of order-preserving expanded intervals",
           ["reserve expanded interval storage","merge expanded intervals in preserved start order"]),
]
