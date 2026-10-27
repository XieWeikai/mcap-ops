# Rust 接口与扩展

**语言：中文 | [English](../rust.md)**

[文档导航](README.md) · [安装与 path 依赖](getting-started.md) · [数据契约](concepts.md)

## 直接调用 core

完整、带断言的示例在 [quality_pipeline.rs](../../crates/core/examples/quality_pipeline.rs)。
在配置的 Linux 执行环境的仓库根目录运行：

```bash
cargo run --locked --release -p mcap-ops-core --example quality_pipeline
```

```rust
use mcap_ops_core::{Signal, sampling::{resample, Method, SampleOptions}};

fn main() -> mcap_ops_core::Result<()> {
    let input = Signal::new(vec![0, 10], vec![0.0, 1.0], 1)?;
    let output = resample(&input, &[5], SampleOptions {
        method: Method::Linear,
        max_gap_ns: 10,
        max_age_ns: 10,
        allow_future: true,
    })?;
    assert_eq!(output.values, vec![0.5]);
    assert_eq!(output.source_left, vec![0]);
    Ok(())
}
```

示例中时间单位仍是 ns，只是使用了很小的整数。实际数据不要混用 ms/秒。

## core 模块索引

| 模块 | 公共类型与函数 |
| --- | --- |
| crate root | `Signal`, `SignalSpec`, `SignalKind`, `Error`, `Result<T>` |
| `time` | `require_strict`, `uniform_grid`, `map_clock`, `inspect_time`, `align_timestamps`, `expand_batch_timestamps`, `TimeStats`, `TimeAlignment` |
| `quality` | `QualityConfig`, `QualityReport`, `Issue`, `IssueCode`, `ChannelStats`, `inspect_signal`, `GatePolicy`, `GateDecision`, `gate` |
| `sampling` | `Method`, `SampleOptions`, `Status`, `Sampled`, `Windowed`, `resample`, `history_windows` |
| `selection` | `Interval`, `IntervalSet` |
| `filter` | `FilterMode`, `Filtered`, `ema`, `lowpass_taps`, `fir`, `unwrap_angles` |

Signal 的 getter 返回借用，`into_parts()` 消费 Signal 并转移三个拥有所有权的字段：
`(Vec<i64>, Vec<f64>, usize)`。Rust Sampled/Windowed 中的数值和掩码是平坦 Vec，
调用者按 channels、centers、offsets 解释形状。

## 显式门控与区间筛选

```rust
use mcap_ops_core::quality::{gate, GatePolicy, IssueCode};
use mcap_ops_core::selection::{Interval, IntervalSet};

// report 来自 inspect_signal；所有策略由调用者明确指定。
let decision = gate(&report, &GatePolicy {
    reject_codes: vec![IssueCode::NonFinite, IssueCode::ClockReversal],
    max_flagged_fraction: 0.01,
    min_samples: 100,
})?;

let keep = IntervalSet::new(vec![Interval { start_ns: 0, end_ns: 1_000_000_000 }])?;
let bad = IntervalSet::new(vec![Interval { start_ns: 200_000_000, end_ns: 300_000_000 }])?;
let clean = keep.difference(&bad);
let selected = clean.mask(&target_times);
```

这是用法片段，report/target_times 由调用者提供。`IntervalSet::new` 会合并重叠/相邻
区间；`intersection`、`difference` 返回新集合；`mask` 对无序时间也有效。
`affected_centers(history_ns,future_ns)` 扩展坏区间，适合剔除上下文触碰坏点的训练中心。
不要直接把 Issue.last_ns 当作半开区间终点，转换时明确离散样本覆盖政策与溢出处理。

## io：读取与 Decoder

```rust
use mcap_ops_io::mcap_ops::{RawReader, MessageFilter, ReadLimits};

for message in RawReader::open("example.mcap", MessageFilter::default(), ReadLimits::default())? {
    let message = message?;
    println!("{} {}", message.channel.topic, message.log_time);
}
```

RawReader 保持文件顺序。若提前 break，不能宣称全文件完成校验；CRC/EOF 和源文件身份
检查必须完成对应读取阶段。上游不得在读取期间修改/截断该文件。

Decoder trait 的准确边界：

```rust
pub trait SignalDecoder {
    fn channels(&self) -> usize;
    fn decode(&self, message: &mcap::Message<'_>)
        -> mcap_ops_io::Result<Vec<mcap_ops_io::mcap_ops::DecodedSample>>;
}
```

一个适配器负责：匹配 topic/schema，按协议解析字段，明确时间来源/单位，展开批量样本，
返回正确通道数。无关消息返回空 Vec，坏消息返回错误，不悄悄跳过。
直接引用 mcap 类型的自定义适配器应声明兼容的 `mcap = "0.26"` 依赖。
调用 `read_signal(path, filter, limits, &decoder, max_samples)` 得到 Signal。

内置 `JsonSignalSpec { topic, fields, channels, timestamp_pointer, publish_clock }`
实现此 trait；没有默认 CDR/Protobuf 解码器。使用者只要已拿到数组，也可绕过 io。

## 编译文档与错误

在配置的 Linux 执行环境 运行：

```bash
cargo doc --locked --workspace --no-deps
```

API 文档生成于 `target/doc/`。core 使用 `Error::Invalid(String)` 和 `Error::Overflow`；
io 保留 IO/MCAP/core/JSON/image 错误并补充 Invalid。使用 `?` 传播错误；benchmark
必须测量成功结果，不能把提早返回 Err 当成更快。

扩展算子时同步公共接口、测试、fixture、Python wrapper（若计划导出）与文档，
具体检查见[贡献指南](contributing.md)。
