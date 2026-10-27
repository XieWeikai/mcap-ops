# mcap_ops.align_timestamps

**语言：中文 | [English](../../../reference/python/align_timestamps.md)**

匹配源索引，不插值数值。

```python
mcap_ops.align_timestamps(source, target, *, nearest=False, max_past_ns=0, max_future_ns=0)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `source` | `int64[N]` | `required` | 连续、严格递增，单位 ns。 |
| `target` | `int64[M]` | `required` | 连续、非递减，单位 ns。 |
| `nearest` | `bool` | `False` | 允许考虑未来候选，否则仅匹配过去。 |
| `max_past_ns / max_future_ns` | `int` | `0` | 分别限制过去/未来的非负容差，单位 ns。 |

## 返回值

字典：indices int64[M]；offsets_ns int64[M] 为源时间减目标时间；valid bool[M]。无效索引为 -1，无效偏移为 0。

## 错误

dtype/连续性错误、时间无序、负容差时 ValueError；偏移无法用 int64 表示时 OverflowError。

## 语义与边界

等距时优先过去。无效偏移为零不代表精确匹配。图像索引前先检查 valid，否则 Python 的 -1 会取最后一帧。要求时钟已经可比较，不估计漂移。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
target = np.array([5, 15, 30], dtype=np.int64) * 1_000_000
r = ops.align_timestamps(t, target, max_past_ns=6_000_000)
assert r["indices"].tolist() == [0, 1, -1]
assert r["valid"].tolist() == [True, True, False]
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
