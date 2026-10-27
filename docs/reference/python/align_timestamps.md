# mcap_ops.align_timestamps

**Language: English | [Chinese](../../zh/reference/python/align_timestamps.md)**

Match timestamps to source indices without interpolating values.

```python
mcap_ops.align_timestamps(source, target, *, nearest=False, max_past_ns=0, max_future_ns=0)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `source` | `int64[N]` | `required` | Contiguous, strictly increasing, ns. |
| `target` | `int64[M]` | `required` | Contiguous, nondecreasing, ns. |
| `nearest` | `bool` | `False` | Permit future candidates; otherwise match past only. |
| `max_past_ns / max_future_ns` | `int` | `0` | Nonnegative, separate past/future tolerances, ns. |

## Returns

dict: indices int64[M], offsets_ns int64[M] (source minus target), valid bool[M]. Invalid indices are -1 and invalid offsets are 0.

## Errors

ValueError for noncontiguous/wrong dtype arrays, unordered timestamps, or negative tolerances. OverflowError if an offset cannot fit int64.

## Semantics and boundaries

Ties prefer the past. A zero invalid offset is not an exact match. Check valid before indexing frames: Python index -1 otherwise selects the last frame. This matches already comparable clocks; it does not estimate clock drift.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
target = np.array([5, 15, 30], dtype=np.int64) * 1_000_000
r = ops.align_timestamps(t, target, max_past_ns=6_000_000)
assert r["indices"].tolist() == [0, 1, -1]
assert r["valid"].tolist() == [True, True, False]
```

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
