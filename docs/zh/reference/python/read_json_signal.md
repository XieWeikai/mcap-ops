# mcap_ops.read_json_signal

**语言：中文 | [English](../../../reference/python/read_json_signal.md)**

将显式选择的 JSON 字段解码为数值信号。

```python
mcap_ops.read_json_signal(path, topic, fields, channels, *, filter=None, limits=None, timestamp_pointer=None, publish_clock=False, max_samples=10_000_000)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `path / topic` | `str` | `required` | 本地普通 MCAP 文件与精确 topic。 |
| `fields` | `list[str]` | `required` | 指向数值或一维数值数组的 RFC 6901 指针。 |
| `channels` | `int` | `required` | 全部字段展开后的正通道数。 |
| `filter` | `dict or None` | `None` | MessageFilter：精确 topic 匹配与半开时间区间。 |
| `limits` | `dict or None` | `None` | ReadLimits：record 字节数与扫描消息数上限。 |
| `timestamp_pointer` | `str or None` | `None` | 指向 int64 纳秒的 payload 字段，优先于输出时钟选择。 |
| `publish_clock` | `bool` | `False` | 无 timestamp_pointer 时，是否使用 publish_time 而非 log_time。 |
| `max_samples` | `int` | `10_000_000` | 解码样本数的正上限。 |

### 配置默认值

| 字段 | 默认值 | 含义 |
| --- | --- | --- |
| `filter.topics` | `[]` | 精确匹配，空列表选择全部。 |
| `filter.start_ns / end_ns` | `None` | 可选 uint64 区间端点 [start,end)。 |
| `filter.publish_clock` | `False` | 按 publish_time 而非 log_time 筛选。 |
| `limits.max_record_bytes` | `67108864` | 每 record 的正上限，包含 chunk。 |
| `limits.max_messages` | `10000000` | 扫描消息数正上限。 |

## 返回值

Signal 字典：timestamps int64[N]、values float64[N,D]、channels int。字段顺序决定展开通道顺序，保留文件顺序。

## 错误

选中 JSON 损坏、字段缺失/非数值、通道不匹配、时间戳非法、超限、IO/MCAP 错误时 ValueError。没有匹配的解码样本时也抛出 ValueError。忽略无关 topic，但不静默跳过损坏的选中消息。

## 语义与边界

filter.publish_clock 单独决定筛选时钟，与输出的 publish_clock/timestamp_pointer 相互独立。输出时间需可用有符号 int64 表示。不做 CDR/Protobuf 解码、排序、去重或时钟估计。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

需要 Python `mcap` 包，仅用于生成测试文件。

```python
import json
import tempfile
from pathlib import Path
from mcap.writer import Writer
import mcap_ops as ops

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "example.mcap"
    with path.open("wb") as stream:
        writer = Writer(stream)
        writer.start()
        channel = writer.register_channel("/sensor", "json", 0)
        for i in range(3):
            writer.add_message(channel, i*10_000_000, json.dumps({"value": float(i)}).encode(), i*10_000_000)
        writer.finish()
    r = ops.read_json_signal(str(path), "/sensor", ["/value"], 1)
    assert r["values"].tolist() == [[0.0], [1.0], [2.0]]
    assert r["timestamps"].tolist() == [0, 10_000_000, 20_000_000]
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
