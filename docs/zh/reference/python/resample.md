# mcap_ops.resample

**语言：中文 | [English](../../../reference/python/resample.md)**

重采样数值，并保留有效性和来源支持。

```python
mcap_ops.resample(timestamps, values, target, *, method="previous", max_gap_ns=0, max_age_ns=0, allow_future=False)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | 连续的一维源时间戳，单位纳秒。 |
| `values` | `float64[N] or [N,D]` | `required` | 数值样本，允许非连续视图。 |
| `target` | `int64[M]` | `required` | 连续、非递减的目标时间戳，单位 ns。 |
| `method` | `str` | `"previous"` | previous、nearest、linear 或 slerp。 |
| `max_gap_ns` | `int` | `0` | 两个支持样本间最大间隔，单位 ns。 |
| `max_age_ns` | `int` | `0` | 单个支持样本的最大年龄/距离，单位 ns。 |
| `allow_future` | `bool` | `False` | 是否允许使用晚于目标时刻的支持样本。 |

## 返回值

Sampled 字典：timestamps int64[M]、values float64[M,D]、channels int、status uint8[M]、valid bool[M]、source_left/right int64[M]、alpha float64[M]、uses_future bool[M]。参见[状态和来源契约](../types.md)。

## 错误

shape 错误、源/目标无序、未知方法、负限制、SLERP 通道不为 4 时 ValueError。单个样本不受支持时返回状态码，而非异常。

## 语义与边界

源时间必须严格递增。精确匹配不需要未来支持。单点支持检查 max_age_ns，插值检查 max_gap_ns；零是严格限制。SLERP 使用 xyzw，输入范数与 1 相差不超过 0.01，内部归一化。无效输出为 NaN，源索引为 -1。重采样不会自动抗混叠。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
target = np.array([5_000_000], dtype=np.int64)
r = ops.resample(t, x, target, method="linear", max_gap_ns=15_000_000, allow_future=True)
assert r["valid"][0] and r["uses_future"][0]
np.testing.assert_allclose(r["values"], [[0.5]])
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
