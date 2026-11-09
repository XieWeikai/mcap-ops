# mcap_ops.motion_bounds

**语言：中文 | [English](../../../reference/python/motion_bounds.md)**

```python
mcap_ops.motion_bounds(timestamps, values, thresholds, edge_ns)
```

离线选择：输入严格递增的 int64 纳秒时间、有限 float64 观测 (N,D) 或 (N,)，及每通道一个与原量同单位的非负有限阈值。edge_ns 是含端点的非负首尾窗口。任一维与端点中位数之差严格超过阈值才算动作；返回原始行的左闭右开区间，左右各多留一点，且不越界。无运动或不足两行返回 None。调用方应先验证区间的采样覆盖。

```python
import numpy as np
import mcap_ops as ops

t = np.arange(7, dtype=np.int64)
x = np.array([0., 0., 0., 2., 2., 2., 2.])
assert ops.motion_bounds(t, x, np.array([1.]), 1) == (2, 4)
```
