# mcap_ops.fir

**语言：中文 | [English](../../../reference/python/fir.md)**

使用有明确支持范围的 FIR 处理规则时间网格。

```python
mcap_ops.fir(timestamps, values, taps, *, mode="causal", period_ns=1, tolerance_ns=0)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | 连续的一维源时间戳，单位纳秒。 |
| `values` | `float64[N] or [N,D]` | `required` | 数值样本，允许非连续视图。 |
| `taps` | `float64[K]` | `required` | 连续有限系数，1 <= K <= 4095。 |
| `mode` | `str` | `"causal"` | causal 或 centered，centered 要求 K 为奇数。 |
| `period_ns` | `int` | `1` | 期望的正输入周期，单位 ns。 |
| `tolerance_ns` | `int` | `0` | 0 <= tolerance < period，时间间隔容差，单位 ns。 |

## 返回值

Filtered 字典：timestamps int64[N]、values float64[N,D]、channels、valid list[bool]、mode、lookahead_samples、group_delay_samples（float 或 None）。

## 错误

时间无序、系数/周期/容差非法、居中模式系数为偶数时 ValueError。不规则/缺失支持会使相应输出无效。

## 语义与边界

因果输出 i 为 sum(taps[k] * x[i-k])。居中模式将输出前移 floor(K/2)。边缘不填充，gap 和非有限行会重置支持。对称因果系数报告 (K-1)/2 延迟，非对称因果系数报告 None；居中模式延迟为 0，但有 K//2 前视。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
r = ops.fir(t, x, np.array([0.5, 0.5], dtype=np.float64), period_ns=10_000_000)
assert r["valid"] == [False, True, True]
np.testing.assert_allclose(r["values"][1:, 0], [0.5, 1.5])
assert r["group_delay_samples"] == 0.5
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
