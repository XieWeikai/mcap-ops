# Python interface

The package is a thin, stable seam over the Rust implementation. It accepts
NumPy arrays and returns dictionaries containing NumPy arrays for numeric
operators. Input arrays are copied into Rust-owned memory; the Rust core never
mutates caller buffers.

```python
import numpy as np
import mcap_ops

timestamps = np.array([0, 10_000_000, 20_000_000], dtype=np.int64)
values = np.array([[0.0], [1.0], [2.0]], dtype=np.float64)
target = np.array([0, 5_000_000, 10_000_000], dtype=np.int64)

result = mcap_ops.resample(
    timestamps, values, target,
    method="linear",
    max_gap_ns=20_000_000,
    max_age_ns=20_000_000,
    allow_future=True,
)
# result["values"]: (3, 1), result["valid"]: (3,)
# result["source_left/right"] and result["alpha"] preserve provenance.
```

## Public groups

- `inspect_signal`: finite/range/rate/acceleration/spike/flatline evidence.
- `align_timestamps`, `resample`, `history_windows`, `uniform_grid`:
  explicit timestamp matching, interpolation, causal hold, and provenance.
- `ema`, `fir`, `lowpass_taps`, `unwrap_angles`: filters with latency and
  lookahead metadata; filters reset at non-finite values or unsupported gaps.
- `image_quality`, `transform_image`: bounded PNG/JPEG quality and transforms.
- `inspect_mcap`, `read_json_signal`: read-only MCAP inspection and an explicit
  JSON payload adapter. CDR/Protobuf belongs in an upstream decoder adapter.
- `validate_video`: complete FFmpeg decode check with bounded timeout/output.

`status == 0` is valid. Other status codes are a contract, not a request to
replace values: callers decide whether to reject a sample, keep it with a mask,
or use a provider-specific policy. A causal operation must not silently consume
future data; use `uses_future`, `lookahead_samples`, and `group_delay_samples`
when constructing training features.
