# mcap_ops.sample_support

**Language: English | [Chinese](../../zh/reference/python/sample_support.md)**

```python
mcap_ops.sample_support(source, target, max_gap_ns)
```

Both timestamp arrays are contiguous int64 nanoseconds from the same clock. Source is strictly increasing; targets may repeat or arrive out of order. A nonnegative gap limit applies to the whole bracket. Exact samples always pass; outside or empty support fails. Returns int64 previous/next original row indices (-1 if missing), and a bool supported mask in target order. No values are imputed. A future right neighbour makes this an offline observation check.

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 4, 20], dtype=np.int64)
r = ops.sample_support(t, np.array([4, 6, 21], dtype=np.int64), 5)
assert r["previous"].tolist() == [1, 1, 2]
assert r["supported"].tolist() == [True, False, False]
```
