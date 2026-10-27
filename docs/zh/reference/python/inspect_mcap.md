# mcap_ops.inspect_mcap

**语言：中文 | [English](../../../reference/python/inspect_mcap.md)**

按原始文件顺序扫描完整 MCAP 容器。

```python
mcap_ops.inspect_mcap(path, *, filter=None, limits=None, max_gap_ns=0)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `path` | `str` | `required` | 本地普通 MCAP 文件路径。 |
| `filter` | `dict or None` | `None` | MessageFilter：精确 topic 匹配与半开时间区间。 |
| `limits` | `dict or None` | `None` | ReadLimits：record 字节数与扫描消息数上限。 |
| `max_gap_ns` | `int` | `0` | 两种时钟统计的正间隔 gap 阈值，单位 ns。 |

### 配置默认值

| 字段 | 默认值 | 含义 |
| --- | --- | --- |
| `filter.topics` | `[]` | 精确匹配，空列表选择全部。 |
| `filter.start_ns / end_ns` | `None` | 可选 uint64 区间端点 [start,end)。 |
| `filter.publish_clock` | `False` | 按 publish_time 而非 log_time 筛选。 |
| `limits.max_record_bytes` | `67108864` | 每 record 的正上限，包含 chunk。 |
| `limits.max_messages` | `10000000` | 扫描消息数正上限。 |

## 返回值

McapReport 字典：format、operator_version、source、file_bytes、scanned_messages、selected_messages、complete、crc_validation、filter、channels。每个 ChannelReport 含通道/schema 标识、payload_bytes、log_time 与 publish_time 的 TimeStats。

## 错误

IO/MCAP 错误、过滤/上限非法、已有 CRC 校验失败、超限、检测到源变化时 ValueError。完整性要求读到 EOF。

## 语义与边界

max_gap_ns=0 会把每个正间隔计为 gap，应显式设置合理阈值。读取上限针对扫描而不仅是选中消息；一个 chunk 也可能超过 max_record_bytes。CRC 可能不存在，不会把缺失 CRC 写成已校验。只报告 payload schema，不解码。

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
    r = ops.inspect_mcap(str(path), max_gap_ns=15_000_000)
    assert r["complete"] and r["selected_messages"] == 3
    assert r["channels"][0]["topic"] == "/sensor"
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
