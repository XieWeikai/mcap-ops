# mcap_ops.resample

**Language: English | [Chinese](../../zh/reference/python/resample.md)**

Sample values while retaining validity and source support.

```python
mcap_ops.resample(timestamps, values, target, *, method="previous", max_gap_ns=0, max_age_ns=0, allow_future=False)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | Contiguous 1-D source timestamps, nanoseconds. |
| `values` | `float64[N] or [N,D]` | `required` | Numeric samples; strided views accepted. |
| `target` | `int64[M]` | `required` | Contiguous, nondecreasing target timestamps, ns. |
| `method` | `str` | `"previous"` | previous, nearest, linear, or slerp. |
| `max_gap_ns` | `int` | `0` | Maximum separation of two supporting samples, ns. |
| `max_age_ns` | `int` | `0` | Maximum age/distance for single-sample support, ns. |
| `allow_future` | `bool` | `False` | Permit support later than the target time. |

## Returns

Sampled dictionary: timestamps int64[M], values float64[M,D], channels int, status uint8[M], valid bool[M], source_left/right int64[M], alpha float64[M], uses_future bool[M]. See [status and support contracts](../types.md).

## Errors

ValueError for invalid shapes, unordered sources/targets, unknown methods, negative limits, or SLERP channel count other than 4. Unsupported individual samples return status codes, not an exception.

## Semantics and boundaries

Source timestamps must be strictly increasing. Exact matches need no future support. Single-point support checks max_age_ns; interpolation checks max_gap_ns. Zero limits are strict. SLERP expects xyzw with norm within 0.01 of one and normalizes internally. Invalid outputs contain NaN and source indices -1. Resampling does not anti-alias.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
target = np.array([5_000_000], dtype=np.int64)
r = ops.resample(t, x, target, method="linear", max_gap_ns=15_000_000, allow_future=True)
assert r["valid"][0] and r["uses_future"][0]
np.testing.assert_allclose(r["values"], [[0.5]])
```

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
