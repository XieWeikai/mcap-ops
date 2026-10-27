# mcap_ops.unwrap_angles

**Language: English | [Chinese](../../zh/reference/python/unwrap_angles.md)**

Unwrap periodic values channel by channel.

```python
mcap_ops.unwrap_angles(timestamps, values, *, period=6.283185307179586, max_gap_ns=0)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | Contiguous 1-D source timestamps, nanoseconds. |
| `values` | `float64[N] or [N,D]` | `required` | Numeric samples; strided views accepted. |
| `period` | `float` | `2*pi` | Finite positive period in the same units as values. |
| `max_gap_ns` | `int` | `0` | Nonnegative continuity threshold, ns. |

## Returns

Signal dictionary only: timestamps int64[N], values float64[N,D], channels int. There is no valid field. Python normalizes nonfinite values to NaN.

## Errors

ValueError for unordered time, shape mismatch, nonpositive/nonfinite period, or negative gap.

## Semantics and boundaries

Gaps and adjacent nonfinite values break continuity. Default max_gap_ns=0 resets across every positive interval; set it to your expected spacing tolerance. This is scalar angle unwrapping, not quaternion interpolation.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

```python
import numpy as np
import mcap_ops as ops
t = np.array([0, 10_000_000], dtype=np.int64)
r = ops.unwrap_angles(t, np.array([3.0, -3.0], dtype=np.float64), max_gap_ns=20_000_000)
np.testing.assert_allclose(r["values"][:, 0], [3.0, 2*np.pi-3.0])
assert "valid" not in r
```

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
