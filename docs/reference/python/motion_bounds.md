# mcap_ops.motion_bounds

**Language: English | [Chinese](../../zh/reference/python/motion_bounds.md)**

```python
mcap_ops.motion_bounds(timestamps, values, thresholds, edge_ns)
```

Offline selection: use strictly increasing int64 timestamps in ns and finite float64 observations (N,D) or (N,). Supply D finite nonnegative float64 thresholds in source units and a nonnegative endpoint window in ns (both endpoints included). Strict departure from per-channel head/tail medians defines movement. Return original half-open row bounds with one neighbouring row on each side, clipped to the input, or None if fewer than two usable rows or no motion. No internal gap policy; provide a covered interval.

```python
import numpy as np
import mcap_ops as ops

t = np.arange(7, dtype=np.int64)
x = np.array([0., 0., 0., 2., 2., 2., 2.])
assert ops.motion_bounds(t, x, np.array([1.]), 1) == (2, 4)
```
