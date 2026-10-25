"""Remaining local candidates; no changed validation or lossy work shortcuts."""
import re


def replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"expected one occurrence: {old[:100]!r}")
    return text.replace(old, new, 1)


def sampling1(s):
    s = replace(s, ".chain(signal.row(b))", ".chain(if a==b { &[][..] } else {signal.row(b)})")
    s = replace(s, "if options.method == Method::Slerp {\n            match slerp",
                "if a==b && options.method!=Method::Slerp {values.copy_from_slice(signal.row(a));}\n"
                "        else if options.method == Method::Slerp {\n            match slerp")
    return replace(s, "if values.iter().any(|v| !v.is_finite()) {",
                   "if (a!=b || options.method==Method::Slerp) && values.iter().any(|v| !v.is_finite()) {")


def sampling2(s):
    pattern = r"} else if signal\s*\.row\(a\).*?Some\(Status::NonFinite\)\s*}"
    s, count = re.subn(pattern, "}", s, count=1, flags=re.DOTALL)
    if count != 1:
        raise ValueError("could not locate input finite check")
    a = s.index("        let values = &mut out.values")
    b = s.index("        out.status[i] = Status::Valid", a)
    return s[:a] + '''        let left=signal.row(a);let right_values=signal.row(b);
        let values=&mut out.values[i*signal.channels()..(i+1)*signal.channels()];
        let mut all_finite=true;
        if options.method==Method::Slerp {
            if left.iter().chain(right_values).any(|v|!v.is_finite()) {
                out.status[i]=Status::NonFinite as u8;continue;
            }
            match slerp(left,right_values,alpha) {
                Some(value)=>values.copy_from_slice(&value),
                None=>{out.status[i]=Status::InvalidQuaternion as u8;continue;}
            }
            all_finite=values.iter().all(|v|v.is_finite());
        } else if a==b {
            values.copy_from_slice(left);
            all_finite=values.iter().all(|v|v.is_finite());
        } else {
            for ((value,&x),&y) in values.iter_mut().zip(left).zip(right_values) {
                *value=(1.0-alpha)*x+alpha*y;
                all_finite &= x.is_finite() & y.is_finite() & value.is_finite();
            }
        }
        if !all_finite {
            values.fill(f64::NAN);out.status[i]=Status::NonFinite as u8;continue;
        }
''' + s[b:]


def history1(s):
    return replace(s, "    let mut requests = Vec::with_capacity(size);", '''    if centers.windows(2).all(|w|
        i128::from(w[0])+i128::from(*offsets.last().unwrap()) <= i128::from(w[1])+i128::from(offsets[0])) {
        let mut target=Vec::with_capacity(size);
        for &center in centers {
            for &offset in offsets {target.push(center.checked_add(offset).ok_or(Error::Overflow)?);}
        }
        return Ok(Windowed{centers:centers.to_vec(),offsets:offsets.to_vec(),samples:resample(signal,&target,options)?});
    }
    let mut requests = Vec::with_capacity(size);''')


def history2(s):
    s=replace(s, "let sorted: Vec<_> = requests.iter().map(|r| r.0).collect();", '''let mut sorted=Vec::with_capacity(requests.len());
    let mut sample_indices=Vec::with_capacity(requests.len());
    for &(time,_) in &requests {
        if sorted.last()!=Some(&time) {sorted.push(time);}
        sample_indices.push(sorted.len()-1);
    }''')
    return replace(s, "for (index, &(time, dest)) in requests.iter().enumerate() {",
                   "for (&index, &(time, dest)) in sample_indices.iter().zip(&requests) {")


def quality1(s):
    raise RuntimeError("inspect_signal round 1 is already recorded")


def quality2(s):
    a=s.index("    values.sort_unstable")
    return s[:a]+'''    let n=values.len();
    if n<=64 {
        values.sort_unstable_by(f64::total_cmp);
        return if n.is_multiple_of(2) {values[n/2-1]/2.0+values[n/2]/2.0} else {values[n/2]};
    }
    let (lower,middle,_)=values.select_nth_unstable_by(n/2,f64::total_cmp);
    if n.is_multiple_of(2) {
        *lower.iter().max_by(|a,b|a.total_cmp(b)).unwrap()/2.0+*middle/2.0
    } else {*middle}
}'''


def gate1(s):
    return replace(s, 'reasons.push(format!("{code:?}"));', '''reasons.push(match code {
        IssueCode::NonFinite=>"NonFinite",IssueCode::BelowRange=>"BelowRange",
        IssueCode::AboveRange=>"AboveRange",IssueCode::ClockReversal=>"ClockReversal",
        IssueCode::DuplicateTime=>"DuplicateTime",IssueCode::Gap=>"Gap",
        IssueCode::Rate=>"Rate",IssueCode::Acceleration=>"Acceleration",
        IssueCode::Spike=>"Spike",IssueCode::Flatline=>"Flatline",
    }.to_owned());''')


def gate2(s):
    return replace(s, "let mut reasons = Vec::new();", "let mut reasons = Vec::with_capacity(policy.reject_codes.len()+2);")


def ema1(s):
    s=replace(s,"for i in 0..signal.len() {", "for (i,is_valid) in valid.iter_mut().enumerate() {")
    s=replace(s,"valid[i] = true;", "*is_valid = true;")
    a=s.index("        for c in 0..signal.channels()")
    b=s.index("        *is_valid = true;",a)
    return s[:a]+'''        let d=signal.channels();
        let (past,tail)=values.split_at_mut(i*d);
        let row=&mut tail[..d];
        match prior {
            Some(p)=>for ((value,&old),&current) in row.iter_mut().zip(&past[p*d..(p+1)*d]).zip(signal.row(i)) {
                *value=(1.0-weight)*old+weight*current;
            },
            None=>row.copy_from_slice(signal.row(i)),
        }
'''+s[b:]


def ema2(s):
    s=replace(s,"    let mut previous: Option<usize> = None;",
        "    let mut previous: Option<usize> = None;\n    let mut cached_weight: Option<(i128,f64)> = None;")
    a=s.index("                let dt =")
    b=s.index("            })",a)
    return s[:a]+'''                let dt_ns=i128::from(signal.timestamps()[i])-i128::from(signal.timestamps()[p]);
                if let Some((cached_dt,weight))=cached_weight {
                    if dt_ns==cached_dt {return weight;}
                }
                let dt=dt_ns as f64/1e9;
                let weight=-(-dt/tau_seconds).exp_m1();
                cached_weight=Some((dt_ns,weight));
                weight
'''+s[b:]


def taps1(s):
    s=replace(s,"    let middle = (taps - 1) as f64 / 2.0;",
        "    let middle = (taps - 1) as f64 / 2.0;\n    let phase_step=2.0*std::f64::consts::PI/(taps-1) as f64;")
    return replace(s,"(2.0 * std::f64::consts::PI * i as f64 / (taps - 1) as f64).cos()",
                   "(phase_step*i as f64).cos()")


def taps2(s):
    a=s.index("    let fc =")
    return s[:a]+'''    let fc=cutoff_hz/sample_rate_hz;
    let middle=(taps-1) as f64/2.0;
    let mut result=vec![0.0;taps];
    for i in 0..=taps/2 {
        let n=i as f64-middle;
        let sinc=if n==0.0 {2.0*fc} else {
            (2.0*std::f64::consts::PI*fc*n).sin()/(std::f64::consts::PI*n)
        };
        let value=sinc*(0.54-0.46*(2.0*std::f64::consts::PI*i as f64/(taps-1) as f64).cos());
        result[i]=value;result[taps-1-i]=value;
    }
    let sum:f64=result.iter().sum();
    for value in &mut result {*value/=sum;}
    Ok(result)
}'''


def fir1(s):
    a=s.index("        for c in 0..signal.channels()")
    b=s.index("        *is_valid =",a)
    return s[:a]+'''        let output=&mut values[i*signal.channels()..(i+1)*signal.channels()];
        output.fill(-0.0);
        for (k,&weight) in taps.iter().enumerate() {
            for (value,&sample) in output.iter_mut().zip(signal.row(end-k)) {*value+=weight*sample;}
        }
'''+s[b:]


def fir2(s):
    a=s.index("    let mut values =")
    b=s.index("    let symmetric =",a)
    return s[:a]+'''    let mut values=vec![f64::NAN;signal.values().len()];
    let mut valid=vec![false;signal.len()];
    let lookahead=if mode==FilterMode::Centered {taps.len()/2} else {0};
    let mut supported=0;
    for end in 0..signal.len() {
        if signal.row(end).iter().any(|v|!v.is_finite()) {supported=0;continue;}
        let regular=end==0 || ((i128::from(signal.timestamps()[end])-i128::from(signal.timestamps()[end-1]))-i128::from(period_ns)).abs()<=i128::from(tolerance_ns);
        supported=if regular {supported+1} else {1};
        if supported<taps.len() {continue;}
        let i=end-lookahead;
        let output=&mut values[i*signal.channels()..(i+1)*signal.channels()];
        output.fill(-0.0);
        for (k,&weight) in taps.iter().enumerate() {
            for (value,&sample) in output.iter_mut().zip(signal.row(end-k)) {*value+=weight*sample;}
        }
        valid[i]=output.iter().all(|v|v.is_finite());
        if !valid[i] {output.fill(f64::NAN);}
    }
'''+s[b:]


def unwrap1(s):
    a=s.index("    for c in 0..signal.channels()")
    b=s.index("    Signal::new(",a)
    return s[:a]+'''    for i in 1..signal.len() {
        if i128::from(signal.timestamps()[i])-i128::from(signal.timestamps()[i-1])>i128::from(max_gap_ns) {continue;}
        for c in 0..signal.channels() {
            let (a,b)=(signal.row(i-1)[c],signal.row(i)[c]);
            if !a.is_finite() || !b.is_finite() {continue;}
            let delta=b-a;
            let wrapped=(delta+period/2.0).rem_euclid(period)-period/2.0;
            let adjusted=if wrapped == -period/2.0 && delta>0.0 {period/2.0} else {wrapped};
            values[i*signal.channels()+c]=values[(i-1)*signal.channels()+c]+adjusted;
        }
    }
'''+s[b:]


def unwrap2(s):
    a=s.index("            let wrapped =")
    b=s.index("            values[",a)
    return s[:a]+'''            let adjusted=if delta.abs()<period/2.0 {delta} else {
                let wrapped=(delta+period/2.0).rem_euclid(period)-period/2.0;
                if wrapped == -period/2.0 && delta>0.0 {period/2.0} else {wrapped}
            };
'''+s[b:]


def recipe(op,file,function,cases,r1,r2,hotspot,methods):
    return dict(operator=op,path=file,function=function,cases=cases,rounds=[r1,r2],
                hotspot=hotspot,methods=methods,complexity="Local safe-Rust loop/allocation change; unchanged masks and provenance, no new dependencies")


SAMPLING="crates/core/src/sampling.rs"
FILTER="crates/core/src/filter.rs"
QUALITY="crates/core/src/quality.rs"
RECIPES=[
    recipe("inspect_signal",QUALITY,["inspect_signal","median"],
           "inspect_signal.basic,inspect_signal.hampel,inspect_signal.wide_hampel",quality1,quality2,
           "Callgrind identifies two full sorts per Hampel window as the dominant quality hotspot",
           ["reuse Hampel scratch and bypass disabled derivative work","select medians without fully sorting wide Hampel windows"]),
    recipe("gate",QUALITY,"gate","gate.pass,gate.fail",gate1,gate2,
           "Gate formatting and small repeated reason-vector allocations dominate failure reports",
           ["copy static reason names instead of invoking Debug formatting","reserve the bounded reason list"]),
    recipe("resample",SAMPLING,"resample","resample.previous,resample.nearest,resample.linear,resample.slerp",
           sampling1,sampling2,"Repeated endpoint checks, arithmetic on held values and separate finite passes",
           ["copy held samples without redundant endpoint arithmetic","fuse finite checks with interpolation writes"]),
    recipe("history_windows",SAMPLING,"history_windows","history_windows.separate,history_windows.overlap",
           history1,history2,"History windows sort and scatter even when already time-ordered, and repeat duplicate samples",
           ["directly sample already ordered history windows","deduplicate overlapping history requests before sampling"]),
    recipe("ema",FILTER,"ema","ema.uniform,ema.jitter",ema1,ema2,
           "Repeated channel indexing and expm1 evaluation in the EMA loop",
           ["zip contiguous EMA rows","cache the EMA weight for repeated time deltas"]),
    recipe("lowpass_taps",FILTER,"lowpass_taps","lowpass_taps",taps1,taps2,
           "Trigonometric evaluations and repeated phase scaling dominate coefficient construction",
           ["precompute the Hamming phase increment","compute symmetric lowpass coefficients once"]),
    recipe("fir",FILTER,"fir","fir.scalar,fir.vector",fir1,fir2,
           "FIR repeatedly strides across channels and materializes two support-prefix buffers",
           ["accumulate FIR taps across contiguous channels","track consecutive valid FIR support without prefix buffers"]),
    recipe("unwrap_angles",FILTER,"unwrap_angles","unwrap_angles",unwrap1,unwrap2,
           "Channel-major strides and per-sample modulo dominate angle unwrapping",
           ["process angle channels in row-major order","bypass modulo for already continuous angle increments"]),
]
