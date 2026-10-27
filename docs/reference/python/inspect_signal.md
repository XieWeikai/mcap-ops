# mcap_ops.inspect_signal

**Language: English | [Chinese](../../zh/reference/python/inspect_signal.md)**

Inspect timing, values, and dynamic anomalies without changing the input.

```python
mcap_ops.inspect_signal(timestamps, values, config=None)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | Contiguous 1-D source timestamps, nanoseconds. |
| `values` | `float64[N] or [N,D]` | `required` | Numeric samples; strided views accepted. |
| `config` | `dict or None` | `None` | QualityConfig fields; omitted fields use defaults below. |

### Configuration defaults

| Field | Default | Meaning |
| --- | --- | --- |
| `max_gap_ns` | `9223372036854775807` | Positive gap threshold, ns. |
| `lower / upper` | `None` | D finite bounds, in value units. |
| `max_rate / max_acceleration` | `None` | D nonnegative finite thresholds, units/s and units/s^2. |
| `hampel_window_ns` | `None` | Positive time radius on each side; can use future data. |
| `hampel_sigma` | `3.0` | Nonnegative finite MAD multiplier. |
| `hampel_min_deviation` | `0.0` | Nonnegative minimum absolute deviation. |
| `max_hampel_samples` | `4096` | Per-window cap, at least 3. |
| `flatline_duration_ns` | `None` | Positive candidate duration. |
| `flatline_tolerance` | `0.0` | Nonnegative finite value tolerance. |
| `max_issues` | `10000` | Positive stored-detail cap. |

## Returns

QualityReport dictionary: time, channels, issues, total_issues, issues_truncated, dynamic_checks_completed, flagged_sample_count. See [types](../types.md).

## Errors

ValueError for shape/configuration errors, negative gap, invalid thresholds, or per-window Hampel cap exhaustion. OverflowError for core timestamp arithmetic overflow.

## Semantics and boundaries

Original order is retained. Reversals and duplicates remain detectable; dynamic_checks_completed reports whether ordered-time dynamic checks completed. Threshold vectors must contain D finite values; scalars do not broadcast. Issue details are capped but total counts and flagged_sample_count remain complete.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
r = ops.inspect_signal(t, x, {"upper": [1.5]})
assert r["total_issues"] == 1
assert r["issues"][0]["code"] == "above_range"
```

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
