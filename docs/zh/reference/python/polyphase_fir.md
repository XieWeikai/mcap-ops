# mcap_ops.polyphase_fir

**语言：中文 | [English](../../../reference/python/polyphase_fir.md)**

```python
mcap_ops.polyphase_fir(values, up, down, taps)
```

输入为一段连续等间距的有限 float64 矩阵 (N,D)，N 至少 2，D 为正；up/down 为正整数倍率。taps 是按约分后升采样率设计的奇数长连续 float64 系数。算子乘以约分后的 up，输出形状为 (ceil(N*up/down),D)，第 j 行中心位于原行坐标 j*down/up，量纲不变。离线滤波会使用未来样本；超出边界按首尾两行的连线延伸。调用方须先按断流分段、确定时钟和滤波系数。

```python
import numpy as np
import mcap_ops as ops

x = np.arange(8., dtype=np.float64)[:, None]
y = ops.polyphase_fir(x, 1, 2, np.array([0.25, 0.5, 0.25]))
np.testing.assert_allclose(y[:, 0], [0., 2., 4., 6.])
```
