"""Small IO candidates: preserve complete scans, CRCs, limits and decoded pixels."""
import re


def replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"expected one occurrence: {old[:100]!r}")
    return text.replace(old, new, 1)


def raw1(s):
    return replace(s, "BufReader::new(file)", "BufReader::with_capacity(64*1024,file)")


def raw2(s):
    s=replace(s,"pub fn open(path: impl AsRef<Path>, filter: MessageFilter, limits: ReadLimits) -> Result<Self> {",
                "pub fn open(path: impl AsRef<Path>, mut filter: MessageFilter, limits: ReadLimits) -> Result<Self> {")
    s=replace(s,"        filter.validate()?;",
                "        filter.validate()?;\n        if filter.topics.len()>8 {filter.topics.sort_unstable();}")
    return replace(s,"self.topics.contains(&m.channel.topic)",
        "(if self.topics.len()>8 {self.topics.binary_search(&m.channel.topic).is_ok()} else {self.topics.contains(&m.channel.topic)})")


def inspect1(s):
    s=replace(s,"        channels.push(ChannelReport {",'''        let log_stats=inspect_time(&logs,max_gap_ns)?;
        let publish_stats=if logs==pubs {log_stats.clone()} else {inspect_time(&pubs,max_gap_ns)?};
        channels.push(ChannelReport {''')
    s=replace(s,"log_time: inspect_time(&logs, max_gap_ns)?,","log_time: log_stats,")
    return replace(s,"publish_time: inspect_time(&pubs, max_gap_ns)?,","publish_time: publish_stats,")


def inspect2(s):
    return replace(s,'''    for id in 0..=u16::MAX {
        let Some(channel) = reader.reader.get_channel(id) else {
            continue;
        };''', '''    for channel in (0..=u16::MAX).filter_map(|id|reader.reader.get_channel(id)) {
        let id=channel.id;''')


def json1(s):
    anchor="        let timestamp_ns ="
    s=replace(s,anchor,'''        let lookup=|pointer:&str| {
            if let Some(key)=pointer.strip_prefix('/') {
                if !key.contains(['/', '~']) && payload.is_object() {return payload.get(key);}
            }
            payload.pointer(pointer)
        };
        let timestamp_ns =''')
    # Replace only the two lookup sites, not the fallback inside lookup itself.
    s,count=re.subn(r"payload\s*\n\s*\.pointer\(pointer\)","lookup(pointer)",s)
    if count!=2: raise ValueError("expected timestamp and field pointer sites")
    return s


def json2(s):
    return replace(s,"let mut values = Vec::new();","let mut values = Vec::with_capacity(self.channels.min(256));")


def read1(s):
    s=replace(s,"let mut timestamps = Vec::new();",
                "let reserve=max_samples.min(4096);\n    let mut timestamps = Vec::with_capacity(reserve);")
    return replace(s,"let mut values = Vec::new();",
        "let mut values = Vec::with_capacity(reserve.saturating_mul(decoder.channels()).min(16384));")


def read2(s):
    s=replace(s,"for sample in decoder.decode(&item?)? {","for mut sample in decoder.decode(&item?)? {")
    return replace(s,"values.extend(sample.values);","values.append(&mut sample.values);")


def decode1(s):
    a=s.index("    let mut reader =")
    b=s.index("    let mut limits =",a)
    return s[:a]+'''    let format=image::guess_format(bytes).ok();
    if !matches!(format,Some(ImageFormat::Png|ImageFormat::Jpeg)) {
        return Err(invalid("only PNG and JPEG are supported"));
    }
    let mut reader=ImageReader::with_format(Cursor::new(bytes),format.unwrap());
'''+s[b:]


def decode2(s):
    return replace(s,"Cursor::new(bytes)","std::io::BufReader::new(Cursor::new(bytes))")


def image_quality1(s):
    s=replace(s,"decode(bytes, options)?.to_rgb8()","decode(bytes, options)?.into_rgb8()")
    s=replace(s,"let (mut mean, mut m2, mut dark, mut bright) = (0.0, 0.0, 0u64, 0u64);",
                "let (mut dark,mut bright)=(0u64,0u64);")
    s=replace(s,"for (i, pixel) in rgb.pixels().enumerate() {","for pixel in rgb.pixels() {")
    s=replace(s,'''        let delta = y - mean;
        mean += delta / (i + 1) as f64;
        m2 += delta * (y - mean);
''',"")
    return replace(s,"    let laplacian_variance =",'''    let mean=gray.chunks(256).map(|chunk|chunk.iter().sum::<f64>()).sum::<f64>()/count as f64;
    let m2=gray.chunks(256).map(|chunk|chunk.iter().map(|&v|(v-mean)*(v-mean)).sum::<f64>()).sum::<f64>();
    let laplacian_variance =''')


def image_quality2(s):
    a=s.index("    let laplacian_variance =")
    b=s.index("    let mut hash =",a)
    return s[:a]+'''    let laplacian_variance=if width>=3 && height>=3 {
        let w=width as usize;
        let n=(width as usize-2)*(height as usize-2);
        let lap=|i:usize|gray[i-w]+gray[i+w]+gray[i-1]+gray[i+1]-4.0*gray[i];
        let mut sum=0.0;
        for y in 1..height as usize-1 {for x in 1..w-1 {sum+=lap(y*w+x);}}
        let average=sum/n as f64;
        let mut variance=0.0;
        for y in 1..height as usize-1 {for x in 1..w-1 {
            let delta=lap(y*w+x)-average;variance+=delta*delta;
        }}
        Some(variance/n as f64)
    } else {None};
'''+s[b:]


def transform1(s):
    return replace(s,"image = image.crop_imm(x, y, width, height);",'''if x!=0 || y!=0 || width!=image.width() || height!=image.height() {
            image = image.crop_imm(x, y, width, height);
        }''')


def transform2(s):
    return replace(s,"image.write_to(&mut output, ImageFormat::Png)?;",'''use image::ImageEncoder;
    image::codecs::png::PngEncoder::new_with_quality(&mut output,
        image::codecs::png::CompressionType::Fast,image::codecs::png::FilterType::Sub)
        .write_image(image.as_bytes(),image.width(),image.height(),image.color().into())?;''')


def probe1(s):
    return replace(s,"std::thread::sleep(Duration::from_millis(10));",
                   "std::thread::sleep(Duration::from_millis(1));")


def probe2(s):
    return re.sub(r"std::thread::sleep\(Duration::from_millis\((?:1|10)\)\);",
                  "std::thread::park_timeout(Duration::from_millis(1));",s,count=1)


def video1(s):
    return replace(s,'            "-progress".as_ref(),',
        '            "-stats_period".as_ref(),\n            "1".as_ref(),\n            "-progress".as_ref(),')


def video2(s):
    a=s.index("    let decoded_frames =")
    b=s.index("        return Err(invalid(",a)
    return s[:a]+'''    let mut frame_count=None;
    let mut completed=false;
    for line in progress.lines().rev() {
        if frame_count.is_none() {frame_count=line.strip_prefix("frame=").and_then(|v|v.trim().parse::<u64>().ok());}
        completed |= line=="progress=end";
        if frame_count.is_some() && completed {break;}
    }
    let decoded_frames=frame_count.unwrap_or(0);
    if decoded_frames==0 || !completed {
'''+s[b:]


def recipe(op,file,function,cases,r1,r2,hotspot,methods):
    return dict(operator=op,path=file,function=function,cases=cases,rounds=[r1,r2],
        hotspot=hotspot,methods=methods,
        complexity="Local bounded allocation, parsing or loop change; complete checks and payload interpretation retained")


MCAP="crates/io/src/mcap_ops.rs"
IMAGE="crates/io/src/image_ops.rs"
VIDEO="crates/io/src/video.rs"
RECIPES=[
    recipe("raw_reader",MCAP,["open",None],"raw_reader.chunked,raw_reader.linear,raw_reader.topics",raw1,raw2,
           "Callgrind: reader buffering and repeated exact topic membership checks",
           ["increase the bounded reader buffer","binary-search long immutable topic filters"]),
    recipe("mcap_inspect",MCAP,"inspect_mcap","mcap_inspect",inspect1,inspect2,
           "Repeated clock summaries and exhaustive channel lookup in the inspection adapter",
           ["reuse identical log and publish clock summaries","stream channel lookup through a filtered iterator"]),
    recipe("json_decode",MCAP,"decode","json_decode",json1,json2,
           "Callgrind: JSON pointer decoding repeatedly allocates unescaped strings for flat field names",
           ["fast-path unescaped top-level JSON pointers","reserve a bounded numeric field vector"]),
    recipe("mcap_read_signal",MCAP,"read_signal","mcap_read_signal",read1,read2,
           "Decoded signal vectors repeatedly grow while moving each decoded row",
           ["reserve bounded decoded signal storage","append decoded row buffers directly"]),
    recipe("image_decode",IMAGE,"decode","image_decode.png,image_decode.jpeg",decode1,decode2,
           "Most work is in validated third-party decoders; inspect small adapter overhead without relaxing limits",
           ["guess image format directly from the byte slice","buffer the in-memory decoder reader"]),
    recipe("image_quality",IMAGE,"image_quality","image_quality.gradient,image_quality.noise",image_quality1,image_quality2,
           "Per-pixel online moment division and repeated decoded RGB allocation",
           ["use chunked two-pass luminance statistics and consume RGB storage","compute Laplacian variance with two stable passes"]),
    recipe("image_transform",IMAGE,"transform_image","image_transform.gradient,image_transform.noise",transform1,transform2,
           "Full-image crop copying and lossless PNG row-filter work",
           ["avoid copying identity crops after validation","encode lossless PNG with a fixed Sub filter"]),
    recipe("video_probe",VIDEO,"run_tool","video_probe,video_validate",probe1,probe2,
           "Child-completion observation is quantized by a ten-millisecond polling sleep",
           ["reduce bounded media child polling latency","use a timed park for media child completion"]),
    recipe("video_validate",VIDEO,"validate_video","video_validate",video1,video2,
           "FFmpeg process/decode dominates; inspect progress emission and final-marker parsing",
           ["reduce intermediate FFmpeg progress emission","parse final progress status and frame count together"]),
]
