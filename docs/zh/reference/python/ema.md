# mcap_ops.ema

**语言：中文 | [English](../../../reference/python/ema.md)**

应用因果、感知实际时间间隔的指数移动平均。

```python
mcap_ops.ema(timestamps, values, tau_seconds, max_gap_ns)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | 连续的一维源时间戳，单位纳秒。 |
| `values` | `float64[N] or [N,D]` | `required` | 数值样本，允许非连续视图。 |
| `tau_seconds` | `float` | `required` | 有限正时间常数，单位秒。 |
| `max_gap_ns` | `int` | `required` | 非负的状态重置 gap 阈值，单位纳秒。 |

## 返回值

Filtered 字典：Signal 字段，以及 valid list[bool]、mode="causal"、lookahead_samples=0、group_delay_samples=None。数值 shape 为 (N,D)。

## 错误

时间无序、shape 错误、tau 非正/非有限、gap 为负时 ValueError。

## 语义与边界

权重为 1-exp(-dt/tau)。超过 gap 阈值后以当前有限行重新开始。任一通道非有限会使整行无效并重置所有通道状态，下一有限行重新开始。不使用未来样本；EMA 没有单一常数群延迟。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
r = ops.ema(t, x, tau_seconds=0.02, max_gap_ns=15_000_000)
assert r["valid"] == [True, True, True]
assert 0.0 < r["values"][1, 0] < 1.0
assert r["lookahead_samples"] == 0
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
