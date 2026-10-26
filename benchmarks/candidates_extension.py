"""Twenty bounded follow-up hypotheses, informed by both accepted and rejected trials.

Recipes are experiments, not production code. They are applied to the last accepted
state and retained only after the unchanged correctness/performance gates pass.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from rsi_batch import function_span

FILTER = "crates/core/src/filter.rs"
QUALITY = "crates/core/src/quality.rs"
TIME = "crates/core/src/time.rs"
SELECT = "crates/core/src/selection.rs"
SAMPLE = "crates/core/src/sampling.rs"
IMAGE = "crates/io/src/image_ops.rs"
PYTHON = "crates/python/src/lib.rs"
CORE = "crates/core/src/lib.rs"


def replace(s, old, new):
    assert s.count(old) == 1, (old, s.count(old))
    return s.replace(old, new, 1)


def fir_slice(s):
    a = s.index("            let value = taps")
    b = s.index("            values[i", a)
    return s[:a] + '''            let support = &signal.values()[start * signal.channels() + c..end * signal.channels() + c + 1];
            let value = taps.iter().zip(support.iter().step_by(signal.channels()).rev())
                .map(|(&w, &v)| w * v).sum::<f64>();
''' + s[b:]


def fir_planes(s):
    s = replace(s, "    let mut values =", '''    let mut planes = vec![0.0; signal.values().len()];
    for c in 0..signal.channels() {
        for (out, row) in planes[c*signal.len()..(c+1)*signal.len()].iter_mut()
            .zip(signal.values().chunks_exact(signal.channels())) {
            *out = row[c];
        }
    }
    let mut values =''')
    a = s.index("        for c in 0..signal.channels()", s.index("    let lookahead"))
    b = s.index("        *is_valid =", a)
    return s[:a] + '''        for c in 0..signal.channels() {
            let support = &planes[c*signal.len()+start..c*signal.len()+end+1];
            values[i*signal.channels()+c] = taps.iter().zip(support.iter().rev())
                .map(|(&w, &v)| w*v).sum::<f64>();
        }
''' + s[b:]


def hampel_cursor(s):
    s = replace(s, "                for i in start..end {", "                let (mut a, mut b) = (start, start);\n                for i in start..end {")
    a = s.index("                    let a = start +")
    b = s.index("                    if b - a", a)
    return s[:a] + '''                    while a < end && i128::from(times[a]) < low { a += 1; }
                    while b < end && i128::from(times[b]) <= high { b += 1; }
''' + s[b:]


def hampel_mad(s):
    s = replace(s, '''                    values.iter_mut().for_each(|v| *v = (*v - center).abs());
                    let threshold = (config.hampel_sigma * 1.4826 * median(&mut values))''',
        '''                    let threshold = (config.hampel_sigma * 1.4826 * sorted_mad(&values, center))''')
    return s + '''

// median() has already sorted the finite values. Absolute deviations are two
// monotone sequences on either side of center; merge only through their median.
fn sorted_mad(sorted: &[f64], center: f64) -> f64 {
    let mut left = sorted.partition_point(|&v| v <= center);
    let mut right = left;
    let (mut previous, mut current) = (0.0, 0.0);
    for _ in 0..=sorted.len()/2 {
        let a = left.checked_sub(1).map(|i| (sorted[i]-center).abs());
        let b = sorted.get(right).map(|v| (v-center).abs());
        previous = current;
        current = match (a,b) {
            (Some(a),Some(b)) if a <= b => {left -= 1; a},
            (Some(a),None) => {left -= 1; a},
            (_,Some(b)) => {right += 1; b},
            _ => unreachable!(),
        };
    }
    if sorted.len().is_multiple_of(2) {previous/2.0+current/2.0} else {current}
}
'''


def quality_rows(s):
    return replace(s, '''        for i in 0..signal.len() {
            let v = signal.row(i)[channel];''', '''        for (i, row) in signal.values().chunks_exact(signal.channels()).enumerate() {
            let v = row[channel];''')


def image_rows(s):
    a = s.index("        let lap =")
    b = s.index("        Some(variance / n as f64)", a)
    return s[:a] + '''        let stencil = |row: usize| {
            let top = &gray[(row-1)*w+1..row*w-1];
            let bottom = &gray[(row+1)*w+1..(row+2)*w-1];
            let left = &gray[row*w..(row+1)*w-2];
            let right = &gray[row*w+2..(row+1)*w];
            let center = &gray[row*w+1..(row+1)*w-1];
            top.iter().zip(bottom).zip(left).zip(right).zip(center)
                .map(|((((&a,&b),&c),&d),&e)| a+b+c+d-4.0*e)
        };
        let mut sum = 0.0;
        for row in 1..height as usize-1 {for value in stencil(row) {sum += value;}}
        let average = sum/n as f64;
        let mut variance = 0.0;
        for row in 1..height as usize-1 {for value in stencil(row) {
            let delta=value-average; variance += delta*delta;
        }}
''' + s[b:]


def image_lut(s):
    s = replace(s, "    let mut gray =", '''    let red: [f64; 256] = std::array::from_fn(|i| 0.2126*i as f64);
    let green: [f64; 256] = std::array::from_fn(|i| 0.7152*i as f64);
    let blue: [f64; 256] = std::array::from_fn(|i| 0.0722*i as f64);
    let mut gray =''')
    return replace(s, '''        let y = 0.2126 * f64::from(pixel[0])
            + 0.7152 * f64::from(pixel[1])
            + 0.0722 * f64::from(pixel[2]);''',
        "        let y = red[pixel[0] as usize] + green[pixel[1] as usize] + blue[pixel[2] as usize];")


def intersection_guard(s):
    return replace(s, "        let (mut i, mut j) = (0, 0);", '''        let (mut i, mut j) = (0, 0);
        // Pay for a binary search only when the first pair is disjoint.
        if let (Some(a), Some(b)) = (self.intervals.first(), other.intervals.first()) {
            if a.end_ns <= b.start_ns {
                i = self.intervals.partition_point(|v| v.end_ns <= b.start_ns);
            } else if b.end_ns <= a.start_ns {
                j = other.intervals.partition_point(|v| v.end_ns <= a.start_ns);
            }
        }''')


def interval_inplace(s):
    a = s.index("        let mut merged:")
    return s[:a] + '''        let mut written = 0;
        for read in 0..intervals.len() {
            let interval = intervals[read];
            if written > 0 && interval.start_ns <= intervals[written-1].end_ns {
                intervals[written-1].end_ns = intervals[written-1].end_ns.max(interval.end_ns);
            } else {
                intervals[written] = interval;
                written += 1;
            }
        }
        intervals.truncate(written);
        Ok(Self { intervals })
    }'''


def align_zip(s):
    s = replace(s, "    for (i, &t) in target.iter().enumerate() {", '''    for (((&t, out_index), out_offset), out_valid) in target.iter()
        .zip(&mut result.indices).zip(&mut result.offsets_ns).zip(&mut result.valid) {''')
    s = replace(s, "result.indices[i] =", "*out_index =")
    s = replace(s, "result.offsets_ns[i] =", "*out_offset =")
    return replace(s, "result.valid[i] =", "*out_valid =")


def grid_reserve(s):
    # ceil((span*rate - floor(rate/2))/period), clipped before allocating.
    return replace(s, "    let mut result = Vec::new();", '''    let span = i128::from(end)-i128::from(start);
    let count = ((span*rate-rate/2).max(0)+period_num-1)/period_num;
    if count > max_points as i128 { return Err(invalid("grid exceeds max_points")); }
    let mut result = Vec::with_capacity(count as usize);''')


def clock_narrow(s):
    anchor = "            let delta = (i128::from(t) - i128::from(origin)) * scale;"
    return replace(s, anchor, '''            // Split the integer-nanosecond part before rounding. For negative
            // deltas subtract one from the half-unit bias to keep ties away from zero.
            if let Some(delta) = t.checked_sub(origin) {
                let bias = if delta >= 0 {500_000_000} else {499_999_999};
                if let Some(adjusted) = delta.checked_mul(rate_ppb).and_then(|v| v.checked_add(bias)) {
                    let correction = adjusted.div_euclid(1_000_000_000);
                    return i64::try_from(i128::from(t)+i128::from(correction)+i128::from(offset))
                        .map_err(|_| Error::Overflow);
                }
            }
''' + anchor)


def strict_reduce(s):
    return replace(s, "times.iter().zip(times.iter().skip(1)).any(|(a, b)| b <= a)",
        "times.iter().zip(times.iter().skip(1)).fold(false, |bad, (a,b)| bad | (b <= a))")


def batch_clone(s):
    s = replace(s, "let mut result = Vec::with_capacity(offsets.len());", "let mut result = offsets.to_vec();")
    return replace(s, '''        for &offset in &offsets[index..index + count] {
            result.push(time.checked_add(offset).ok_or(Error::Overflow)?);
        }''', '''        for value in &mut result[index..index+count] {
            *value = time.checked_add(*value).ok_or(Error::Overflow)?;
        }''')


def history_key(s):
    return replace(s, "requests.sort_unstable_by_key(|&(t, index)| (t, index));",
        "requests.sort_unstable_by_key(|&(t, _)| t);")


def slerp_reciprocal(s):
    s = replace(s, "    for j in 0..4 {", "    let (ia, ib) = (1.0/na, 1.0/nb);\n    for j in 0..4 {") if s.count("    for j in 0..4 {") == 1 else s.replace("    for j in 0..4 {", "    let (ia, ib) = (1.0/na, 1.0/nb);\n    for j in 0..4 {", 1)
    s = replace(s, "a[j] / na", "a[j] * ia")
    s = replace(s, "b[j] / nb", "b[j] * ib")
    s = replace(s, "    let n = norm(&q);", "    let inverse_norm = 1.0 / norm(&q);")
    return replace(s, "*v /= n;", "*v *= inverse_norm;")


def ema_fuse(s):
    old = '''        if signal.row(i).iter().any(|v| !v.is_finite()) {
            previous = None;
            continue;
        }
'''
    s = replace(s, old, "")
    s = replace(s, "        match prior {", "        let mut finite = true;\n        match prior {")
    s = replace(s, "                    *value = (1.0 - weight) * old + weight * current;",
        "                    finite &= current.is_finite();\n                    *value = (1.0 - weight) * old + weight * current;")
    s = replace(s, "            None => row.copy_from_slice(signal.row(i)),", '''            None => {
                row.copy_from_slice(signal.row(i));
                finite = row.iter().all(|v| v.is_finite());
            },''')
    return replace(s, "        *is_valid = true;", '''        if !finite { row.fill(f64::NAN); previous = None; continue; }
        *is_valid = true;''')


def bridge_move(sources):
    sources[CORE] = replace(sources[CORE], "    pub fn timestamps(&self) -> &[i64] {", '''    /// Consume the signal and transfer its owned row-major buffers without copying.
    /// Returns (nanosecond timestamps, flat values, channel count).
    pub fn into_parts(self) -> (Vec<i64>, Vec<f64>, usize) {
        (self.timestamps, self.values, self.channels)
    }
    pub fn timestamps(&self) -> &[i64] {''')
    s = sources[PYTHON]
    s = replace(s, "fn signal_dict(py: Python<'_>, signal: &Signal) -> PyResult<Py<PyDict>> {", "fn signal_dict(py: Python<'_>, signal: Signal) -> PyResult<Py<PyDict>> {\n    let (timestamps, values, channels) = signal.into_parts();")
    s = replace(s, "signal.timestamps().to_vec().into_pyarray(py)", "timestamps.into_pyarray(py)")
    s = replace(s, "numpy_values(py, signal.values().to_vec())", "numpy_values(py, values)")
    s = replace(s, 'dict.set_item("channels", signal.channels())?', 'dict.set_item("channels", channels)?')
    s = s.replace("signal_dict(py, &result.signal)", "signal_dict(py, result.signal)")
    s = s.replace("signal_dict(py, &result)", "signal_dict(py, result)")
    s = s.replace("signal_dict(py, &signal)", "signal_dict(py, signal)")
    sources[PYTHON] = s


def time_quantile(s):
    s = replace(s, "    positive.sort_unstable();\n    let median = quantile(&positive, 0.5);", '''    let minimum = positive.iter().min().copied();
    let maximum = positive.iter().max().copied();
    let median = select_quantile(&mut positive, 0.5);
    let p95 = select_quantile(&mut positive, 0.95);''')
    s = replace(s, "positive_interval_min_ns: positive.first().copied(),", "positive_interval_min_ns: minimum,")
    s = replace(s, "positive_interval_max_ns: positive.last().copied(),", "positive_interval_max_ns: maximum,")
    s = replace(s, "positive_interval_p95_ns: quantile(&positive, 0.95),", "positive_interval_p95_ns: p95,")
    a, b = function_span(s, "quantile")
    return s[:a] + '''fn select_quantile(values: &mut [i64], q: f64) -> Option<f64> {
    if values.is_empty() {return None;}
    let index = (values.len()-1) as f64*q;
    let a = index.floor() as usize;
    let b = index.ceil() as usize;
    let (lower, middle, _) = values.select_nth_unstable(b);
    let high = *middle as f64;
    let low = if a == b {high} else {*lower.iter().max().unwrap() as f64};
    Some(low + (high-low)*(index-a as f64))
}''' + s[b:]


def unwrap_zip(s):
    a = s.index("        for c in 0..signal.channels() {")
    s = s[:a] + s[a:].replace('''        for c in 0..signal.channels() {
            let (a, b) = (signal.row(i - 1)[c], signal.row(i)[c]);''', '''        let d = signal.channels();
        let (past, current) = values.split_at_mut(i*d);
        for (((&a, &b), &old), output) in signal.row(i-1).iter().zip(signal.row(i))
            .zip(&past[(i-1)*d..]).zip(&mut current[..d]) {''', 1)
    return replace(s, "            values[i * signal.channels() + c] = values[(i - 1) * signal.channels() + c] + adjusted;",
        "            *output = old + adjusted;")


def recipe(op, path, function, change, cases, method, lesson, hotspot):
    return dict(operator=op, paths=[path], function=function, change=change, cases=cases,
                method=method, lesson=lesson, hotspot=hotspot)


FIR = "fir.scalar,fir.vector"
QC = "inspect_signal.basic,inspect_signal.hampel,inspect_signal.wide_hampel"
IQ = "image_quality.gradient,image_quality.noise"
ALIGN = "align_timestamps.previous,align_timestamps.nearest"
RECIPES = [
    recipe("fir", FILTER, "fir", fir_slice, FIR, "dot FIR taps against checked strided support slices", "Earlier channel-inner accumulation regressed 26%; retain channel-outer summation and remove repeated row slicing instead.", "FIR dot loops repeatedly calculate and bound-check row slices."),
    recipe("fir", FILTER, "fir", fir_planes, FIR, "transpose FIR input once into contiguous channel planes", "Earlier loop interchange lost scalar throughput; this candidate keeps reduction order and trades one bounded input copy for contiguous support.", "FIR strided dot products dominate after support checks."),
    recipe("inspect_signal", QUALITY, "inspect_signal", hampel_cursor, QC, "advance Hampel window bounds with monotone cursors", "Scratch reuse helped; wide quickselect was unstable. Remove two binary searches per sample without changing the median algorithm.", "Hampel window lookup repeats partition_point over each gap-delimited segment."),
    recipe("inspect_signal", QUALITY, None, hampel_mad, QC, "merge ordered absolute deviations through their median", "The first median sorts already; exploit that order instead of repeating the previously rejected quickselect hypothesis.", "Baseline Callgrind attributes most Hampel instructions to two sorts per window."),
    recipe("inspect_signal", QUALITY, "inspect_signal", quality_rows, QC, "iterate bounded signal rows for channel statistics", "Keep Welford arithmetic and issue order; scratch and disabled-check work already removed.", "Quality channel scans repeatedly derive row offsets and bounds."),
    recipe("image_quality", IMAGE, "image_quality", image_rows, IQ, "zip bounded image rows for Laplacian stencils", "Two-pass moments helped; preserve those arithmetic orders while reducing per-pixel stencil indexing.", "Image profile shows repeated neighbor indexing alongside decoding and hashing."),
    recipe("image_quality", IMAGE, "image_quality", image_lut, IQ, "tabulate exact eight-bit luminance contributions", "Avoid reduced precision or approximate statistics; each 256-entry table uses the same f64 multiply as the old pixel loop.", "Luminance construction repeats three identical coefficient multiplications per byte value."),
    recipe("interval_intersection", SELECT, "intersection", intersection_guard, "interval_intersection.dense,interval_intersection.late", "skip disjoint initial interval prefixes conditionally", "Unconditional prefix search improved late overlap but regressed dense overlap 13%; guard searches on disjoint first pairs.", "Late overlap scans thousands of impossible intersections before producing output."),
    recipe("interval_new", SELECT, "new", interval_inplace, "interval_new", "merge sorted intervals in their owned input allocation", "Reserve and sortedness precheck both failed; avoid the second vector altogether.", "Interval construction copies an already owned vector into a growing merge buffer."),
    recipe("align_timestamps", TIME, "align_timestamps", align_zip, ALIGN, "zip alignment output buffers with target timestamps", "Push-based outputs and abs_diff both failed; keep zero-initialized buffers and exact i128 tolerance logic.", "Alignment writes three separately indexed vectors at every selected target."),
    recipe("uniform_grid", TIME, "uniform_grid", grid_reserve, "uniform_grid.integer,uniform_grid.rational", "derive exact bounded grid capacity before generation", "Quotient/remainder recurrence was accepted; now remove geometric vector growth without allocating max_points.", "Grid recurrence still grows its output buffer repeatedly."),
    recipe("map_clock", TIME, "map_clock", clock_narrow, "map_clock.offset,map_clock.drift", "round clock drift using checked narrow correction arithmetic", "Zero-drift fast path helped; preserve wide fallback and away-from-zero tie semantics for actual drift.", "Nonzero clock drift still invokes wide signed division per timestamp."),
    recipe("require_strict", TIME, "require_strict", strict_reduce, "require_strict", "reduce timestamp order violations without early branches", "Zipped adjacency beat windows; keep it and allow SIMD through a non-short-circuit boolean reduction.", "Order checks run a predictable branch for every adjacent pair."),
    recipe("expand_batch_timestamps", TIME, "expand_batch_timestamps", batch_clone, "expand_batch_timestamps", "update copied batch offsets through mutable slices", "Iterator spelling and min/max prescans failed; retain per-element checked addition while removing Vec push bookkeeping.", "Batch expansion writes each pre-reserved result through push."),
    recipe("history_windows", SAMPLE, "history_windows", history_key, "history_windows.separate,history_windows.overlap", "sort history requests by timestamp without redundant tie keys", "Deduplication helped; equal-time requests already share one sampled result, so destination tie ordering is unobservable.", "Overlap sorting compares destination indices even when timestamps are identical."),
    recipe("resample", SAMPLE, "slerp", slerp_reciprocal, "resample.previous,resample.nearest,resample.linear,resample.slerp", "reuse quaternion normalization reciprocals", "Method splitting caused regressions; optimize the existing SLERP helper without duplicating sampling logic.", "SLERP normalization divides four components by each shared norm."),
    recipe("ema", FILTER, "ema", ema_fuse, "ema.uniform,ema.jitter", "fuse EMA finite-input checks into output updates", "Weight caching and zipped rows succeeded; remove the remaining duplicate input scan while preserving invalid-row reset.", "EMA reads current rows for finite checks and again for arithmetic."),
    dict(operator="python_bridge", paths=[CORE, PYTHON], function=None, change=bridge_move, python=True,
         cases="python.ema,python.fir,python.unwrap_angles,python.read_json_signal", method="move owned signal buffers into NumPy without cloning",
         lesson="Direct NumPy outputs succeeded; Signal-backed results still clone their owned buffers before transfer. Public result types stay unchanged.",
         hotspot="signal_dict clones both time and value arrays even though callers discard the Rust Signal."),
    recipe("inspect_time", TIME, None, time_quantile, "inspect_time.uniform,inspect_time.jitter", "select clock quantiles without fully sorting intervals", "Uniform fast path helped and is retained; only nonuniform intervals need partial selection.", "Jitter statistics sort all positive intervals to obtain four order statistics."),
    recipe("unwrap_angles", FILTER, "unwrap_angles", unwrap_zip, "unwrap_angles", "zip disjoint angle rows and accumulated outputs", "Row-major order and modulo bypass helped; retain those and remove repeated channel-index arithmetic.", "Unwrap loop indexes previous/current original rows and accumulated output separately."),
]
