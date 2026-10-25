//! Success-path microbenchmarks. Fixture creation and validation are untimed.
use image::{DynamicImage, ImageFormat, RgbImage};
use mcap::{records::MessageHeader, Message, WriteOptions};
use mcap_ops_core::{filter, quality, sampling, selection, time, Signal};
use mcap_ops_io::mcap_ops::SignalDecoder;
use mcap_ops_io::{image_ops, mcap_ops, video};
use std::{
    borrow::Cow,
    collections::BTreeMap,
    fs::File,
    hint::black_box,
    io::Cursor,
    path::Path,
    process::Command,
    sync::Arc,
    time::{Duration, Instant},
};

struct Runner {
    selected: Option<String>,
    profile: bool,
    samples: usize,
    millis: f64,
}
impl Runner {
    #[inline(never)]
    fn bench<F, T>(&self, name: &str, mut f: F)
    where
        F: FnMut() -> T,
    {
        if self
            .selected
            .as_deref()
            .is_some_and(|s| !s.split(',').any(|v| v == name))
        {
            return;
        }
        black_box(f());
        if self.profile {
            for _ in 0..2 {
                black_box(f());
            }
            println!("{}", serde_json::json!({"case":name,"profile":true}));
            return;
        }
        let mut iterations = 1usize;
        loop {
            let start = Instant::now();
            for _ in 0..iterations {
                black_box(f());
            }
            let elapsed = start.elapsed().as_secs_f64() * 1000.0;
            if elapsed >= self.millis || iterations >= 1_048_576 {
                break;
            }
            iterations = (iterations * 2).min(1_048_576);
        }
        let mut values = Vec::with_capacity(self.samples);
        for _ in 0..self.samples {
            let start = Instant::now();
            for _ in 0..iterations {
                black_box(f());
            }
            values.push(start.elapsed().as_secs_f64() * 1e9 / iterations as f64);
        }
        let mut sorted = values.clone();
        sorted.sort_by(f64::total_cmp);
        println!(
            "{}",
            serde_json::json!({"case":name,"median_ns":sorted[sorted.len()/2],
            "samples_ns":values,"iterations":iterations})
        );
    }
}
fn signal(n: usize, d: usize, jitter: bool) -> Signal {
    let timestamps = (0..n)
        .map(|i| i as i64 * 1_000_000 + if jitter { (i % 7) as i64 * 271 } else { 0 })
        .collect();
    let values = (0..n)
        .flat_map(|i| (0..d).map(move |c| (i as f64 * 0.001 + c as f64 * 0.1).sin()))
        .collect();
    Signal::new(timestamps, values, d).unwrap()
}
fn png(noisy: bool) -> Vec<u8> {
    let image = RgbImage::from_fn(640, 480, |x, y| {
        let z = x.wrapping_mul(1_664_525) ^ y.wrapping_mul(1_013_904_223);
        image::Rgb(if noisy {
            [z as u8, (z >> 8) as u8, (z >> 16) as u8]
        } else {
            [
                (x as u8).wrapping_add(y as u8),
                (x / 3) as u8,
                (y / 2) as u8,
            ]
        })
    });
    let mut out = Cursor::new(Vec::new());
    DynamicImage::ImageRgb8(image)
        .write_to(&mut out, ImageFormat::Png)
        .unwrap();
    out.into_inner()
}
fn mcap_fixture(path: &Path, chunked: bool) {
    let mut writer = WriteOptions::new()
        .compression(None)
        .use_chunks(chunked)
        .create(File::create(path).unwrap())
        .unwrap();
    let schema = writer
        .add_schema("Bench", "jsonschema", br#"{"type":"object"}"#)
        .unwrap();
    let channel = writer
        .add_channel(schema, "/state", "json", &BTreeMap::new())
        .unwrap();
    for i in 0..20_000u32 {
        writer
            .write_to_known_channel(
                &MessageHeader {
                    channel_id: channel,
                    sequence: i,
                    log_time: i as u64 * 1_000_000,
                    publish_time: i as u64 * 1_000_000,
                },
                format!(
                    r#"{{"q":[{},{},{},{}],"nested":{{"v":{}}},"t":{}}}"#,
                    i % 7,
                    i % 11,
                    i % 13,
                    i % 17,
                    i % 19,
                    i as u64 * 1_000_000
                )
                .as_bytes(),
            )
            .unwrap();
    }
    writer.finish().unwrap();
}
fn main() {
    let args: Vec<_> = std::env::args().collect();
    let selected = args
        .windows(2)
        .find(|w| w[0] == "--case")
        .map(|w| w[1].clone());
    let runner = Runner {
        selected,
        profile: args.iter().any(|s| s == "--profile"),
        samples: std::env::var("RSI_SAMPLES")
            .ok()
            .and_then(|s| s.parse().ok())
            .unwrap_or(7),
        millis: std::env::var("RSI_MILLIS")
            .ok()
            .and_then(|s| s.parse().ok())
            .unwrap_or(20.0),
    };
    assert!(runner.samples > 0 && runner.millis > 0.0);
    let dense = signal(50_000, 6, false);
    let jitter = signal(50_000, 6, true);
    let times = dense.timestamps();
    let target: Vec<_> = (0..25_000).map(|i| i * 2_000_000 + 500_000).collect();
    let options = sampling::SampleOptions {
        method: sampling::Method::Linear,
        max_gap_ns: 2_000_000,
        max_age_ns: 2_000_000,
        allow_future: true,
    };
    let q = Signal::new(
        times.to_vec(),
        (0..dense.len())
            .flat_map(|i| {
                let a = i as f64 * 0.0001;
                [0., 0., a.sin(), a.cos()]
            })
            .collect(),
        4,
    )
    .unwrap();
    runner.bench("require_strict", || {
        black_box(&dense).require_ordered().unwrap()
    });
    for (name, num, den) in [
        ("uniform_grid.integer", 1000, 1),
        ("uniform_grid.rational", 30_000, 1001),
    ] {
        runner.bench(name, || {
            time::uniform_grid(
                black_box(0),
                black_box(50_000_000_000),
                black_box(num),
                black_box(den),
                100_000,
            )
            .unwrap()
        });
    }
    for (name, ppb) in [("map_clock.offset", 0), ("map_clock.drift", 1200)] {
        runner.bench(name, || {
            time::map_clock(black_box(times), 0, 17, black_box(ppb)).unwrap()
        });
    }
    for (name, s) in [
        ("inspect_time.uniform", &dense),
        ("inspect_time.jitter", &jitter),
    ] {
        runner.bench(name, || {
            time::inspect_time(black_box(s.timestamps()), 2_000_000).unwrap()
        });
    }
    for (name, nearest) in [
        ("align_timestamps.previous", false),
        ("align_timestamps.nearest", true),
    ] {
        runner.bench(name, || {
            time::align_timestamps(
                black_box(times),
                black_box(&target),
                black_box(nearest),
                2_000_000,
                2_000_000,
            )
            .unwrap()
        });
    }
    let batch_times: Vec<_> = (0..5000).map(|i| i * 10_000_000).collect();
    let counts = vec![10; 5000];
    let offsets: Vec<_> = (0..50_000).map(|i| (i % 10) * 1_000_000).collect();
    runner.bench("expand_batch_timestamps", || {
        time::expand_batch_timestamps(
            black_box(&batch_times),
            black_box(&counts),
            black_box(&offsets),
        )
        .unwrap()
    });
    for (name, method) in [
        ("resample.previous", sampling::Method::Previous),
        ("resample.nearest", sampling::Method::Nearest),
        ("resample.linear", sampling::Method::Linear),
        ("resample.slerp", sampling::Method::Slerp),
    ] {
        let s = if method == sampling::Method::Slerp {
            &q
        } else {
            &dense
        };
        runner.bench(name, || {
            sampling::resample(
                black_box(s),
                black_box(&target),
                black_box(sampling::SampleOptions { method, ..options }),
            )
            .unwrap()
        });
    }
    let history_offsets = [-3_000_000, -2_000_000, -1_000_000, 0];
    for (name, step) in [
        ("history_windows.separate", 10_000_000),
        ("history_windows.overlap", 1_000_000),
    ] {
        let centers: Vec<_> = (0..4000).map(|i| 10_000_000 + i * step).collect();
        runner.bench(name, || {
            sampling::history_windows(
                black_box(&dense),
                black_box(&centers),
                black_box(&history_offsets),
                black_box(options),
            )
            .unwrap()
        });
    }
    let short = signal(4000, 6, false);
    for (name, cfg, s) in [
        (
            "inspect_signal.basic",
            quality::QualityConfig::default(),
            &dense,
        ),
        (
            "inspect_signal.hampel",
            quality::QualityConfig {
                hampel_window_ns: Some(20_000_000),
                ..Default::default()
            },
            &short,
        ),
        (
            "inspect_signal.wide_hampel",
            quality::QualityConfig {
                hampel_window_ns: Some(100_000_000),
                ..Default::default()
            },
            &short,
        ),
    ] {
        runner.bench(name, || {
            quality::inspect_signal(black_box(s), black_box(&cfg)).unwrap()
        });
    }
    let pass = quality::inspect_signal(&short, &quality::QualityConfig::default()).unwrap();
    let fail = quality::inspect_signal(
        &short,
        &quality::QualityConfig {
            upper: Some(vec![0.; 6]),
            max_rate: Some(vec![0.; 6]),
            hampel_window_ns: Some(3_000_000),
            ..Default::default()
        },
    )
    .unwrap();
    let policy = quality::GatePolicy {
        reject_codes: vec![
            quality::IssueCode::AboveRange,
            quality::IssueCode::Rate,
            quality::IssueCode::Spike,
        ],
        min_samples: 100_000,
        max_flagged_fraction: 0.1,
    };
    for (name, report) in [("gate.pass", &pass), ("gate.fail", &fail)] {
        let p = quality::GatePolicy {
            min_samples: 1,
            ..policy.clone()
        };
        runner.bench(name, || {
            quality::gate(black_box(report), black_box(&p)).unwrap()
        });
    }
    for (name, s) in [("ema.uniform", &dense), ("ema.jitter", &jitter)] {
        runner.bench(name, || {
            filter::ema(black_box(s), black_box(0.05), 2_000_000).unwrap()
        });
    }
    runner.bench("lowpass_taps", || {
        filter::lowpass_taps(black_box(1000.), black_box(50.), black_box(63)).unwrap()
    });
    let taps = filter::lowpass_taps(1000., 50., 31).unwrap();
    for (name, d) in [("fir.scalar", 1), ("fir.vector", 6)] {
        let s = signal(20_000, d, false);
        runner.bench(name, || {
            filter::fir(
                black_box(&s),
                black_box(&taps),
                black_box(filter::FilterMode::Causal),
                1_000_000,
                0,
            )
            .unwrap()
        });
    }
    runner.bench("unwrap_angles", || {
        filter::unwrap_angles(
            black_box(&dense),
            black_box(std::f64::consts::TAU),
            2_000_000,
        )
        .unwrap()
    });
    let iv: Vec<_> = (0..6000)
        .map(|i| selection::Interval {
            start_ns: i * 20,
            end_ns: i * 20 + 10,
        })
        .collect();
    let a = selection::IntervalSet::new(iv.clone()).unwrap();
    let b = selection::IntervalSet::new(
        (0..6000)
            .map(|i| selection::Interval {
                start_ns: i * 20 + 5,
                end_ns: i * 20 + 15,
            })
            .collect(),
    )
    .unwrap();
    let late = selection::IntervalSet::new(vec![selection::Interval {
        start_ns: 119_000,
        end_ns: 130_000,
    }])
    .unwrap();
    runner.bench("interval_new", || {
        selection::IntervalSet::new(black_box(iv.clone())).unwrap()
    });
    let queries: Vec<_> = (0..30_000).map(|i| i * 5).collect();
    let shuffled: Vec<_> = (0..30_000).map(|i| (i * 7919) % 150_000).collect();
    runner.bench("interval_contains", || {
        black_box(&queries)
            .iter()
            .filter(|&&t| black_box(&a).contains(black_box(t)))
            .count()
    });
    for (name, qs) in [
        ("interval_mask.ordered", &queries),
        ("interval_mask.shuffled", &shuffled),
    ] {
        runner.bench(name, || black_box(&a).mask(black_box(qs)));
    }
    for (name, other) in [
        ("interval_intersection.dense", &b),
        ("interval_intersection.late", &late),
    ] {
        runner.bench(name, || black_box(&a).intersection(black_box(other)));
    }
    runner.bench("interval_difference", || {
        black_box(&a).difference(black_box(&b))
    });
    runner.bench("interval_affected_centers", || {
        black_box(&a).affected_centers(3, 2).unwrap()
    });
    let wants_io = runner.selected.as_deref().is_none_or(|list| {
        list.split(',').any(|s| {
            s.starts_with("mcap")
                || s.starts_with("raw_reader")
                || s.starts_with("json_decode")
                || s.starts_with("image")
                || s.starts_with("video")
        })
    });
    if !wants_io {
        return;
    }
    let img_options = image_ops::ImageOptions::default();
    let png_data = png(false);
    let noise = png(true);
    let mut jpeg = Cursor::new(Vec::new());
    image::load_from_memory(&png_data)
        .unwrap()
        .write_to(&mut jpeg, ImageFormat::Jpeg)
        .unwrap();
    for (name, data) in [
        ("image_decode.png", &png_data),
        ("image_decode.jpeg", jpeg.get_ref()),
    ] {
        runner.bench(name, || {
            image_ops::decode(black_box(data), black_box(&img_options)).unwrap()
        });
    }
    for (name, data) in [
        ("image_quality.gradient", &png_data),
        ("image_quality.noise", &noise),
    ] {
        runner.bench(name, || {
            image_ops::image_quality(black_box(data), black_box(&img_options)).unwrap()
        });
    }
    for (name, data) in [
        ("image_transform.gradient", &png_data),
        ("image_transform.noise", &noise),
    ] {
        runner.bench(name, || {
            image_ops::transform_image(
                black_box(data),
                black_box(&img_options),
                Some([0, 0, 640, 480]),
                Some([320, 240]),
                image_ops::ResizeFilter::Lanczos3,
            )
            .unwrap()
        });
    }
    let temp = tempfile::tempdir().unwrap();
    let chunked = temp.path().join("chunked.mcap");
    let linear = temp.path().join("linear.mcap");
    mcap_fixture(&chunked, true);
    mcap_fixture(&linear, false);
    let limits = mcap_ops::ReadLimits {
        max_record_bytes: 8 << 20,
        max_messages: 100_000,
    };
    let default_filter = mcap_ops::MessageFilter::default();
    let many_filter = mcap_ops::MessageFilter {
        topics: (0..50)
            .map(|i| format!("/other/{i}"))
            .chain(["/state".into()])
            .collect(),
        ..Default::default()
    };
    for (name, path, filter) in [
        ("raw_reader.chunked", &chunked, &default_filter),
        ("raw_reader.linear", &linear, &default_filter),
        ("raw_reader.topics", &chunked, &many_filter),
    ] {
        runner.bench(name, || {
            let mut total = 0;
            for message in mcap_ops::RawReader::open(
                black_box(path),
                black_box(filter.clone()),
                limits.clone(),
            )
            .unwrap()
            {
                total += message.unwrap().data.len();
            }
            assert!(total > 0);
            total
        });
    }
    runner.bench("mcap_inspect", || {
        mcap_ops::inspect_mcap(
            black_box(&chunked),
            default_filter.clone(),
            limits.clone(),
            2_000_000,
        )
        .unwrap()
    });
    let decoder = mcap_ops::JsonSignalSpec {
        topic: "/state".into(),
        fields: vec!["/q".into()],
        channels: 4,
        timestamp_pointer: Some("/t".into()),
        publish_clock: false,
    };
    let msg = Message {
        channel: Arc::new(mcap::Channel {
            id: 1,
            topic: "/state".into(),
            message_encoding: "json".into(),
            schema: None,
            metadata: BTreeMap::new(),
        }),
        sequence: 0,
        log_time: 0,
        publish_time: 0,
        data: Cow::Borrowed(br#"{"q":[1,2,3,4],"nested":{"v":5},"t":17}"#),
    };
    runner.bench("json_decode", || decoder.decode(black_box(&msg)).unwrap());
    runner.bench("mcap_read_signal", || {
        mcap_ops::read_signal(
            black_box(&chunked),
            default_filter.clone(),
            limits.clone(),
            black_box(&decoder),
            100_000,
        )
        .unwrap()
    });
    if runner
        .selected
        .as_deref()
        .is_none_or(|list| list.split(',').any(|s| s.starts_with("video")))
    {
        let path = temp.path().join("clip.mp4");
        let result = Command::new("ffmpeg")
            .args([
                "-nostdin",
                "-v",
                "error",
                "-f",
                "lavfi",
                "-i",
                "testsrc=size=320x240:rate=30",
                "-t",
                "2",
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
            ])
            .arg(&path)
            .output()
            .unwrap();
        assert!(
            result.status.success(),
            "{}",
            String::from_utf8_lossy(&result.stderr)
        );
        runner.bench("video_probe", || {
            video::probe_video(black_box(&path), "ffprobe", Duration::from_secs(30)).unwrap()
        });
        runner.bench("video_validate", || {
            video::validate_video(
                black_box(&path),
                "ffmpeg",
                "ffprobe",
                Duration::from_secs(30),
            )
            .unwrap()
        });
    }
}
