use mcap_ops_core::{Signal, filter::*, quality::*, sampling::*, selection::*, time::*};
use proptest::prelude::*;

fn signal(times:&[i64],values:&[f64])->Signal {Signal::new(times.to_vec(),values.to_vec(),1).unwrap()}
fn options(method:Method)->SampleOptions {SampleOptions{method,max_gap_ns:20,max_age_ns:10,allow_future:true}}

#[test]
fn grid_preserves_epoch_and_half_open_end() {
    let start=1_700_000_000_000_000_003;
    let grid=uniform_grid(start,start+100_000_000,30,1,10).unwrap();
    assert_eq!(grid,vec![start,start+33_333_333,start+66_666_667]);
    assert!(uniform_grid(0,100,1_000_000_000,1,4).is_err());
    assert!(uniform_grid(0,100,0,1,4).is_err());
}

#[test]
fn fractional_rate_does_not_accumulate_rounding() {
    let grid=uniform_grid(0,200_000_000_000,30_000,1001,7000).unwrap();
    assert_eq!(grid[3000],100_100_000_000);
}

#[test]
fn clock_correction_and_overflow() {
    assert_eq!(map_clock(&[0,1_000_000_000],0,50,1000).unwrap(),vec![50,1_000_001_050]);
    assert!(map_clock(&[i64::MAX],0,1,0).is_err());
    assert!(map_clock(&[1],0,0,-1_000_000_000).is_err());
}

#[test]
fn audit_keeps_reversals_and_duplicates() {
    let stats=inspect_time(&[0,10,10,8,40],15).unwrap();
    assert_eq!((stats.reversals,stats.duplicates,stats.gaps),(1,1,1));
    assert!(resample(&signal(&[0,10,10],&[1.,2.,3.]),&[5],options(Method::Linear)).is_err());
}

#[test]
fn previous_is_causal_age_limited_and_never_zero_fills() {
    let s=signal(&[10,20],&[1.,2.]);
    let out=resample(&s,&[0,10,19,25,31],options(Method::Previous)).unwrap();
    assert_eq!(out.valid(),vec![false,true,true,true,false]);
    assert_eq!(out.source_left,vec![-1,0,0,1,-1]);
    assert!(out.values[0].is_nan() && out.values[4].is_nan());
    assert!(!out.uses_future.iter().any(|v|*v));
}

#[test]
fn linear_exact_endpoints_survive_a_gap() {
    let s=signal(&[0,10,100],&[0.,10.,100.]);
    let out=resample(&s,&[0,5,10,50,100],options(Method::Linear)).unwrap();
    assert_eq!(out.valid(),vec![true,true,true,false,true]);
    assert_eq!(out.values[1],5.);
    assert_eq!(out.alpha[1],0.5);
    assert_eq!(out.status[3],Status::Gap as u8);
}

#[test]
fn causal_mode_rejects_future_interpolation() {
    let opts=SampleOptions{allow_future:false,..options(Method::Linear)};
    let out=resample(&signal(&[0,10],&[0.,1.]),&[0,5,10],opts).unwrap();
    assert_eq!(out.status,vec![0,Status::Future as u8,0]);
}

#[test]
fn nearest_ties_choose_past_and_before_start_respects_future_policy() {
    let s=signal(&[10,20],&[1.,2.]);
    let out=resample(&s,&[9,15,19],options(Method::Nearest)).unwrap();
    assert_eq!(out.source_left,vec![0,0,1]);
    assert_eq!(out.uses_future,vec![true,false,true]);
    let out=resample(&s,&[9,19],SampleOptions{allow_future:false,..options(Method::Nearest)}).unwrap();
    assert_eq!(out.source_left,vec![-1,0]);
}

#[test]
fn nonfinite_support_is_invalid() {
    let out=resample(&signal(&[0,10,20],&[0.,f64::NAN,20.]),&[0,5,10,15,20],options(Method::Linear)).unwrap();
    assert_eq!(out.valid(),vec![true,false,false,false,true]);
}

#[test]
fn quaternion_shortest_path_and_invalid_norm() {
    let s=Signal::new(vec![0,10],vec![0.,0.,0.,1.,0.,0.,0.,-1.],4).unwrap();
    let out=resample(&s,&[5],options(Method::Slerp)).unwrap();
    assert!(out.valid()[0]);
    assert!((out.values[3].abs()-1.).abs()<1e-12);
    let s=Signal::new(vec![0],vec![0.,0.,0.,0.],4).unwrap();
    assert_eq!(resample(&s,&[0],options(Method::Slerp)).unwrap().status[0],Status::InvalidQuaternion as u8);
}

#[test]
fn overlapping_history_preserves_order_and_provenance() {
    let s=signal(&[0,5,10,15,20],&[0.,5.,10.,15.,20.]);
    let out=history_windows(&s,&[10,15],&[-10,-5,0],options(Method::Previous)).unwrap();
    assert_eq!(out.samples.timestamps,vec![0,5,10,5,10,15]);
    assert_eq!(out.samples.source_left,vec![0,1,2,1,2,3]);
    assert!(history_windows(&s,&[10],&[1],options(Method::Previous)).is_err());
}

#[test]
fn empty_signal_and_shape_contracts() {
    assert!(Signal::new(vec![1],vec![1.,2.],1).is_err());
    let s=Signal::new(vec![],vec![],3).unwrap();
    let out=resample(&s,&[1,2],options(Method::Previous)).unwrap();
    assert_eq!(out.values.len(),6);
    assert_eq!(out.valid(),vec![false,false]);
}

#[test]
fn full_width_timestamp_distances_do_not_wrap() {
    let s=signal(&[i64::MIN+1,i64::MAX-1],&[1.,2.]);
    let out=resample(&s,&[0],options(Method::Linear)).unwrap();
    assert_eq!(out.status[0],Status::Gap as u8);
}

#[test]
fn quality_caps_details_not_gate_evidence() {
    let s=signal(&[0,10,20],&[f64::NAN,10.,20.]);
    let cfg=QualityConfig{upper:Some(vec![5.]),max_issues:1,..Default::default()};
    let r=inspect_signal(&s,&cfg).unwrap();
    assert_eq!(r.total_issues,3);
    assert_eq!(r.flagged_sample_count,3);
    assert!(r.issues_truncated);
    let d=gate(&r,&GatePolicy{reject_codes:vec![IssueCode::AboveRange],max_flagged_fraction:1.0,min_samples:1}).unwrap();
    assert!(!d.passed);
}

#[test]
fn numeric_summary_ignores_nonfinite_but_reports_it() {
    let r=inspect_signal(&signal(&[0,1,2],&[1.,3.,f64::INFINITY]),&QualityConfig::default()).unwrap();
    assert_eq!(r.channels[0].finite,2);
    assert_eq!(r.channels[0].mean,Some(2.));
    assert_eq!(r.channels[0].std,Some(1.));
}

#[test]
fn robust_spike_is_not_automatically_removed() {
    let s=signal(&[0,10,20,30,40],&[1.,1.,50.,1.,1.]);
    let cfg=QualityConfig{hampel_window_ns:Some(20),..Default::default()};
    let r=inspect_signal(&s,&cfg).unwrap();
    assert!(r.issues.iter().any(|i|i.code==IssueCode::Spike && i.start_index==2));
    assert_eq!(s.values()[2],50.);
    assert!(gate(&r,&GatePolicy{reject_codes:vec![],max_flagged_fraction:1.,min_samples:1}).unwrap().passed);
}

#[test]
fn rate_uses_actual_dt_and_does_not_cross_gaps() {
    let s=signal(&[0,1_000_000_000,11_000_000_000],&[0.,2.,100.]);
    let r=inspect_signal(&s,&QualityConfig{max_gap_ns:2_000_000_000,max_rate:Some(vec![1.]),..Default::default()}).unwrap();
    assert_eq!(r.issues.iter().filter(|i|i.code==IssueCode::Rate).count(),1);
}

#[test]
fn flatline_duration_and_gap_boundaries() {
    let s=signal(&[0,10,20,100,110],&[2.,2.,2.,2.,2.]);
    let r=inspect_signal(&s,&QualityConfig{max_gap_ns:15,flatline_duration_ns:Some(20),..Default::default()}).unwrap();
    let events:Vec<_>=r.issues.iter().filter(|i|i.code==IssueCode::Flatline).collect();
    assert_eq!(events.len(),1);
    assert_eq!(events[0].end_index_exclusive,3);
}

#[test]
fn malformed_clock_skips_dynamic_checks_but_keeps_finite_check() {
    let r=inspect_signal(&signal(&[2,1],&[0.,f64::NAN]),&QualityConfig{max_rate:Some(vec![0.]),..Default::default()}).unwrap();
    assert!(!r.dynamic_checks_completed);
    assert!(r.all_codes.contains(&IssueCode::ClockReversal));
    assert!(r.all_codes.contains(&IssueCode::NonFinite));
}

#[test]
fn selection_is_half_open_and_never_retimes() {
    let a=IntervalSet::new(vec![Interval{start_ns:10,end_ns:20},Interval{start_ns:0,end_ns:10}]).unwrap();
    assert_eq!(a.mask(&[-1,0,19,20]),vec![false,true,true,false]);
    let b=IntervalSet::new(vec![Interval{start_ns:5,end_ns:15}]).unwrap();
    assert_eq!(a.difference(&b).intervals(),&[Interval{start_ns:0,end_ns:5},Interval{start_ns:15,end_ns:20}]);
    assert_eq!(a.intersection(&b).intervals(),b.intervals());
    assert_eq!(b.affected_centers(3,2).unwrap().intervals(),&[Interval{start_ns:3,end_ns:18}]);
}

#[test]
fn ema_causal_reset_and_no_future_dependency() {
    let s=signal(&[0,1_000_000_000,10_000_000_000],&[0.,1.,4.]);
    let out=ema(&s,1.,2_000_000_000).unwrap();
    assert!((out.signal.values()[1]-(1.-(-1f64).exp())).abs()<1e-12);
    assert_eq!(out.signal.values()[2],4.);
    assert_eq!(out.lookahead_samples,0);
    assert_eq!(out.group_delay_samples,None);
}

#[test]
fn fir_marks_edges_gaps_and_delay() {
    let s=signal(&[0,10,20,30,100,110,120],&[1.;7]);
    let out=fir(&s,&[0.25,0.5,0.25],FilterMode::Causal,10,0).unwrap();
    assert_eq!(out.valid,vec![false,false,true,true,false,false,true]);
    assert_eq!(out.group_delay_samples,Some(1.));
    let centered=fir(&s,&[0.25,0.5,0.25],FilterMode::Centered,10,0).unwrap();
    assert_eq!(centered.lookahead_samples,1);
}

#[test]
fn lowpass_coefficients_preserve_dc() {
    let taps=lowpass_taps(200.,20.,31).unwrap();
    assert!((taps.iter().sum::<f64>()-1.).abs()<1e-12);
    assert!(lowpass_taps(100.,50.,31).is_err());
}

#[test]
fn unwrap_resets_after_missing_values() {
    let s=signal(&[0,1,2,3],&[3.1,-3.1,f64::NAN,-3.]);
    let out=unwrap_angles(&s,std::f64::consts::TAU,10).unwrap();
    assert!(out.values()[1]>3.1);
    assert_eq!(out.values()[3],-3.);
}

proptest! {
    #[test]
    fn exact_samples_are_identity(values in prop::collection::vec(-1000f64..1000.,1..128)) {
        let times:Vec<_>=(0..values.len()).map(|i|i as i64*100).collect();
        let s=signal(&times,&values);
        let out=resample(&s,&times,options(Method::Linear)).unwrap();
        prop_assert_eq!(&out.values,&values);
        prop_assert!(out.valid().iter().all(|v|*v));
    }
    #[test]
    fn causal_sampling_never_references_future(targets in prop::collection::vec(-100i64..1100,0..200)) {
        let times:Vec<_>=(0..100).map(|i|i*10).collect();
        let s=signal(&times,&vec![1.;100]);let mut targets=targets;targets.sort_unstable();
        let out=resample(&s,&targets,options(Method::Previous)).unwrap();
        for (i,&index) in out.source_left.iter().enumerate() {
            if index>=0 {prop_assert!(times[index as usize]<=targets[i]);}
        }
    }
}
