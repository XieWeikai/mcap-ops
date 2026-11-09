# mcap_ops.sample_support

**语言：中文 | [English](../../../reference/python/sample_support.md)**

```python
mcap_ops.sample_support(source, target, max_gap_ns)
```

输入为同一时钟的连续 int64 纳秒数组。源须严格递增，查询可以重复或乱序。非负间隙上限约束整个左右括区；精确命中总是有效，越界或空源无效。返回与查询等长的原始行索引 previous、next（缺侧为 -1）及布尔 supported。此检测可用到未来的右邻点，不会补数。

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 4, 20], dtype=np.int64)
r = ops.sample_support(t, np.array([4, 6, 21], dtype=np.int64), 5)
assert r["previous"].tolist() == [1, 1, 2]
assert r["supported"].tolist() == [True, False, False]
```
