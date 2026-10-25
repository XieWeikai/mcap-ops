"""Python interface to the Rust MCAP operators.

The public functions return ordinary Python dictionaries/lists after the Rust
implementation has completed. Input arrays are copied into Rust-owned memory;
outputs are not aliases of caller buffers.
"""
import json

from ._native import (
    align_timestamps as _align_timestamps,
    ema as _ema,
    fir as _fir,
    history_windows as _history_windows,
    image_quality as _image_quality,
    inspect_mcap as _inspect_mcap,
    inspect_signal as _inspect_signal,
    lowpass_taps,
    package_version,
    read_json_signal as _read_json_signal,
    resample as _resample,
    transform_image,
    uniform_grid,
    unwrap_angles as _unwrap_angles,
    validate_video as _validate_video,
)

__version__ = package_version()


def _loads(value):
    return json.loads(value) if isinstance(value, str) else {key: value[key] for key in sorted(value)}


def _normalize_signal(result):
    import numpy as np
    channels = int(result["channels"])
    result["timestamps"] = np.asarray(result["timestamps"], dtype=np.int64)
    result["values"] = np.asarray(result["values"], dtype=np.float64).reshape(-1, channels)
    return result


def inspect_signal(timestamps, values, config=None):
    return _loads(_inspect_signal(timestamps, values, None if config is None else json.dumps(config)))


def resample(timestamps, values, target, *, method="previous", max_gap_ns=0, max_age_ns=0, allow_future=False):
    result = _normalize_signal(_loads(_resample(timestamps, values, target, method, max_gap_ns, max_age_ns, allow_future)))
    import numpy as np
    result["status"] = np.asarray(result["status"], dtype=np.uint8)
    result["source_left"] = np.asarray(result["source_left"], dtype=np.int64)
    result["source_right"] = np.asarray(result["source_right"], dtype=np.int64)
    result["alpha"] = np.asarray(result["alpha"], dtype=np.float64)
    result["uses_future"] = np.asarray(result["uses_future"], dtype=bool)
    result["valid"] = result["status"] == 0
    return result


def history_windows(timestamps, values, centers, offsets, *, method="previous", max_gap_ns=0, max_age_ns=0, allow_future=False):
    result = _normalize_signal(_loads(_history_windows(timestamps, values, centers, offsets, method, max_gap_ns, max_age_ns, allow_future)))
    import numpy as np
    result["centers"] = np.asarray(result["centers"], dtype=np.int64)
    result["offsets"] = np.asarray(result["offsets"], dtype=np.int64)
    result["status"] = np.asarray(result["status"], dtype=np.uint8)
    result["source_left"] = np.asarray(result["source_left"], dtype=np.int64)
    result["source_right"] = np.asarray(result["source_right"], dtype=np.int64)
    result["alpha"] = np.asarray(result["alpha"], dtype=np.float64)
    result["uses_future"] = np.asarray(result["uses_future"], dtype=bool)
    result["valid"] = result["status"] == 0
    result["values"] = result["values"].reshape(len(result["centers"]), len(result["offsets"]), result["channels"])
    result["timestamps"] = result["timestamps"].reshape(len(result["centers"]), len(result["offsets"]))
    return result


def align_timestamps(source, target, *, nearest=False, max_past_ns=0, max_future_ns=0):
    result = _loads(_align_timestamps(source, target, nearest, max_past_ns, max_future_ns))
    import numpy as np
    result["indices"] = np.asarray(result["indices"], dtype=np.int64)
    result["offsets_ns"] = np.asarray(result["offsets_ns"], dtype=np.int64)
    result["valid"] = np.asarray(result["valid"], dtype=bool)
    return result


def ema(timestamps, values, tau_seconds, max_gap_ns):
    return _normalize_signal(_loads(_ema(timestamps, values, tau_seconds, max_gap_ns)))


def fir(timestamps, values, taps, *, mode="causal", period_ns=1, tolerance_ns=0):
    return _normalize_signal(_loads(_fir(timestamps, values, taps, mode, period_ns, tolerance_ns)))


def unwrap_angles(timestamps, values, *, period=2 * 3.141592653589793, max_gap_ns=0):
    return _normalize_signal(_loads(_unwrap_angles(timestamps, values, period, max_gap_ns)))


def image_quality(data, options=None):
    return _loads(_image_quality(data, None if options is None else json.dumps(options)))


def read_json_signal(path, topic, fields, channels, *, filter=None, limits=None, timestamp_pointer=None, publish_clock=False, max_samples=10_000_000):
    result = _loads(_read_json_signal(path, topic, fields, channels,
        None if filter is None else json.dumps(filter),
        None if limits is None else json.dumps(limits), timestamp_pointer, publish_clock, max_samples))
    return _normalize_signal(result)


def inspect_mcap(path, *, filter=None, limits=None, max_gap_ns=0):
    return _loads(_inspect_mcap(path, None if filter is None else json.dumps(filter), None if limits is None else json.dumps(limits), max_gap_ns))


def validate_video(path, *, ffmpeg="ffmpeg", ffprobe="ffprobe", timeout_seconds=600.0):
    return _loads(_validate_video(path, ffmpeg, ffprobe, timeout_seconds))


__all__ = [
    "__version__", "align_timestamps", "ema", "history_windows", "image_quality",
    "inspect_mcap", "inspect_signal", "resample", "uniform_grid", "validate_video",
    "fir", "lowpass_taps", "unwrap_angles", "transform_image", "read_json_signal",
]
