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
    extension_edges();
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
    let extra_images=[
        image::DynamicImage::ImageRgba8(image::RgbaImage::from_fn(8,7,|x,y|image::Rgba([(x*17) as u8,(y*31) as u8,93,(x+y) as u8]))),
        image::DynamicImage::ImageLuma16(image::ImageBuffer::from_fn(6,5,|x,y|image::Luma([(x*1000+y*100) as u16]))),
        image::DynamicImage::ImageRgb16(image::ImageBuffer::from_fn(7,6,|x,y|image::Rgb([(x*1000) as u16,(y*2000) as u16,65535]))),
    ];
    for image in extra_images {
        let mut encoded=Cursor::new(Vec::new());image.write_to(&mut encoded,image::ImageFormat::Png).unwrap();
        let oa=before_io::image_ops::ImageOptions::default();let ob=after_io::image_ops::ImageOptions::default();
        let a=before_io::image_ops::transform_image(encoded.get_ref(),&oa,None,Some([9,8]),before_io::image_ops::ResizeFilter::Lanczos3).unwrap();
        let b=after_io::image_ops::transform_image(encoded.get_ref(),&ob,None,Some([9,8]),after_io::image_ops::ResizeFilter::Lanczos3).unwrap();
        assert_eq!(image::load_from_memory(&a).unwrap().to_rgba16(),image::load_from_memory(&b).unwrap().to_rgba16());
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
        let many=serde_json::json!({"topics":["/z","/q","/x","/b","/empty","/a","/c","/d","/e","/f","/q"]});
        let ra=before_io::mcap_ops::inspect_mcap(&path,serde_json::from_value(many.clone()).unwrap(),Default::default(),2_000_000).unwrap();
        let rb=after_io::mcap_ops::inspect_mcap(&path,serde_json::from_value(many).unwrap(),Default::default(),2_000_000).unwrap();
        json(serde_json::to_value(ra).unwrap(),serde_json::to_value(rb).unwrap());
        let spec=serde_json::json!({"topic":"/q","channels":5,"fields":["/q","/a~1b","/nested/x"]});
        let da:before_io::mcap_ops::JsonSignalSpec=serde_json::from_value(spec.clone()).unwrap();
        let db:after_io::mcap_ops::JsonSignalSpec=serde_json::from_value(spec).unwrap();
        let a=before_io::mcap_ops::read_signal(&path,Default::default(),Default::default(),&da,1000).unwrap();
        let b=after_io::mcap_ops::read_signal(&path,Default::default(),Default::default(),&db,1000).unwrap();
        assert_eq!(a.timestamps(),b.timestamps());numbers(a.values(),b.values());
    }
    println!("equivalence: 180 randomized core scenarios, 13 image fixtures, 2 MCAP fixtures passed");
}

// Additional public-interface oracles for the twenty follow-up experiments.
fn extension_edges() {
    let extremes = [i64::MIN, i64::MIN+1, -1_000_000_001, -3, -1, 0, 1, 3,
                    1_000_000_001, i64::MAX-1, i64::MAX];
    let mut clocks = 0;
    for origin in [i64::MIN, -1_700_000_000_000_000_000, -1, 0, 1, i64::MAX] {
        for offset in [i64::MIN, -17, 0, 17, i64::MAX] {
            for rate in [i64::MIN, -1_000_000_000, -999_999_999, -500_000_000, -1200, -1, 0, 1, 1200, 500_000_000, i64::MAX] {
                // Test single timestamps too: an early overflow must not hide later tie cases.
                for t in extremes {
                    assert_eq!(before::time::map_clock(&[t],origin,offset,rate).map_err(|e|e.to_string()),
                        after::time::map_clock(&[t],origin,offset,rate).map_err(|e|e.to_string()));
                    clocks += 1;
                }
            }
        }
    }
    for (start,end) in [(0,0),(-9,11),(i64::MIN,i64::MIN+100),(i64::MAX-100,i64::MAX),
                        (i64::MIN,i64::MAX),(10,0)] {
        for (num,den) in [(0,1),(1,0),(1,1),(30_000,1001),(1_000_000_000,1),(u32::MAX,u32::MAX),(u32::MAX,1)] {
            for limit in [0,1,31,64] {
                assert_eq!(before::time::uniform_grid(start,end,num,den,limit).map_err(|e|e.to_string()),
                    after::time::uniform_grid(start,end,num,den,limit).map_err(|e|e.to_string()));
            }
        }
    }
    for times in [vec![],vec![i64::MIN],vec![0,0],vec![i64::MIN,i64::MAX],vec![9,8,8,10],vec![0,2,3,7,20]] {
        for gap in [0,3,i64::MAX] {
            let a=before::time::inspect_time(&times,gap);
            let b=after::time::inspect_time(&times,gap);
            match (a,b) {
                (Ok(a),Ok(b)) => json(serde_json::to_value(a).unwrap(),serde_json::to_value(b).unwrap()),
                (Err(a),Err(b)) => assert_eq!(a.to_string(),b.to_string()),
                _ => panic!("inspect_time result differs"),
            }
        }
        assert_eq!(before::time::require_strict(&times).map_err(|e|e.to_string()),
            after::time::require_strict(&times).map_err(|e|e.to_string()));
    }
    let mut seed=937;
    for n in [3,4,31,64,257] {
        for variant in 0..5 {
            let times:Vec<_>=(0..n).map(|i|i as i64*10+if i>n/2 {100} else {0}).collect();
            let values:Vec<f64>=(0..n).map(|i|match variant {
                0 => (rng(&mut seed)%1000) as f64,
                1 => if i%2==0 {-0.0} else {0.0},
                2 => if i%3==0 {f64::NAN} else {(i%5) as f64},
                3 => if i%2==0 {f64::MAX} else {-f64::MAX},
                _ => (i as f64*0.13).sin(),
            }).collect();
            let a=before::Signal::new(times.clone(),values.clone(),1).unwrap();
            let b=after::Signal::new(times,values,1).unwrap();
            for window in [10,50,5000] {
                let cfg=serde_json::json!({"hampel_window_ns":window,"max_gap_ns":50,"max_issues":1000});
                let qa=before::quality::inspect_signal(&a,&serde_json::from_value(cfg.clone()).unwrap()).unwrap();
                let qb=after::quality::inspect_signal(&b,&serde_json::from_value(cfg).unwrap()).unwrap();
                assert_eq!(qa.flagged_samples,qb.flagged_samples);
                json(serde_json::to_value(qa).unwrap(),serde_json::to_value(qb).unwrap());
            }
        }
    }
    for angle in [0.0_f64,0.01,0.5,1.5,3.14] {
        for scale in [0.98,0.995,1.0,1.005,1.02] {
            for sign in [-1.0,1.0] {
                let q=vec![0.0,0.0,0.0,1.0,0.0,0.0,scale*angle.sin()*sign,scale*angle.cos()*sign];
                let a=before::Signal::new(vec![0,100],q.clone(),4).unwrap();
                let b=after::Signal::new(vec![0,100],q,4).unwrap();
                sampled(before::sampling::resample(&a,&[-1,0,1,25,50,99,100,101],before::sampling::SampleOptions{
                    method:before::sampling::Method::Slerp,max_gap_ns:100,max_age_ns:100,allow_future:true}).unwrap(),
                    after::sampling::resample(&b,&[-1,0,1,25,50,99,100,101],after::sampling::SampleOptions{
                    method:after::sampling::Method::Slerp,max_gap_ns:100,max_age_ns:100,allow_future:true}).unwrap());
            }
        }
    }
    println!("extension edge oracle: {clocks} clock cases, 168 grids, 75 Hampel cases, 50 SLERP cases passed");
}
