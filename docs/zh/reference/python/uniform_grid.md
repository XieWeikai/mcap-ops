# mcap_ops.uniform_grid

**语言：中文 | [English](../../../reference/python/uniform_grid.md)**

生成有理数频率的纳秒时间网格。

```python
mcap_ops.uniform_grid(start_ns, end_ns, rate_num, rate_den, max_points)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `start_ns / end_ns` | `int64` | `required` | 半开区间 [start_ns,end_ns)，起点不大于终点。 |
| `rate_num / rate_den` | `uint32` | `required` | 正整数分子/分母，频率单位 Hz。 |
| `max_points` | `int` | `required` | 输出长度的正整数上限。 |

## 返回值

list[int]，不是 NumPy 数组。起终点相同返回空列表。使用 np.asarray(..., dtype=np.int64) 转换。

## 错误

区间倒置、频率/上限为零、周期小于纳秒、超过 max_points 时 ValueError；整数转换/运算溢出时 OverflowError。

## 语义与边界

使用整数运算，不把 epoch 转成浮点数。按有理数周期舍入，支持 30000/1001 Hz，避免逐步累积周期舍入误差。不包含终点。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

```python
import mcap_ops as ops
grid = ops.uniform_grid(0, 21_000_000, 100, 1, 10)
assert grid == [0, 10_000_000, 20_000_000]
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
