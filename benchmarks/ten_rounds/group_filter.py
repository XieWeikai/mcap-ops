from common import *

RECIPES=[]
def add(op,method,transform,lesson):RECIPES.append(candidate(op,FILTER,op,method,transform,lesson))


add('ema','initialize EMA storage through zeroed allocation',lambda s:replace(s,
    'let mut values = vec![f64::NAN; signal.values().len()];','let mut values = vec![0.0; signal.values().len()];'),
    'Every EMA row is fully written or filled with NaNs; avoid an unconditional initial NaN fill.')
add('ema','initialize EMA storage from the input snapshot',lambda s:replace(s,
    'let mut values = vec![f64::NAN; signal.values().len()];','let mut values = signal.values().to_vec();'),
    'Compare bulk copying with fill allocation; non-finite rows still reset and become all-NaN.')
def ema_scalar_cache(s):
    s=replace(s,'let mut cached_weight: Option<(i128, f64)> = None;',
        'let mut cached_dt=-1i128;\n    let mut cached_weight=0.0;')
    s=replace(s,'''                if let Some((cached_dt, weight)) = cached_weight {
                    if dt_ns == cached_dt {
                        return weight;
                    }
                }''','''                if dt_ns==cached_dt {return cached_weight;}''')
    return replace(s,'cached_weight = Some((dt_ns, weight));','cached_dt=dt_ns;cached_weight=weight;')
add('ema','store EMA cache validity in an impossible negative delta',ema_scalar_cache,
    'Ordered timestamps guarantee positive deltas; remove the Option tag while preserving exact cached weights.')
def ema_cache(s,size):
    s=replace(s,'let mut cached_weight: Option<(i128, f64)> = None;',
        f'let mut cache=[(-1i128,0.0f64);{size}];\n    let mut next_cache=0;')
    s=replace(s,'''                if let Some((cached_dt, weight)) = cached_weight {
                    if dt_ns == cached_dt {
                        return weight;
                    }
                }''','''                if let Some(&(_,weight))=cache.iter().find(|&&(dt,_)|dt==dt_ns) {return weight;}''')
    return replace(s,'cached_weight = Some((dt_ns, weight));',
        f'cache[next_cache]=(dt_ns,weight);next_cache=(next_cache+1)%{size};')
for size in (2,4,8):
    add('ema',f'cache {size} exact EMA delta weights',lambda s,n=size:ema_cache(s,n),
        'Single-delta caching helped; bounded multi-delta caches may avoid repeated expm1 for periodic jitter.')
add('ema','compare finite EMA inputs against the maximum finite magnitude',lambda s:replace(s,
    'finite &= current.is_finite();','finite &= current.abs()<=f64::MAX;'),
    'Keep exact NaN/Inf detection while testing floating comparison versus exponent-bit classification.')
RECIPES += [hint('ema',FILTER,'ema',k) for k in ('always','never')]
def ema_tau(s):
    s=replace(s,'    let mut values =','    let inverse_tau=1.0/tau_seconds;\n    let mut values =')
    return replace(s,'let weight = -(-dt / tau_seconds).exp_m1();',
        'let weight = -(if inverse_tau.is_finite() {-dt*inverse_tau} else {-dt/tau_seconds}).exp_m1();')
add('ema','reuse a finite reciprocal time constant',ema_tau,
    'Guard reciprocal overflow and retain the original expression for subnormal tau; compare numeric outputs through the oracle.')


def taps_recurrence(s,sinc,window):
    a=s.index('    let fc =')
    init=''
    if sinc:init+='    let (mut sn,mut cn)=(-2.0*std::f64::consts::PI*fc*middle).sin_cos();\n    let (sd,cd)=(2.0*std::f64::consts::PI*fc).sin_cos();\n'
    if window:init+='    let (mut sw,mut cw)=(0.0f64,1.0f64);\n    let (swd,cwd)=(2.0*std::f64::consts::PI/(taps-1) as f64).sin_cos();\n'
    sin='sn' if sinc else '(2.0*std::f64::consts::PI*fc*n).sin()'
    cos='cw' if window else '(2.0*std::f64::consts::PI*i as f64/(taps-1) as f64).cos()'
    update=''
    if sinc:update+='        (sn,cn)=(sn*cd+cn*sd,cn*cd-sn*sd);\n'
    if window:update+='        (sw,cw)=(sw*cwd+cw*swd,cw*cwd-sw*swd);\n'
    return s[:a]+f'''    let fc=cutoff_hz/sample_rate_hz;
    let middle=(taps-1) as f64/2.0;
    let mut result=vec![0.0;taps];
{init}    for i in 0..=taps/2 {{
        let n=i as f64-middle;
        let sinc=if n==0.0 {{2.0*fc}} else {{{sin}/(std::f64::consts::PI*n)}};
        let value=sinc*(0.54-0.46*{cos});
        result[i]=value;result[taps-1-i]=value;
{update}    }}
    let sum:f64=result.iter().sum();
    for value in &mut result {{*value/=sum;}}
    Ok(result)
}}'''
for si,wi,label in [(True,False,'sinc'),(False,True,'Hamming'),(True,True,'both')]:
    add('lowpass_taps',f'advance {label} phases by trigonometric recurrence',lambda s,a=si,b=wi:taps_recurrence(s,a,b),
        'Symmetry already removed half the trigonometric calls; evaluate a bounded recurrence under the existing numerical tolerance.')
add('lowpass_taps','factor the sinc denominator into a reciprocal pi',lambda s:replace(s,
    '/ (std::f64::consts::PI * n)','/ n * std::f64::consts::FRAC_1_PI'),
    'Test constant reciprocal lowering while retaining the exact zero-offset coefficient branch.')
add('lowpass_taps','normalize coefficients with a guarded reciprocal sum',lambda s:replace(s,
    '''    for value in &mut result {
        *value /= sum;
    }''','''    let inverse=1.0/sum;
    for value in &mut result {if inverse.is_finite() {*value*=inverse;} else {*value/=sum;}}'''),
    'Do not turn tiny valid sums into infinite coefficients; retain division when the reciprocal overflows.')
def taps_middle(s):
    s=replace(s,'    for i in 0..=taps / 2 {','    result[taps/2]=2.0*fc;\n    for i in 0..taps / 2 {')
    return replace(s,'''        let sinc = if n == 0.0 {
            2.0 * fc
        } else {
            (2.0 * std::f64::consts::PI * fc * n).sin() / (std::f64::consts::PI * n)
        };''','''        let sinc=(2.0*std::f64::consts::PI*fc*n).sin()/(std::f64::consts::PI*n);''')
add('lowpass_taps','set the center coefficient outside the symmetric loop',taps_middle,
    'The midpoint is the only zero sinc argument; remove that per-iteration branch while preserving symmetry.')
add('lowpass_taps','specialize three-tap coefficient construction',lambda s:replace(s,'    let middle =',
    '''    if taps==3 {
        let a=(2.0*std::f64::consts::PI*fc).sin()/std::f64::consts::PI*(0.54-0.46);
        let b=2.0*fc;let sum=a+b+a;return Ok(vec![a/sum,b/sum,a/sum]);
    }
    let middle ='''),'Evaluate the smallest supported filter without skipping argument checks or DC normalization.')
RECIPES += [hint('lowpass_taps',FILTER,'lowpass_taps',k) for k in ('always','never')]
def taps_push(s):
    s=replace(s,'let mut result = vec![0.0; taps];','let mut result = Vec::with_capacity(taps);')
    s=replace(s,'''        result[i] = value;
        result[taps - 1 - i] = value;''','        result.push(value);')
    return replace(s,'    let sum: f64 =','    for i in (0..taps/2).rev() {result.push(result[i]);}\n    let sum: f64 =')
add('lowpass_taps','append the symmetric coefficient half without zero filling',taps_push,
    'Compare append construction with the existing prefilled symmetric array; output order is unchanged.')


add('fir','index FIR support directly in the flat signal buffer',lambda s:replace(s,
    'w * signal.row(end - k)[c]','w * signal.values()[(end-k)*signal.channels()+c]'),
    'Strided iterator and transposition attempts failed; remove repeated row-slice construction without changing data layout.')
def fir_rchunks(s):
    a=s.index('            let value = taps');b=s.index('            values[i',a)
    return s[:a]+'''            let value=taps.iter().zip(signal.values()[start*signal.channels()..(end+1)*signal.channels()].rchunks_exact(signal.channels()))
                .map(|(&w,row)|w*row[c]).sum::<f64>();
'''+s[b:]
add('fir','iterate FIR support as reversed row chunks',fir_rchunks,
    'Avoid the rejected step_by-reverse iterator and retain channel-outer summation order.')
def fir_prefix(s):
    a=s.index('    let mut bad_prefix');b=s.index('    let lookahead',a)
    return s[:a]+'''    let mut bad_prefix=vec![0usize;signal.len()+1];
    let mut gap_prefix=vec![0usize;signal.len()+1];
    for i in 0..signal.len() {
        bad_prefix[i+1]=bad_prefix[i]+usize::from(signal.row(i).iter().any(|v|!v.is_finite()));
        gap_prefix[i+1]=gap_prefix[i]+usize::from(i>0 &&
            (i128::from(signal.timestamps()[i])-i128::from(signal.timestamps()[i-1])-i128::from(period_ns)).abs()>i128::from(tolerance_ns));
    }
'''+s[b:]
add('fir','construct row and gap support prefixes in one pass',fir_prefix,
    'Retain constant-time window validity while reducing independent scans and loop setup.')
def fir_run(s):
    a=s.index('    let mut bad_prefix');b=s.index('    let symmetric',a)
    return s[:a]+'''    let lookahead=if mode==FilterMode::Centered {taps.len()/2} else {0};
    let mut supported=0;
    for end in 0..signal.len() {
        if signal.row(end).iter().any(|v|!v.is_finite()) {supported=0;continue;}
        let regular=end==0 || (i128::from(signal.timestamps()[end])-i128::from(signal.timestamps()[end-1])-i128::from(period_ns)).abs()<=i128::from(tolerance_ns);
        supported=if regular {supported+1} else {1};
        if supported<taps.len() {continue;}
        let i=end-lookahead;
        for c in 0..signal.channels() {
            values[i*signal.channels()+c]=taps.iter().enumerate().map(|(k,w)|w*signal.row(end-k)[c]).sum::<f64>();
        }
        let row=&mut values[i*signal.channels()..(i+1)*signal.channels()];
        valid[i]=row.iter().all(|v|v.is_finite());if !valid[i] {row.fill(f64::NAN);}
    }
'''+s[b:]
add('fir','track consecutive support while retaining channel-outer convolution',fir_run,
    'The earlier prefix-removal attempt also interchanged convolution loops; isolate support tracking from that failed loop change.')
def fir_single(s):
    return replace(s,'    let mut bad_prefix', '''    if taps.len()==1 {
        for (i,row) in signal.values().chunks_exact(signal.channels()).enumerate() {
            let output=&mut values[i*signal.channels()..(i+1)*signal.channels()];
            for (value,&x) in output.iter_mut().zip(row) {*value=taps[0]*x;}
            valid[i]=row.iter().all(|v|v.is_finite()) && output.iter().all(|v|v.is_finite());
            if !valid[i] {output.fill(f64::NAN);}
        }
        return Ok(Filtered{signal:Signal::new(signal.timestamps().to_vec(),values,signal.channels())?,valid,mode,lookahead_samples:0,group_delay_samples:Some(0.0)});
    }
    let mut bad_prefix''')
add('fir','specialize finite one-tap FIR windows',fir_single,
    'A one-tap window has no interior gap edges; preserve source order, non-finite handling and exact delay metadata.')
def fir_unroll(s,width):
    a=s.index('            let value = taps');b=s.index('            values[i',a)
    code=''.join(f'                value+=taps[k+{i}]*signal.values()[(end-k-{i})*signal.channels()+c];\n' for i in range(width))
    return s[:a]+f'''            let mut value=-0.0;
            let mut k=0;
            while k+{width}<=taps.len() {{
{code}                k+={width};
            }}
            while k<taps.len() {{value+=taps[k]*signal.values()[(end-k)*signal.channels()+c];k+=1;}}
'''+s[b:]
for width in (2,4):
    add('fir',f'unroll ordered FIR accumulation by {width} coefficients',lambda s,n=width:fir_unroll(s,n),
        'Keep each output summation in original tap order; avoid transpose allocation and reassociation.')
RECIPES += [hint('fir',FILTER,'fir',k) for k in ('always','never')]
def fir_static(s):
    s=replace(s,'    let mut values =', '''    #[inline(always)]
    fn fixed<const K:usize>(signal:&Signal,end:usize,c:usize,taps:&[f64;K])->f64 {
        taps.iter().enumerate().map(|(k,w)|w*signal.row(end-k)[c]).sum()
    }
    let mut values =''')
    a=s.index('            let value = taps');b=s.index('            values[i',a)
    return s[:a]+'''            let value=match taps.len() {
                3=>fixed(signal,end,c,<&[f64;3]>::try_from(taps).unwrap()),
                31=>fixed(signal,end,c,<&[f64;31]>::try_from(taps).unwrap()),
                _=>taps.iter().enumerate().map(|(k,w)|w*signal.row(end-k)[c]).sum(),
            };
'''+s[b:]
add('fir','specialize common FIR lengths without transposing data',fir_static,
    'Compile known 3/31-tap reductions with fixed bounds; retain the general path and all eight representative FIR cases.')


def unwrap_half(s):
    s=replace(s,'    let mut values =','    let half=period/2.0;\n    let mut values =')
    # Do not rewrite the initializer introduced above.
    a=s.index('    let mut values =')
    return s[:a]+s[a:].replace('period / 2.0','half')
add('unwrap_angles','hoist the angle half-period explicitly',unwrap_half,
    'Preserve the prior modulo bypass while testing invariant arithmetic placement.')
add('unwrap_angles','compare angle finiteness through finite magnitudes',lambda s:replace(s,
    '!a.is_finite() || !b.is_finite()','!(a.abs()<=f64::MAX && b.abs()<=f64::MAX)'),
    'Use exact NaN/Inf classification with a different machine comparison form.')
def unwrap_gaps(s):
    s=replace(s,'    let mut values =', '''    let has_gaps=signal.timestamps().windows(2).any(|w|i128::from(w[1])-i128::from(w[0])>i128::from(max_gap_ns));
    let mut values =''')
    return replace(s,'        if i128::from(signal.timestamps()[i])',
        '        if has_gaps && i128::from(signal.timestamps()[i])')
add('unwrap_angles','skip repeated gap arithmetic after a gap-free preflight',unwrap_gaps,
    'Inspect every gap once, then keep the exact fallback when any discontinuity exists.')
def unwrap_rows(s):
    s=replace(s,'    for i in 1..signal.len() {', '''    let d=signal.channels();
    for (index,(left,right)) in signal.values().chunks_exact(d).zip(signal.values().chunks_exact(d).skip(1)).enumerate() {
        let i=index+1;''')
    return replace(s,'''signal
            .row(i - 1)
            .iter()
            .zip(signal.row(i))''','''left.iter().zip(right)''')
add('unwrap_angles','iterate adjacent original angle rows as chunks',unwrap_rows,
    'Zipped output rows succeeded previously; extend that locality to the immutable input rows.')
add('unwrap_angles','expand positive-period Euclidean remainder explicitly',lambda s:replace(s,
    'let wrapped = (delta + period / 2.0).rem_euclid(period) - period / 2.0;',
    '''let remainder=(delta+period/2.0)%period;
                let wrapped=if remainder<0.0 {remainder+period} else {remainder}-period/2.0;'''),
    'The period has already been validated positive, so the generic absolute-divisor step is unnecessary.')
add('unwrap_angles','handle single-turn angle remainders by exact subtraction',lambda s:replace(s,
    'let wrapped = (delta + period / 2.0).rem_euclid(period) - period / 2.0;',
    '''let shifted=delta+period/2.0;
                let remainder=if shifted>=period && shifted<2.0*period {shifted-period}
                    else if shifted<0.0 && shifted> -period {shifted+period}
                    else {shifted.rem_euclid(period)};
                let wrapped=remainder-period/2.0;'''),
    'Avoid fmod only where the quotient is known; preserve half-period tie behavior and the arbitrary-jump fallback.')
add('unwrap_angles','compare ordered angle gaps as unsigned distances',lambda s:replace(s,
    '''i128::from(signal.timestamps()[i]) - i128::from(signal.timestamps()[i - 1])
            > i128::from(max_gap_ns)''',
    'signal.timestamps()[i].abs_diff(signal.timestamps()[i-1])>max_gap_ns as u64'),
    'Source timestamps are strictly ordered; abs_diff preserves full-range integer gaps without signed subtraction overflow.')
RECIPES += [hint('unwrap_angles',FILTER,'unwrap_angles',k) for k in ('always','never')]
def unwrap_stream(s):
    s=replace(s,'let mut values = signal.values().to_vec();', '''let mut values=Vec::with_capacity(signal.values().len());
    if !signal.is_empty() {values.extend_from_slice(signal.row(0));}''')
    return replace(s,'    for i in 1..signal.len() {',
        '    for i in 1..signal.len() {\n        values.extend_from_slice(signal.row(i));')
add('unwrap_angles','copy each angle row immediately before transforming it',unwrap_stream,
    'Compare streaming copy-and-transform locality with a full-buffer copy followed by a second pass.')
