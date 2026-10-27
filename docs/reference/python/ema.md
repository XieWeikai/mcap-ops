# mcap_ops.ema

**Language: English | [Chinese](../../zh/reference/python/ema.md)**

Apply a causal, time-aware exponential moving average.

```python
mcap_ops.ema(timestamps, values, tau_seconds, max_gap_ns)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | Contiguous 1-D source timestamps, nanoseconds. |
| `values` | `float64[N] or [N,D]` | `required` | Numeric samples; strided views accepted. |
| `tau_seconds` | `float` | `required` | Finite positive time constant in seconds. |
| `max_gap_ns` | `int` | `required` | Nonnegative reset threshold in nanoseconds. |

## Returns

Filtered dictionary: Signal fields plus valid list[bool], mode="causal", lookahead_samples=0, group_delay_samples=None. Values retain shape (N,D).

## Errors

ValueError for unordered time, invalid shape, nonpositive/nonfinite tau, or negative gap.

## Semantics and boundaries

Weight is 1-exp(-dt/tau). A gap beyond the threshold resets state to the current finite row. Any nonfinite channel invalidates the row and resets all-channel state; the next finite row restarts it. No future samples are used; EMA has no single constant group delay.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
r = ops.ema(t, x, tau_seconds=0.02, max_gap_ns=15_000_000)
assert r["valid"] == [True, True, True]
assert 0.0 < r["values"][1, 0] < 1.0
assert r["lookahead_samples"] == 0
```

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
