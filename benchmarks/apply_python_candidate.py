"""Apply one Python-bridge candidate; benchmarking/acceptance is separate."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from rsi_batch import function_span


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError(f"expected unique fragment: {old[:100]!r}")
    return text.replace(old, new, 1)


def revise(source, name, transform):
    start, end = function_span(source, name)
    return source[:start] + transform(source[start:end]) + source[end:]


HELPERS = '''fn numpy_values<'py>(py:Python<'py>,mut values:Vec<f64>)->Bound<'py,numpy::PyArray1<f64>> {
    // The previous JSON bridge mapped all non-finite floats to NumPy NaN.
    for value in &mut values {if !value.is_finite() {*value=f64::NAN;}}
    values.into_pyarray(py)
}

fn signal_dict(py:Python<'_>,signal:&Signal)->PyResult<Py<PyDict>> {
    let dict=PyDict::new(py);
    dict.set_item("timestamps",signal.timestamps().to_vec().into_pyarray(py))?;
    dict.set_item("values",numpy_values(py,signal.values().to_vec()))?;
    dict.set_item("channels",signal.channels())?;
    Ok(dict.unbind())
}

fn sampled_dict(py:Python<'_>,result:sampling::Sampled)->PyResult<Py<PyDict>> {
    let dict=PyDict::new(py);
    dict.set_item("timestamps",result.timestamps.into_pyarray(py))?;
    dict.set_item("values",numpy_values(py,result.values))?;
    dict.set_item("channels",result.channels)?;
    dict.set_item("status",result.status.into_pyarray(py))?;
    dict.set_item("source_left",result.source_left.into_pyarray(py))?;
    dict.set_item("source_right",result.source_right.into_pyarray(py))?;
    dict.set_item("alpha",numpy_values(py,result.alpha))?;
    dict.set_item("uses_future",result.uses_future.into_pyarray(py))?;
    Ok(dict.unbind())
}'''

FILTERED = '''fn filtered_dict(py:Python<'_>,result:filter::Filtered)->PyResult<Py<PyDict>> {
    let dict=signal_dict(py,&result.signal)?;
    dict.bind(py).set_item("valid",result.valid)?;
    dict.bind(py).set_item("mode",format!("{:?}",result.mode).to_lowercase())?;
    dict.bind(py).set_item("lookahead_samples",result.lookahead_samples)?;
    dict.bind(py).set_item("group_delay_samples",result.group_delay_samples)?;
    Ok(dict)
}'''


def round_one(source):
    source=replace_once(source,"use numpy::{PyReadonlyArray1, PyReadonlyArrayDyn};",
                        "use numpy::{IntoPyArray, PyReadonlyArray1, PyReadonlyArrayDyn};\nuse pyo3::types::PyDict;")
    source=revise(source,"sampled_json",lambda _:HELPERS)
    source=revise(source,"filtered_json",lambda _:FILTERED)
    for name in ["resample","history_windows","align_timestamps","ema","fir","unwrap_angles","read_json_signal"]:
        def change(body):
            body=replace_once(body,f"fn {name}(\n",f"fn {name}(\n    py: Python<'_>,\n")
            body=replace_once(body,"-> PyResult<String>","-> PyResult<Py<PyDict>>")
            if name=="resample":
                body="#[allow(clippy::too_many_arguments)]\n"+body
                return replace_once(body,"sampled_json(&result)","sampled_dict(py,result)")
            if name in ("ema","fir"):
                return replace_once(body,"filtered_json(&result)","filtered_dict(py,result)")
            start=body.rindex("    json(")
            if name=="history_windows":
                return body[:start]+'''    let dict=sampled_dict(py,result.samples)?;
    dict.bind(py).set_item("centers",result.centers.into_pyarray(py))?;
    dict.bind(py).set_item("offsets",result.offsets.into_pyarray(py))?;
    Ok(dict)
}'''
            if name=="align_timestamps":
                return body[:start]+'''    let dict=PyDict::new(py);
    dict.set_item("indices",result.indices.into_pyarray(py))?;
    dict.set_item("offsets_ns",result.offsets_ns.into_pyarray(py))?;
    dict.set_item("valid",result.valid.into_pyarray(py))?;
    Ok(dict.unbind())
}'''
            return body[:start]+f"    signal_dict(py,&{'signal' if name=='read_json_signal' else 'result'})\n}}"
        source=revise(source,name,change)
    return source


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("round",type=int,choices=[1,2])
    args=parser.parse_args()
    path=ROOT / "crates/python/src/lib.rs"
    source=path.read_text()
    if args.round==1:
        source=round_one(source)
        wrapper=ROOT / "python/mcap_ops/__init__.py"
        text=replace_once(wrapper.read_text(),"return json.loads(value)",
                          "return json.loads(value) if isinstance(value, str) else value")
        wrapper.write_text(text)
    else:
        source=replace_once(source,"let flat = array.iter().copied().collect();",'''let flat = if array.is_standard_layout() {
        array.as_slice().expect("standard layout has a contiguous slice").to_vec()
    } else {array.iter().copied().collect()};''')
    path.write_text(source)


if __name__=="__main__":
    main()
