# mcap_ops.lowpass_taps

**语言：中文 | [English](../../../reference/python/lowpass_taps.md)**

设计归一化、对称的 Hamming 加窗 sinc 低通系数。

```python
mcap_ops.lowpass_taps(sample_rate_hz, cutoff_hz, taps)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `sample_rate_hz` | `float` | `required` | 有限的输入采样率，Hz。 |
| `cutoff_hz` | `float` | `required` | 0 < cutoff < sample_rate/2，Hz。 |
| `taps` | `int` | `required` | [3,4095] 范围内的奇数系数数量。 |

## 返回值

长度为 taps 的 list[float]，对称且归一化为单位直流增益。传给 fir 前转换为连续 float64 数组。

## 错误

频率非有限、cutoff 不合法、tap 数为偶数或越界时 ValueError。

## 语义与边界

这里只设计系数，需另行调用 fir。降采样前根据目标 Nyquist 限制决定带宽，不会自动选择滤波策略。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

```python
import numpy as np
import mcap_ops as ops
h = np.asarray(ops.lowpass_taps(200.0, 20.0, 31), dtype=np.float64)
assert len(h) == 31
np.testing.assert_allclose(h, h[::-1])
np.testing.assert_allclose(h.sum(), 1.0)
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
