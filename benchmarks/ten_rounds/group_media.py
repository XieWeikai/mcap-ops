from common import *

RECIPES=[]
def add(op,path,fn,method,transform,lesson):RECIPES.append(candidate(op,path,fn,method,transform,lesson))


def decode_buffer(s,capacity):
    frozen=original(IMAGE);a,b=function_span(frozen,'decode');s=frozen[a:b]
    return replace(s,'Cursor::new(bytes)',f'std::io::BufReader::with_capacity({capacity},Cursor::new(bytes))')
for capacity in (1024,2048,4096,16384,32768,65536,131072,262144):
    add('image_decode',IMAGE,'decode',f'measure a {capacity}-byte bounded image input buffer',lambda s,n=capacity:decode_buffer(s,n),
        'The old default-size buffer did not help; sweep explicit reader capacities across PNG and JPEG without changing decoder limits.')
RECIPES += [hint('image_decode',IMAGE,'decode',k) for k in ('always','never')]


def quality_chunks(s,size):
    result,count=re.subn(r'\.chunks\(\d+\)',f'.chunks({size})',s)
    assert count==2
    return result
for size in (64,128,512,1024):
    add('image_quality',IMAGE,'image_quality',f'aggregate luminance moments in blocks of {size}',lambda s,n=size:quality_chunks(s,n),
        'Stable two-pass statistics succeeded; tune independent reduction-chain lengths and verify large-image numerical equivalence.')
def quality_store(s):
    a=s.index('        let mut sum =');b=s.index('        Some(variance / n as f64)',a)
    return s[:a]+'''        let laplacians:Vec<_>=(1..height as usize-1).flat_map(&stencil).collect();
        let average=laplacians.iter().sum::<f64>()/n as f64;
        let variance=laplacians.iter().map(|&v|{let d=v-average;d*d}).sum::<f64>();
'''+s[b:]
add('image_quality',IMAGE,'image_quality','reuse computed Laplacians during the variance pass',quality_store,
    'Measure a bounded extra f64 image plane against recomputing five-neighbor stencils; output statistics retain two passes.')
def quality_boundary(s):
    a=s.index('        let mut sum =');b=s.index('        let average =',a)
    return s[:a]+'''        let h=height as usize;
        let mut sum=0.0;
        for x in 1..w-1 {sum+=gray[x]+gray[(h-1)*w+x]-gray[w+x]-gray[(h-2)*w+x];}
        for y in 1..h-1 {sum+=gray[y*w]+gray[y*w+w-1]-gray[y*w+1]-gray[y*w+w-2];}
'''+s[b:]
add('image_quality',IMAGE,'image_quality','compute the Laplacian mean from telescoping image boundaries',quality_boundary,
    'Interior stencil terms cancel in the sum; retain the full stable variance pass and validate floating-point tolerance on large images.')
def quality_lanes(s,size):
    a=s.index('    let mean =');b=s.index('    let laplacian_variance',a)
    return s[:a]+f'''    let moment=|center:Option<f64>| {{
        let mut lanes=[0.0;{size}];
        let mut chunks=gray.chunks_exact({size});
        for block in chunks.by_ref() {{for (lane,&v) in lanes.iter_mut().zip(block) {{
            *lane+=center.map_or(v,|m|{{let d=v-m;d*d}});
        }}}}
        let mut total=lanes.iter().sum::<f64>();
        for &v in chunks.remainder() {{total+=center.map_or(v,|m|{{let d=v-m;d*d}});}}
        total
    }};
    let mean=moment(None)/count as f64;
    let m2=moment(Some(mean));
'''+s[b:]
for size in (4,8):
    add('image_quality',IMAGE,'image_quality',f'use {size} independent luminance reduction lanes',lambda s,n=size:quality_lanes(s,n),
        'Independent accumulators expose instruction-level parallelism without fast-math or reduced precision.')
RECIPES += [hint('image_quality',IMAGE,'image_quality',k) for k in ('always','never')]


def png_options(s,compression,filter):
    frozen=original(IMAGE);a,b=function_span(frozen,'transform_image');s=frozen[a:b]
    return replace(s,'    image.write_to(&mut output, ImageFormat::Png)?;',f'''    use image::ImageEncoder;
    image::codecs::png::PngEncoder::new_with_quality(&mut output,
        image::codecs::png::CompressionType::{compression},image::codecs::png::FilterType::{filter})
        .write_image(image.as_bytes(),image.width(),image.height(),image.color().into())?;''')
for compression,filter in [('Fast','Up'),('Fast','Avg'),('Fast','Paeth'),('Fast','NoFilter'),
                           ('Default','Adaptive'),('Default','Sub'),('Default','Paeth'),('Best','Adaptive')]:
    add('image_transform',IMAGE,'transform_image',f'encode lossless PNG with {compression} compression and {filter} filtering',
        lambda s,c=compression,f=filter:png_options(s,c,f),
        'Fast/Sub failed in the prior campaign; compare other documented encoder hints while checking exact decoded pixels and encoded-size growth.')
RECIPES += [hint('image_transform',IMAGE,'transform_image',k) for k in ('always','never')]


def tool_poll(s,micros):
    return re.sub(r'std::thread::sleep\(Duration::from_(?:millis|micros)\(\d+\)\);',
        f'std::thread::sleep(Duration::from_micros({micros}));',s,count=1)
for micros in (250,500,2000):
    add('video_probe',VIDEO,'run_tool',f'poll media completion every {micros} microseconds',lambda s,n=micros:tool_poll(s,n),
        'The original ten-to-one millisecond change helped; quantify the remaining latency versus polling-cost tradeoff without reducing checks.')
add('video_probe',VIDEO,'run_tool','bound the final media sleep by the remaining timeout',lambda s:replace(s,
    'std::thread::sleep(Duration::from_millis(1));',
    'std::thread::sleep(Duration::from_millis(1).min(timeout.saturating_sub(started.elapsed())));'),
    'Avoid oversleeping a nearly exhausted timeout while retaining output-size checks on every poll.')
add('video_probe',VIDEO,'run_tool','move valid UTF-8 media output into Strings without copying',lambda s:replace(s,
    'Ok(String::from_utf8_lossy(&data).into_owned())',
    'Ok(match String::from_utf8(data) {Ok(text)=>text,Err(error)=>String::from_utf8_lossy(&error.into_bytes()).into_owned()})'),
    'Most ffprobe output is ASCII JSON; retain byte-for-byte lossy-decoding behavior for invalid UTF-8.')
def tool_capacity(s):
    s=replace(s,'        if file.metadata()?.len() > MAX_TOOL_OUTPUT {',
        '        let length=file.metadata()?.len();\n        if length > MAX_TOOL_OUTPUT {')
    return replace(s,'let mut data = Vec::new();','let mut data = Vec::with_capacity(length as usize);')
add('video_probe',VIDEO,'run_tool','reserve the validated media output length before reading',tool_capacity,
    'Use already bounded tempfile metadata to avoid diagnostic-buffer growth; retain read limits and final parsing.')
def tool_args(s):
    s=replace(s,'''    let mut child = Command::new(program)
        .args(args)''','''    let mut command=Command::new(program);
    for argument in args {command.arg(argument);}
    let mut child = command''')
    return s
add('video_probe',VIDEO,'run_tool','append borrowed media arguments individually',tool_args,
    'Profiled work is dominated by child execution; measure command-builder overhead without shell interpolation or altered arguments.')
RECIPES += [hint('video_probe',VIDEO,'run_tool',k) for k in ('always','never')]
def tool_deadline(s):
    s=replace(s,'    let started = Instant::now();','    let started = Instant::now();\n    let deadline=started+timeout;')
    return replace(s,'started.elapsed() > timeout','Instant::now() > deadline')
add('video_probe',VIDEO,'run_tool','compare media deadlines directly during polling',tool_deadline,
    'Hoist the fixed deadline instead of recomputing elapsed duration; preserve the same comparison point and diagnostic limit.')


def video_threads(s,decoder=None,filters=None,period=None):
    frozen=original(VIDEO);a,b=function_span(frozen,'validate_video');s=frozen[a:b]
    flags=[]
    if decoder is not None:flags+=['-threads',str(decoder)]
    if filters is not None:flags+=['-filter_threads',str(filters)]
    if period is not None:flags+=['-stats_period',str(period)]
    inserted=''.join(f'            "{flag}".as_ref(),\n' for flag in flags)
    return replace(s,'            "-i".as_ref(),',inserted+'            "-i".as_ref(),')
for count in (1,2,4,8):
    add('video_validate',VIDEO,'validate_video',f'limit FFmpeg decoding to {count} threads',lambda s,n=count:video_threads(s,decoder=n),
        'Child startup and decoding dominate; compare worker overhead under the fixed CPU affinity without skipping frames or errors.')
for count in (1,2,4,8):
    add('video_validate',VIDEO,'validate_video',f'limit FFmpeg filter workers to {count}',lambda s,n=count:video_threads(s,filters=n),
        'Null-output validation still initializes a filter graph; keep complete first-stream decoding and exact frame-count parsing.')
add('video_validate',VIDEO,'validate_video','use one decoder and one filter worker together',lambda s:video_threads(s,decoder=1,filters=1),
    'Measure the combined worker configuration separately from each individual limit.')
add('video_validate',VIDEO,'validate_video','emit periodic FFmpeg progress every two seconds',lambda s:video_threads(s,period=2),
    'The earlier one-second setting failed; retain the mandatory final progress marker and full frame count while measuring a longer interval.')
