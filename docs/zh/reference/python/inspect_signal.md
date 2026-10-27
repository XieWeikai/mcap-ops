# mcap_ops.inspect_signal

**语言：中文 | [English](../../../reference/python/inspect_signal.md)**

检测时间、数值和动态异常，不修改输入。

```python
mcap_ops.inspect_signal(timestamps, values, config=None)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | 连续的一维源时间戳，单位纳秒。 |
| `values` | `float64[N] or [N,D]` | `required` | 数值样本，允许非连续视图。 |
| `config` | `dict or None` | `None` | QualityConfig 字段，省略的字段使用下列默认值。 |

### 配置默认值

| 字段 | 默认值 | 含义 |
| --- | --- | --- |
| `max_gap_ns` | `9223372036854775807` | 正 gap 阈值，ns。 |
| `lower / upper` | `None` | D 个有限上下界，与数值同单位。 |
| `max_rate / max_acceleration` | `None` | D 个非负有限阈值，单位分别为 数值单位/s 和 数值单位/s^2。 |
| `hampel_window_ns` | `None` | 两侧的正时间半径，可能使用未来数据。 |
| `hampel_sigma` | `3.0` | 非负有限 MAD 倍数。 |
| `hampel_min_deviation` | `0.0` | 非负的最小绝对偏差。 |
| `max_hampel_samples` | `4096` | 每窗口上限，至少 3。 |
| `flatline_duration_ns` | `None` | 正的候选持续时间。 |
| `flatline_tolerance` | `0.0` | 非负有限数值容差。 |
| `max_issues` | `10000` | 保存明细的正上限。 |

## 返回值

返回 QualityReport 字典：time、channels、issues、total_issues、issues_truncated、dynamic_checks_completed、flagged_sample_count。参见[类型](../types.md)。

## 错误

shape/配置错误、负 gap、无效阈值、Hampel 窗口超限时 ValueError；core 时间运算溢出时 OverflowError。

## 语义与边界

保留原始顺序，时钟回退和重复仍可检测；dynamic_checks_completed 表明有序时间的动态检查是否完成。阈值向量必须包含 D 个有限值，不会广播标量。明细可以截断，但总数和 flagged_sample_count 保持完整。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
r = ops.inspect_signal(t, x, {"upper": [1.5]})
assert r["total_issues"] == 1
assert r["issues"][0]["code"] == "above_range"
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
