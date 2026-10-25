//! Stable Python seam over the Rust implementations.
use mcap_ops_core::{filter, quality, sampling, time, Signal};
use mcap_ops_io::{image_ops, mcap_ops, video};
use numpy::{PyReadonlyArray1, PyReadonlyArrayDyn};
use pyo3::{exceptions::{PyIOError, PyValueError}, prelude::*};
use serde::de::DeserializeOwned;
use std::{ffi::OsStr, time::Duration};

fn json<T: serde::Serialize>(value: &T) -> PyResult<String> {
    serde_json::to_string(value).map_err(|error| PyValueError::new_err(error.to_string()))
}
fn parse<T: DeserializeOwned + Default>(value: Option<&str>) -> PyResult<T> {
    value.map_or_else(|| Ok(T::default()), |raw| serde_json::from_str(raw)
        .map_err(|error| PyValueError::new_err(error.to_string())))
}
fn signal_from_arrays(timestamps: PyReadonlyArray1<'_, i64>, values: PyReadonlyArrayDyn<'_, f64>) -> PyResult<Signal> {
    let times = timestamps.as_slice().map_err(|error| PyValueError::new_err(error.to_string()))?.to_vec();
    let array = values.as_array();
    let channels = match array.ndim() { 1 => 1, 2 => array.shape()[1], _ => return Err(PyValueError::new_err("values must be 1-D or 2-D")) };
    let flat = array.iter().copied().collect();
    Signal::new(times, flat, channels).map_err(|error| PyValueError::new_err(error.to_string()))
}
fn map_core_error(error: mcap_ops_core::Error) -> PyErr { PyValueError::new_err(error.to_string()) }
fn methods(value: &str) -> PyResult<sampling::Method> {
    match value { "previous" => Ok(sampling::Method::Previous), "nearest" => Ok(sampling::Method::Nearest),
        "linear" => Ok(sampling::Method::Linear), "slerp" => Ok(sampling::Method::Slerp),
        _ => Err(PyValueError::new_err("method must be previous, nearest, linear, or slerp")) }
}

fn sampled_json(result: &sampling::Sampled) -> PyResult<String> {
    json(&serde_json::json!({
        "timestamps": result.timestamps,
        "values": result.values,
        "channels": result.channels,
        "status": result.status,
        "source_left": result.source_left,
        "source_right": result.source_right,
        "alpha": result.alpha,
        "uses_future": result.uses_future,
    }))
}

fn filtered_json(result: &filter::Filtered) -> PyResult<String> {
    json(&serde_json::json!({
        "timestamps": result.signal.timestamps(),
        "values": result.signal.values(),
        "channels": result.signal.channels(),
        "valid": result.valid,
        "mode": format!("{:?}", result.mode).to_lowercase(),
        "lookahead_samples": result.lookahead_samples,
        "group_delay_samples": result.group_delay_samples,
    }))
}

#[pyfunction]
#[pyo3(signature=(timestamps, values, config_json=None))]
fn inspect_signal(timestamps: PyReadonlyArray1<'_, i64>, values: PyReadonlyArrayDyn<'_, f64>, config_json: Option<&str>) -> PyResult<String> {
    let signal=signal_from_arrays(timestamps,values)?;let config:quality::QualityConfig=parse(config_json)?;
    json(&quality::inspect_signal(&signal,&config).map_err(map_core_error)?)
}

#[pyfunction]
#[pyo3(signature=(timestamps, values, target, method="previous", max_gap_ns=0, max_age_ns=0, allow_future=false))]
fn resample(timestamps: PyReadonlyArray1<'_, i64>, values: PyReadonlyArrayDyn<'_, f64>, target: PyReadonlyArray1<'_, i64>, method: &str, max_gap_ns: i64, max_age_ns: i64, allow_future: bool) -> PyResult<String> {
    let signal=signal_from_arrays(timestamps,values)?;
    let options=sampling::SampleOptions{method:methods(method)?,max_gap_ns,max_age_ns,allow_future};
    let result=sampling::resample(&signal,target.as_slice().map_err(|e|PyValueError::new_err(e.to_string()))?,options).map_err(map_core_error)?;
    sampled_json(&result)
}

#[pyfunction]
#[pyo3(signature=(timestamps, values, centers, offsets, method="previous", max_gap_ns=0, max_age_ns=0, allow_future=false))]
#[allow(clippy::too_many_arguments)]
fn history_windows(timestamps: PyReadonlyArray1<'_, i64>, values: PyReadonlyArrayDyn<'_, f64>, centers: PyReadonlyArray1<'_, i64>, offsets: PyReadonlyArray1<'_, i64>, method: &str, max_gap_ns: i64, max_age_ns: i64, allow_future: bool) -> PyResult<String> {
    let signal=signal_from_arrays(timestamps,values)?;let options=sampling::SampleOptions{method:methods(method)?,max_gap_ns,max_age_ns,allow_future};
    let result=sampling::history_windows(&signal,centers.as_slice().map_err(|e|PyValueError::new_err(e.to_string()))?,offsets.as_slice().map_err(|e|PyValueError::new_err(e.to_string()))?,options).map_err(map_core_error)?;
    json(&serde_json::json!({"centers":result.centers,"offsets":result.offsets,"timestamps":result.samples.timestamps,"values":result.samples.values,"channels":result.samples.channels,"status":result.samples.status,"source_left":result.samples.source_left,"source_right":result.samples.source_right,"alpha":result.samples.alpha,"uses_future":result.samples.uses_future}))
}

#[pyfunction]
fn align_timestamps(source: PyReadonlyArray1<'_, i64>, target: PyReadonlyArray1<'_, i64>, nearest: bool, max_past_ns: i64, max_future_ns: i64) -> PyResult<String> {
    let result=time::align_timestamps(source.as_slice().map_err(|e|PyValueError::new_err(e.to_string()))?,target.as_slice().map_err(|e|PyValueError::new_err(e.to_string()))?,nearest,max_past_ns,max_future_ns).map_err(map_core_error)?;
    json(&serde_json::json!({"indices":result.indices,"offsets_ns":result.offsets_ns,"valid":result.valid}))
}

#[pyfunction]
fn uniform_grid(start_ns: i64, end_ns: i64, rate_num: u32, rate_den: u32, max_points: usize) -> PyResult<Vec<i64>> {
    time::uniform_grid(start_ns,end_ns,rate_num,rate_den,max_points).map_err(map_core_error)
}

#[pyfunction]
#[pyo3(signature=(timestamps, values, tau_seconds, max_gap_ns))]
fn ema(timestamps: PyReadonlyArray1<'_, i64>, values: PyReadonlyArrayDyn<'_, f64>, tau_seconds: f64, max_gap_ns: i64) -> PyResult<String> {
    let signal=signal_from_arrays(timestamps,values)?;let result=filter::ema(&signal,tau_seconds,max_gap_ns).map_err(map_core_error)?;
    filtered_json(&result)
}

#[pyfunction]
#[pyo3(signature=(timestamps, values, taps, mode="causal", period_ns=1, tolerance_ns=0))]
fn fir(timestamps: PyReadonlyArray1<'_, i64>, values: PyReadonlyArrayDyn<'_, f64>, taps: PyReadonlyArray1<'_, f64>, mode: &str, period_ns: i64, tolerance_ns: i64) -> PyResult<String> {
    let signal=signal_from_arrays(timestamps,values)?;
    let filter_mode=match mode {"causal"=>filter::FilterMode::Causal,"centered"=>filter::FilterMode::Centered,_=>return Err(PyValueError::new_err("mode must be causal or centered"))};
    let result=filter::fir(&signal,taps.as_slice().map_err(|e|PyValueError::new_err(e.to_string()))?,filter_mode,period_ns,tolerance_ns).map_err(map_core_error)?;
    filtered_json(&result)
}

#[pyfunction]
fn lowpass_taps(sample_rate_hz: f64, cutoff_hz: f64, taps: usize) -> PyResult<Vec<f64>> {
    filter::lowpass_taps(sample_rate_hz,cutoff_hz,taps).map_err(map_core_error)
}

#[pyfunction]
#[pyo3(signature=(timestamps, values, period=std::f64::consts::TAU, max_gap_ns=0))]
fn unwrap_angles(timestamps: PyReadonlyArray1<'_, i64>, values: PyReadonlyArrayDyn<'_, f64>, period: f64, max_gap_ns: i64) -> PyResult<String> {
    let signal=signal_from_arrays(timestamps,values)?;let result=filter::unwrap_angles(&signal,period,max_gap_ns).map_err(map_core_error)?;
    json(&serde_json::json!({"timestamps":result.timestamps(),"values":result.values(),"channels":result.channels()}))
}

#[pyfunction]
fn image_quality(bytes: &[u8], options_json: Option<&str>) -> PyResult<String> {
    let options:image_ops::ImageOptions=parse(options_json)?;json(&image_ops::image_quality(bytes,&options).map_err(|e|PyValueError::new_err(e.to_string()))?)
}

#[pyfunction]
#[pyo3(signature=(bytes, options_json=None, crop=None, resize=None, filter="lanczos3"))]
fn transform_image(bytes: &[u8], options_json: Option<&str>, crop: Option<Vec<u32>>, resize: Option<Vec<u32>>, filter: &str) -> PyResult<Vec<u8>> {
    let options:image_ops::ImageOptions=parse(options_json)?;
    let crop=crop.map(|v|{if v.len()!=4{return Err(PyValueError::new_err("crop must have four integers"));}Ok([v[0],v[1],v[2],v[3]])}).transpose()?;
    let resize=resize.map(|v|{if v.len()!=2{return Err(PyValueError::new_err("resize must have two integers"));}Ok([v[0],v[1]])}).transpose()?;
    let resize_filter=match filter {"nearest"=>image_ops::ResizeFilter::Nearest,"triangle"=>image_ops::ResizeFilter::Triangle,"lanczos3"=>image_ops::ResizeFilter::Lanczos3,_=>return Err(PyValueError::new_err("filter must be nearest, triangle, or lanczos3"))};
    image_ops::transform_image(bytes,&options,crop,resize,resize_filter).map_err(|e|PyValueError::new_err(e.to_string()))
}

#[pyfunction]
#[pyo3(signature=(path, filter_json=None, limits_json=None, max_gap_ns=0))]
fn inspect_mcap(path: &str, filter_json: Option<&str>, limits_json: Option<&str>, max_gap_ns: i64) -> PyResult<String> {
    let filter:mcap_ops::MessageFilter=parse(filter_json)?;let limits:mcap_ops::ReadLimits=parse(limits_json)?;
    json(&mcap_ops::inspect_mcap(path,filter,limits,max_gap_ns).map_err(|e|PyIOError::new_err(e.to_string()))?)
}

#[pyfunction]
#[pyo3(signature=(path, topic, fields, channels, filter_json=None, limits_json=None, timestamp_pointer=None, publish_clock=false, max_samples=10000000))]
#[allow(clippy::too_many_arguments)]
fn read_json_signal(path: &str, topic: &str, fields: Vec<String>, channels: usize, filter_json: Option<&str>, limits_json: Option<&str>, timestamp_pointer: Option<String>, publish_clock: bool, max_samples: usize) -> PyResult<String> {
    let filter:mcap_ops::MessageFilter=parse(filter_json)?;let limits:mcap_ops::ReadLimits=parse(limits_json)?;
    let decoder=mcap_ops::JsonSignalSpec{topic:topic.to_string(),fields,channels,timestamp_pointer,publish_clock};
    let signal=mcap_ops::read_signal(path,filter,limits,&decoder,max_samples).map_err(|e|PyIOError::new_err(e.to_string()))?;
    json(&serde_json::json!({"timestamps":signal.timestamps(),"values":signal.values(),"channels":signal.channels()}))
}

#[pyfunction]
#[pyo3(signature=(path, ffmpeg="ffmpeg", ffprobe="ffprobe", timeout_seconds=600.0))]
fn validate_video(path: &str, ffmpeg: &str, ffprobe: &str, timeout_seconds: f64) -> PyResult<String> {
    if !timeout_seconds.is_finite() || timeout_seconds<=0.0 {return Err(PyValueError::new_err("timeout_seconds must be positive"));}
    let report=video::validate_video(path,OsStr::new(ffmpeg),OsStr::new(ffprobe),Duration::from_secs_f64(timeout_seconds))
        .map_err(|e|PyIOError::new_err(e.to_string()))?;json(&report)
}

#[pyfunction]
fn package_version() -> &'static str {env!("CARGO_PKG_VERSION")}

#[pymodule]
fn _native(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(inspect_signal,module)?)?;
    module.add_function(wrap_pyfunction!(resample,module)?)?;
    module.add_function(wrap_pyfunction!(history_windows,module)?)?;
    module.add_function(wrap_pyfunction!(align_timestamps,module)?)?;
    module.add_function(wrap_pyfunction!(uniform_grid,module)?)?;
    module.add_function(wrap_pyfunction!(ema,module)?)?;
    module.add_function(wrap_pyfunction!(fir,module)?)?;
    module.add_function(wrap_pyfunction!(lowpass_taps,module)?)?;
    module.add_function(wrap_pyfunction!(unwrap_angles,module)?)?;
    module.add_function(wrap_pyfunction!(image_quality,module)?)?;
    module.add_function(wrap_pyfunction!(transform_image,module)?)?;
    module.add_function(wrap_pyfunction!(inspect_mcap,module)?)?;
    module.add_function(wrap_pyfunction!(read_json_signal,module)?)?;
    module.add_function(wrap_pyfunction!(validate_video,module)?)?;
    module.add_function(wrap_pyfunction!(package_version,module)?)?;
    Ok(())
}
