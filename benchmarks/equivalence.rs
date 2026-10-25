//! Differential oracle against the immutable pre-RSI implementation.
use std::{collections::BTreeMap,fs::File,io::Cursor};
fn numbers(a:&[f64],b:&[f64]) {
    assert_eq!(a.len(),b.len());
    for (i,(&x,&y)) in a.iter().zip(b).enumerate() {
        if x.is_nan() {assert!(y.is_nan(),"{i}: {x} != {y}");}
        else if !x.is_finite() {assert_eq!(x,y);}
        else {assert!((x-y).abs()<=1e-10*(1.0+x.abs()),"{i}: {x} != {y}");}
    }
}
fn json(a:serde_json::Value,b:serde_json::Value) {
    match (&a,&b) {
        (serde_json::Value::Number(x),serde_json::Value::Number(y))=>{
            if let (Some(x),Some(y))=(x.as_i64(),y.as_i64()) {assert_eq!(x,y);}
            else if let (Some(x),Some(y))=(x.as_u64(),y.as_u64()) {assert_eq!(x,y);}
            else {numbers(&[x.as_f64().unwrap()],&[y.as_f64().unwrap()]);}
        }
        (serde_json::Value::Array(x),serde_json::Value::Array(y))=>{
            assert_eq!(x.len(),y.len());for (x,y) in x.iter().zip(y) {json(x.clone(),y.clone());}
        }
        (serde_json::Value::Object(x),serde_json::Value::Object(y))=>{
            assert_eq!(x.len(),y.len());for (k,x) in x {json(x.clone(),y[k].clone());}
        }
        _=>assert_eq!(a,b),
    }
}
fn sampled(a:before::sampling::Sampled,b:after::sampling::Sampled) {
    assert_eq!(a.timestamps,b.timestamps);assert_eq!(a.channels,b.channels);
    assert_eq!(a.status,b.status);assert_eq!(a.source_left,b.source_left);
    assert_eq!(a.source_right,b.source_right);assert_eq!(a.uses_future,b.uses_future);
    numbers(&a.values,&b.values);numbers(&a.alpha,&b.alpha);
}
fn rng(seed:&mut u64)->u64 {*seed=seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);*seed}
fn main() {
    let mut seed=17;
    for iteration in 0..180 {
        let n=1+(rng(&mut seed)%150) as usize;let d=1+(rng(&mut seed)%6) as usize;
        let mut times=Vec::new();let mut t=1_700_000_000_000_000_000i64;
        for _ in 0..n {t+=1+(rng(&mut seed)%35) as i64;times.push(t);}
        let mut values:Vec<_>=(0..n*d).map(|_|(rng(&mut seed)%10000) as f64/100.0-50.0).collect();
        if iteration%3==0 {let index=rng(&mut seed) as usize%values.len();values[index]=f64::NAN;}
        let a=before::Signal::new(times.clone(),values.clone(),d).unwrap();
        let b=after::Signal::new(times.clone(),values,d).unwrap();
        let mut targets=vec![times[0]-10,*times.last().unwrap()+10];
        targets.extend(times.iter().flat_map(|&t|[t,t+1]));targets.sort_unstable();
        assert_eq!(before::time::require_strict(&times).is_ok(),after::time::require_strict(&times).is_ok());
        for rate in [1,3,30,1000,30000] {
            assert_eq!(before::time::uniform_grid(times[0],times[0]+1000000000,rate,1001,1000).ok(),
                after::time::uniform_grid(times[0],times[0]+1000000000,rate,1001,1000).ok());
        }
        for ppb in [-999_999_999,-1200,0,1200,1_000_000_000] {
            assert_eq!(before::time::map_clock(&times,times[0],-7,ppb).ok(),after::time::map_clock(&times,times[0],-7,ppb).ok());
        }
        json(serde_json::to_value(before::time::inspect_time(&times,20).unwrap()).unwrap(),
            serde_json::to_value(after::time::inspect_time(&times,20).unwrap()).unwrap());
        for nearest in [true,false] {
            let aa=before::time::align_timestamps(&times,&targets,nearest,10,10).unwrap();
            let bb=after::time::align_timestamps(&times,&targets,nearest,10,10).unwrap();
            assert_eq!(aa.indices,bb.indices);assert_eq!(aa.offsets_ns,bb.offsets_ns);assert_eq!(aa.valid,bb.valid);
        }
        for (ma,mb) in [
            (before::sampling::Method::Previous,after::sampling::Method::Previous),
            (before::sampling::Method::Nearest,after::sampling::Method::Nearest),
            (before::sampling::Method::Linear,after::sampling::Method::Linear),
        ] {
            for allow_future in [true,false] {
                let oa=before::sampling::SampleOptions{method:ma,max_gap_ns:20,max_age_ns:10,allow_future};
                let ob=after::sampling::SampleOptions{method:mb,max_gap_ns:20,max_age_ns:10,allow_future};
                sampled(before::sampling::resample(&a,&targets,oa).unwrap(),after::sampling::resample(&b,&targets,ob).unwrap());
                let offsets=[-40,-20,0];
                let wa=before::sampling::history_windows(&a,&times,&offsets,oa).unwrap();
                let wb=after::sampling::history_windows(&b,&times,&offsets,ob).unwrap();
                assert_eq!(wa.centers,wb.centers);assert_eq!(wa.offsets,wb.offsets);sampled(wa.samples,wb.samples);
            }
        }
        let config=serde_json::json!({"max_gap_ns":25,"lower":vec![-30.;d],"upper":vec![30.;d],
            "max_rate":vec![1e8;d],"max_acceleration":vec![1e16;d],"hampel_window_ns":50,
            "flatline_duration_ns":20,"flatline_tolerance":0.1,"max_issues":7});
        let qa=before::quality::inspect_signal(&a,&serde_json::from_value(config.clone()).unwrap()).unwrap();
        let qb=after::quality::inspect_signal(&b,&serde_json::from_value(config).unwrap()).unwrap();
        assert_eq!(qa.flagged_samples,qb.flagged_samples);
        json(serde_json::to_value(&qa).unwrap(),serde_json::to_value(&qb).unwrap());
        let policy=serde_json::json!({"reject_codes":["non_finite","above_range","rate","spike"],
            "max_flagged_fraction":0.5,"min_samples":5});
        json(serde_json::to_value(before::quality::gate(&qa,&serde_json::from_value(policy.clone()).unwrap()).unwrap()).unwrap(),
            serde_json::to_value(after::quality::gate(&qb,&serde_json::from_value(policy).unwrap()).unwrap()).unwrap());
        let fa=before::filter::ema(&a,0.05,30).unwrap();let fb=after::filter::ema(&b,0.05,30).unwrap();
        assert_eq!(fa.valid,fb.valid);numbers(fa.signal.values(),fb.signal.values());
        numbers(before::filter::unwrap_angles(&a,std::f64::consts::TAU,30).unwrap().values(),
            after::filter::unwrap_angles(&b,std::f64::consts::TAU,30).unwrap().values());
        for count in [3,7,31,63] {
            numbers(&before::filter::lowpass_taps(200.,20.,count).unwrap(),&after::filter::lowpass_taps(200.,20.,count).unwrap());
        }
        let regular:Vec<_>=(0..n).map(|i|i as i64*10).collect();
        let ra=before::Signal::new(regular.clone(),a.values().to_vec(),d).unwrap();
        let rb=after::Signal::new(regular.clone(),b.values().to_vec(),d).unwrap();
        for (ma,mb) in [(before::filter::FilterMode::Causal,after::filter::FilterMode::Causal),
            (before::filter::FilterMode::Centered,after::filter::FilterMode::Centered)] {
            let x=before::filter::fir(&ra,&[0.25,0.5,0.25],ma,10,0).unwrap();
            let y=after::filter::fir(&rb,&[0.25,0.5,0.25],mb,10,0).unwrap();
            assert_eq!(x.valid,y.valid);assert_eq!(x.lookahead_samples,y.lookahead_samples);
            assert_eq!(x.group_delay_samples,y.group_delay_samples);numbers(x.signal.values(),y.signal.values());
        }
        let mut raw:Vec<_>=(0..30).map(|_|{let s=(rng(&mut seed)%500) as i64;(s,s+1+(rng(&mut seed)%20) as i64)}).collect();
        let ia=before::selection::IntervalSet::new(raw.iter().map(|&(s,e)|before::selection::Interval{start_ns:s,end_ns:e}).collect()).unwrap();
        let ib=after::selection::IntervalSet::new(raw.iter().map(|&(s,e)|after::selection::Interval{start_ns:s,end_ns:e}).collect()).unwrap();
        let qs:Vec<_>=(-5..550).collect();assert_eq!(ia.mask(&qs),ib.mask(&qs));
        for &q in &qs {assert_eq!(ia.contains(q),ib.contains(q));}
        raw.iter_mut().for_each(|(s,e)|{*s+=7;*e+=9;});
        let ja=before::selection::IntervalSet::new(raw.iter().map(|&(s,e)|before::selection::Interval{start_ns:s,end_ns:e}).collect()).unwrap();
        let jb=after::selection::IntervalSet::new(raw.iter().map(|&(s,e)|after::selection::Interval{start_ns:s,end_ns:e}).collect()).unwrap();
        for (x,y) in [(ia.intersection(&ja),ib.intersection(&jb)),(ia.difference(&ja),ib.difference(&jb)),
            (ia.affected_centers(3,8).unwrap(),ib.affected_centers(3,8).unwrap())] {
            json(serde_json::to_value(x).unwrap(),serde_json::to_value(y).unwrap());
        }
        assert_eq!(before::time::expand_batch_timestamps(&times,&vec![2;n],&vec![0;2*n]).ok(),
            after::time::expand_batch_timestamps(&times,&vec![2;n],&vec![0;2*n]).ok());
    }
    for n in [1,2,3,8,64] {
        for format in [image::ImageFormat::Png,image::ImageFormat::Jpeg] {
            let rgb=image::RgbImage::from_fn(n,n,|x,y|image::Rgb([(x*19) as u8,(y*17) as u8,(x+y) as u8]));
            let mut bytes=Cursor::new(Vec::new());image::DynamicImage::ImageRgb8(rgb).write_to(&mut bytes,format).unwrap();
            let oa=before_io::image_ops::ImageOptions::default();let ob=after_io::image_ops::ImageOptions::default();
            let a=before_io::image_ops::decode(bytes.get_ref(),&oa).unwrap();
            let b=after_io::image_ops::decode(bytes.get_ref(),&ob).unwrap();
            assert_eq!(a.to_rgba8(),b.to_rgba8());
            json(serde_json::to_value(before_io::image_ops::image_quality(bytes.get_ref(),&oa).unwrap()).unwrap(),
                serde_json::to_value(after_io::image_ops::image_quality(bytes.get_ref(),&ob).unwrap()).unwrap());
            for crop in [None,Some([0,0,n,n])] {
                let x=before_io::image_ops::transform_image(bytes.get_ref(),&oa,crop,Some([n+2,n+1]),before_io::image_ops::ResizeFilter::Lanczos3).unwrap();
                let y=after_io::image_ops::transform_image(bytes.get_ref(),&ob,crop,Some([n+2,n+1]),after_io::image_ops::ResizeFilter::Lanczos3).unwrap();
                assert_eq!(image::load_from_memory(&x).unwrap().to_rgba8(),image::load_from_memory(&y).unwrap().to_rgba8());
            }
        }
    }
    let temp=tempfile::tempdir().unwrap();
    for chunks in [true,false] {
        let path=temp.path().join(format!("fixture-{chunks}.mcap"));
        let mut writer=mcap::WriteOptions::new().use_chunks(chunks).compression(None).create(File::create(&path).unwrap()).unwrap();
        let cid=writer.add_channel(0,"/q","json",&BTreeMap::new()).unwrap();
        writer.add_channel(0,"/empty","json",&BTreeMap::new()).unwrap();
        for i in 0..300u64 {
            writer.write_to_known_channel(&mcap::records::MessageHeader{channel_id:cid,sequence:i as u32,
                log_time:i*1_000_000,publish_time:i*1_000_000+7},
                format!(r#"{{"q":[{i},2,3],"a/b":4,"nested":{{"x":5}}}}"#).as_bytes()).unwrap();
        }
        writer.finish().unwrap();
        let cfg=serde_json::json!({"topics":["/q","/missing"],"start_ns":17000000,"end_ns":150000000});
        let ra=before_io::mcap_ops::inspect_mcap(&path,serde_json::from_value(cfg.clone()).unwrap(),Default::default(),2_000_000).unwrap();
        let rb=after_io::mcap_ops::inspect_mcap(&path,serde_json::from_value(cfg).unwrap(),Default::default(),2_000_000).unwrap();
        json(serde_json::to_value(ra).unwrap(),serde_json::to_value(rb).unwrap());
        let spec=serde_json::json!({"topic":"/q","channels":5,"fields":["/q","/a~1b","/nested/x"]});
        let da:before_io::mcap_ops::JsonSignalSpec=serde_json::from_value(spec.clone()).unwrap();
        let db:after_io::mcap_ops::JsonSignalSpec=serde_json::from_value(spec).unwrap();
        let a=before_io::mcap_ops::read_signal(&path,Default::default(),Default::default(),&da,1000).unwrap();
        let b=after_io::mcap_ops::read_signal(&path,Default::default(),Default::default(),&db,1000).unwrap();
        assert_eq!(a.timestamps(),b.timestamps());numbers(a.values(),b.values());
    }
    println!("equivalence: 180 randomized core scenarios, 10 image fixtures, 2 MCAP fixtures passed");
}
