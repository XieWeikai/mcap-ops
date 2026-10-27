# mcap_ops.read_json_signal

**Language: English | [Chinese](../../zh/reference/python/read_json_signal.md)**

Decode explicitly selected JSON fields into a numeric signal.

```python
mcap_ops.read_json_signal(path, topic, fields, channels, *, filter=None, limits=None, timestamp_pointer=None, publish_clock=False, max_samples=10_000_000)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `path / topic` | `str` | `required` | Regular local MCAP file and exact topic. |
| `fields` | `list[str]` | `required` | RFC 6901 pointers to numbers or flat numeric arrays. |
| `channels` | `int` | `required` | Positive flattened channel count across all fields. |
| `filter` | `dict or None` | `None` | MessageFilter: exact topics and a half-open time interval. |
| `limits` | `dict or None` | `None` | ReadLimits: record-byte and scanned-message caps. |
| `timestamp_pointer` | `str or None` | `None` | Payload pointer to int64 nanoseconds; overrides output clock choice. |
| `publish_clock` | `bool` | `False` | Use publish_time instead of log_time if no timestamp_pointer. |
| `max_samples` | `int` | `10_000_000` | Positive decoded-sample cap. |

### Configuration defaults

| Field | Default | Meaning |
| --- | --- | --- |
| `filter.topics` | `[]` | Exact matches; empty selects all. |
| `filter.start_ns / end_ns` | `None` | Optional uint64 bounds [start,end). |
| `filter.publish_clock` | `False` | Select by publish_time rather than log_time. |
| `limits.max_record_bytes` | `67108864` | Positive per-record cap; chunks included. |
| `limits.max_messages` | `10000000` | Positive scanned-message cap. |

## Returns

Signal dictionary: timestamps int64[N], values float64[N,D], channels int. Field order determines flattened channel order; file order is preserved.

## Errors

ValueError for malformed selected JSON, missing/non-numeric fields, channel mismatch, invalid timestamp, limits, IO, or MCAP errors. No matching decoded samples also raises ValueError. Unrelated topics are skipped; malformed selected messages are not silently skipped.

## Semantics and boundaries

filter.publish_clock chooses the clock for selection independently of publish_clock/timestamp_pointer for output. Output times must fit signed int64. No CDR/Protobuf decoding, sorting, deduplication, or clock estimation is performed.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

Requires the Python `mcap` package to generate the fixture.

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

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
