# mcap_ops.history_windows

**语言：中文 | [English](../../../reference/python/history_windows.md)**

按显式纳秒偏移，为每个中心时间构建历史窗口。

```python
mcap_ops.history_windows(timestamps, values, centers, offsets, *, method="previous", max_gap_ns=0, max_age_ns=0, allow_future=False)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | 连续的一维源时间戳，单位纳秒。 |
| `values` | `float64[N] or [N,D]` | `required` | 数值样本，允许非连续视图。 |
| `centers` | `int64[T]` | `required` | 连续、严格递增的中心时间。 |
| `offsets` | `int64[W]` | `required` | 连续、非空、严格递增、非正的偏移。 |
| `method` | `str` | `"previous"` | previous、nearest、linear 或 slerp。 |
| `max_gap_ns` | `int` | `0` | 两个支持样本间最大间隔，单位 ns。 |
| `max_age_ns` | `int` | `0` | 单个支持样本的最大年龄/距离，单位 ns。 |
| `allow_future` | `bool` | `False` | 是否允许使用晚于目标时刻的支持样本。 |

## 返回值

Windowed 字典：values (T,W,D)、timestamps (T,W)、centers (T,)、offsets (W,)、channels int。status、valid、source_left/right、alpha、uses_future 仍为一维 (T*W,)，请显式 reshape。

## 错误

采样契约、centers/offsets 无效时 ValueError；center+offset 或输出 shape 溢出时 OverflowError。

## 语义与边界

每个请求是 centers[i]+offsets[j]。负偏移本身不保证因果性：allow_future=True 时插值仍可能用到相对请求时刻的未来支持。历史不足时不会填充。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
r = ops.history_windows(t, x, np.array([20_000_000], dtype=np.int64),
                        np.array([-10_000_000, 0], dtype=np.int64))
assert r["values"].shape == (1, 2, 1)
assert r["valid"].shape == (2,)
assert r["valid"].reshape(1, 2).all()
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
