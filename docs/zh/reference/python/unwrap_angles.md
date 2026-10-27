# mcap_ops.unwrap_angles

**语言：中文 | [English](../../../reference/python/unwrap_angles.md)**

逐通道展开周期角度。

```python
mcap_ops.unwrap_angles(timestamps, values, *, period=6.283185307179586, max_gap_ns=0)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | 连续的一维源时间戳，单位纳秒。 |
| `values` | `float64[N] or [N,D]` | `required` | 数值样本，允许非连续视图。 |
| `period` | `float` | `2*pi` | 有限正周期，单位与 values 一致。 |
| `max_gap_ns` | `int` | `0` | 连续性判断的非负阈值，单位 ns。 |

## 返回值

仅返回 Signal 字典：timestamps int64[N]、values float64[N,D]、channels int，没有 valid 字段。Python 将非有限值归一化为 NaN。

## 错误

时间无序、shape 不匹配、周期非正/非有限、gap 为负时 ValueError。

## 语义与边界

gap 和相邻非有限值会打断连续性。默认 max_gap_ns=0 会在每个正间隔重置，应按预期采样间隔设置。这是标量角度展开，不是四元数插值。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

```python
import numpy as np
import mcap_ops as ops
t = np.array([0, 10_000_000], dtype=np.int64)
r = ops.unwrap_angles(t, np.array([3.0, -3.0], dtype=np.float64), max_gap_ns=20_000_000)
np.testing.assert_allclose(r["values"][:, 0], [3.0, 2*np.pi-3.0])
assert "valid" not in r
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
