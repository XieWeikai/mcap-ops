# mcap_ops.inspect_mcap

**Language: English | [Chinese](../../zh/reference/python/inspect_mcap.md)**

Scan a complete MCAP container in original file order.

```python
mcap_ops.inspect_mcap(path, *, filter=None, limits=None, max_gap_ns=0)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `path` | `str` | `required` | Path to a regular local MCAP file. |
| `filter` | `dict or None` | `None` | MessageFilter: exact topics and a half-open time interval. |
| `limits` | `dict or None` | `None` | ReadLimits: record-byte and scanned-message caps. |
| `max_gap_ns` | `int` | `0` | Positive-interval gap threshold for both clock summaries, ns. |

### Configuration defaults

| Field | Default | Meaning |
| --- | --- | --- |
| `filter.topics` | `[]` | Exact matches; empty selects all. |
| `filter.start_ns / end_ns` | `None` | Optional uint64 bounds [start,end). |
| `filter.publish_clock` | `False` | Select by publish_time rather than log_time. |
| `limits.max_record_bytes` | `67108864` | Positive per-record cap; chunks included. |
| `limits.max_messages` | `10000000` | Positive scanned-message cap. |

## Returns

McapReport dictionary: format, operator_version, source, file_bytes, scanned_messages, selected_messages, complete, crc_validation, filter, channels. Each ChannelReport contains channel/schema identity, payload_bytes, log_time and publish_time TimeStats.

## Errors

ValueError for IO/MCAP errors, invalid filters or limits, failed available CRCs, limits exceeded, or detected source changes. Completion requires EOF.

## Semantics and boundaries

max_gap_ns=0 counts every positive interval as a gap; set a meaningful threshold. Read limits apply to the scan, not only selected messages. A chunk can exceed max_record_bytes. CRCs may be absent; the report does not pretend absent CRCs were verified. Payload schemas are reported, not decoded.

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
    r = ops.inspect_mcap(str(path), max_gap_ns=15_000_000)
    assert r["complete"] and r["selected_messages"] == 3
    assert r["channels"][0]["topic"] == "/sensor"
```

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
