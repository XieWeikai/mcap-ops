# mcap_ops.history_windows

**Language: English | [Chinese](../../zh/reference/python/history_windows.md)**

Gather history at each center using explicit nanosecond offsets.

```python
mcap_ops.history_windows(timestamps, values, centers, offsets, *, method="previous", max_gap_ns=0, max_age_ns=0, allow_future=False)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | Contiguous 1-D source timestamps, nanoseconds. |
| `values` | `float64[N] or [N,D]` | `required` | Numeric samples; strided views accepted. |
| `centers` | `int64[T]` | `required` | Contiguous, strictly increasing center times. |
| `offsets` | `int64[W]` | `required` | Contiguous, nonempty, strictly increasing, nonpositive offsets. |
| `method` | `str` | `"previous"` | previous, nearest, linear, or slerp. |
| `max_gap_ns` | `int` | `0` | Maximum separation of two supporting samples, ns. |
| `max_age_ns` | `int` | `0` | Maximum age/distance for single-sample support, ns. |
| `allow_future` | `bool` | `False` | Permit support later than the target time. |

## Returns

Windowed dictionary: values (T,W,D), timestamps (T,W), centers (T,), offsets (W,), channels int. status, valid, source_left/right, alpha, uses_future remain flat (T*W,). Reshape these explicitly.

## Errors

ValueError for sampling contract errors or invalid centers/offsets. OverflowError if center+offset or output shape overflows.

## Semantics and boundaries

Each request is centers[i]+offsets[j]. Negative offsets alone do not ensure causality: interpolation may still use future support relative to the requested time if allow_future=True. No padding of missing history.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
r = ops.history_windows(t, x, np.array([20_000_000], dtype=np.int64),
                        np.array([-10_000_000, 0], dtype=np.int64))
assert r["values"].shape == (1, 2, 1)
assert r["valid"].shape == (2,)
assert r["valid"].reshape(1, 2).all()
```

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
