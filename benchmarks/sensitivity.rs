//! Additional workload sensitivity; both sides share this exact harness binary.
use std::{hint::black_box, time::Instant};

fn bench<F, T>(name: &str, mut operation: F)
where F: FnMut() -> T {
    let arguments: Vec<_> = std::env::args().collect();
    if arguments.windows(2).find(|a| a[0] == "--case")
        .is_some_and(|a| !a[1].split(',').any(|c| c == name)) {return;}
    black_box(operation());
    let millis: f64 = std::env::var("RSI_MILLIS").unwrap_or("20".into()).parse().unwrap();
    let samples: usize = std::env::var("RSI_SAMPLES").unwrap_or("7".into()).parse().unwrap();
    let mut iterations = 1;
    loop {
        let start=Instant::now();
        for _ in 0..iterations {black_box(operation());}
        if start.elapsed().as_secs_f64()*1000.0 >= millis || iterations >= 1_048_576 {break;}
        iterations *= 2;
    }
    let mut times=Vec::new();
    for _ in 0..samples {
        let start=Instant::now();
        for _ in 0..iterations {black_box(operation());}
        times.push(start.elapsed().as_secs_f64()*1e9/iterations as f64);
    }
    let mut sorted=times.clone();sorted.sort_by(f64::total_cmp);
    println!("{}",serde_json::json!({"case":name,"median_ns":sorted[samples/2],"samples_ns":times,"iterations":iterations}));
}

fn main() {
    let before = std::env::args().any(|a| a == "before");
    for (name,n,d,k,invalid) in [
        ("sensitivity.fir.short.scalar",20000,1,3,false),
        ("sensitivity.fir.short.vector",20000,6,3,false),
        ("sensitivity.fir.wide",8192,32,63,false),
        ("sensitivity.fir.small.scalar",32,1,3,false),
        ("sensitivity.fir.small.vector",32,6,31,false),
        ("sensitivity.fir.gapped",20000,6,31,true),
    ] {
        let timestamps:Vec<_>=(0..n).map(|i|i as i64*1000).collect();
        let values:Vec<_>=(0..n*d).map(|i|if invalid && (i/d)%17==0 {f64::NAN} else {(i as f64*0.01).sin()}).collect();
        let taps=vec![1.0/k as f64;k];
        if before {
            let signal=before::Signal::new(timestamps,values,d).unwrap();
            bench(name,||before::filter::fir(black_box(&signal),black_box(&taps),before::filter::FilterMode::Causal,1000,0).unwrap());
        } else {
            let signal=after::Signal::new(timestamps,values,d).unwrap();
            bench(name,||after::filter::fir(black_box(&signal),black_box(&taps),after::filter::FilterMode::Causal,1000,0).unwrap());
        }
    }
    for (name,constant) in [("sensitivity.hampel.random",false),("sensitivity.hampel.constant",true)] {
        let timestamps:Vec<_>=(0..4000).map(|i|i*1000).collect();
        let mut seed=9829u64;
        let values:Vec<_>=(0..4000).map(|_| {seed=seed.wrapping_mul(6364136223846793005).wrapping_add(1);
            if constant {17.0} else {(seed>>32) as f64/u32::MAX as f64}}).collect();
        if before {
            let signal=before::Signal::new(timestamps,values,1).unwrap();
            let config=before::quality::QualityConfig{hampel_window_ns:Some(100_000),..Default::default()};
            bench(name,||before::quality::inspect_signal(black_box(&signal),black_box(&config)).unwrap());
        } else {
            let signal=after::Signal::new(timestamps,values,1).unwrap();
            let config=after::quality::QualityConfig{hampel_window_ns:Some(100_000),..Default::default()};
            bench(name,||after::quality::inspect_signal(black_box(&signal),black_box(&config)).unwrap());
        }
    }
}
