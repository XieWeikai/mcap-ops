# Rust 接口索引

**语言：中文 | [English](../../reference/rust.md)**

以下链接进入与本站同一源码版本构建的 rustdoc，可查询完整签名、字段、方法、trait 实现和源码。这个双语索引解释用途；编译器生成的 Rust 语法及源注释共用一份英文参考。

[mcap-ops-core](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/index.html) · [mcap-ops-io](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/index.html)

## 如何查询

点击类型名后查看 **Fields / Implementations / Trait Implementations**；`Signal` 的构造与所有权方法、`IntervalSet` 的交差集和窗口扩展、`RawReader` 的 Iterator 实现都在那里。rustdoc 搜索支持按符号名和类型查询，可直接打开字段/方法锚点。

## mcap_ops_core

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [Error](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/enum.Error.html) | enum | 有类型的验证与处理错误 |
| [Result](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/type.Result.html) | type | crate 专属结果别名 |
| [Signal](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/struct.Signal.html) | struct | 自有行优先数值信号 |
| [SignalSpec](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/struct.SignalSpec.html) | struct | 描述单位、坐标系、时钟和种类 |
| [SignalKind](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/enum.SignalKind.html) | enum | 连续、四元数、命令、离散、事件 |

## mcap_ops_core::filter

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [FilterMode](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/enum.FilterMode.html) | enum | 因果或居中支持 |
| [Filtered](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/struct.Filtered.html) | struct | 信号、掩码、前视与群延迟 |
| [ema](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/fn.ema.html) | fn | 感知时间的因果平滑 |
| [lowpass_taps](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/fn.lowpass_taps.html) | fn | 归一化加窗 sinc 系数 |
| [fir](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/fn.fir.html) | fn | 规则网格的有限冲激响应滤波 |
| [unwrap_angles](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/fn.unwrap_angles.html) | fn | 带 gap 重置的周期值展开 |

## mcap_ops_core::quality

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [IssueCode](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/enum.IssueCode.html) | enum | 稳定的质量问题分类 |
| [QualityConfig](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.QualityConfig.html) | struct | 检测阈值与资源上限 |
| [Issue](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.Issue.html) | struct | 源区间、测量值与阈值 |
| [ChannelStats](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.ChannelStats.html) | struct | 有限值统计与溢出标记 |
| [QualityReport](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.QualityReport.html) | struct | 有上限的明细与完整计数 |
| [inspect_signal](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/fn.inspect_signal.html) | fn | 时间、范围、变化率、尖峰与平线检测 |
| [GatePolicy](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.GatePolicy.html) | struct | 显式拒绝策略 |
| [GateDecision](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.GateDecision.html) | struct | 通过结果与拒绝原因 |
| [gate](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/fn.gate.html) | fn | 基于完整证据评估策略 |

## mcap_ops_core::sampling

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [Method](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/enum.Method.html) | enum | Previous、Nearest、Linear、Slerp |
| [SampleOptions](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/struct.SampleOptions.html) | struct | 方法、gap、age、未来许可 |
| [Status](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/enum.Status.html) | enum | 稳定的 0-6 样本状态码 |
| [Sampled](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/struct.Sampled.html) | struct | 数值、来源支持与状态 |
| [resample](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/fn.resample.html) | fn | 采样到有序目标时间轴 |
| [Windowed](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/struct.Windowed.html) | struct | 中心、偏移与扁平 Sampled 缓冲区 |
| [history_windows](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/fn.history_windows.html) | fn | 按每个中心的显式历史偏移采样 |

## mcap_ops_core::selection

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [Interval](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/selection/struct.Interval.html) | struct | 半开纳秒区间 |
| [IntervalSet](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/selection/struct.IntervalSet.html) | struct | 规范区间运算与上下文扩展 |

## mcap_ops_core::time

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [require_strict](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.require_strict.html) | fn | 拒绝重复和时钟回退 |
| [uniform_grid](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.uniform_grid.html) | fn | [start,end) 的有理频率舍入网格 |
| [map_clock](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.map_clock.html) | fn | 围绕原点显式应用偏移和 ppb 缩放 |
| [TimeStats](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/struct.TimeStats.html) | struct | 时钟质量与正间隔统计 |
| [inspect_time](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.inspect_time.html) | fn | 原始顺序时间统计 |
| [TimeAlignment](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/struct.TimeAlignment.html) | struct | 索引、有符号偏移、有效性 |
| [align_timestamps](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.align_timestamps.html) | fn | 有界过去/最近索引匹配 |
| [expand_batch_timestamps](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.expand_batch_timestamps.html) | fn | 按显式样本偏移展开消息时间 |

## mcap_ops_io

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [Error](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/enum.Error.html) | enum | 有类型的验证与处理错误 |
| [Result](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/type.Result.html) | type | crate 专属结果别名 |

## mcap_ops_io::image_ops

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [ImageOptions](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/struct.ImageOptions.html) | struct | 图像上限与曝光阈值 |
| [decode](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/fn.decode.html) | fn | 有界 PNG/JPEG 解码器 |
| [ImageQuality](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/struct.ImageQuality.html) | struct | 图像指标与解码 RGB hash |
| [image_quality](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/fn.image_quality.html) | fn | 计算曝光与清晰度指标 |
| [ResizeFilter](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/enum.ResizeFilter.html) | enum | Nearest、Triangle、Lanczos3 |
| [transform_image](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/fn.transform_image.html) | fn | 先裁剪再缩放，返回编码 PNG |

## mcap_ops_io::mcap_ops

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [MessageFilter](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.MessageFilter.html) | struct | topic 与 MCAP 时钟选择 |
| [ReadLimits](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.ReadLimits.html) | struct | record 大小与扫描消息上限 |
| [RawReader](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.RawReader.html) | struct | 可失败的原始顺序 MCAP 迭代器 |
| [ChannelReport](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.ChannelReport.html) | struct | 通道/schema 标识与双时钟 |
| [McapReport](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.McapReport.html) | struct | 完整容器扫描报告 |
| [inspect_mcap](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/fn.inspect_mcap.html) | fn | 验证并汇总容器 |
| [DecodedSample](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.DecodedSample.html) | struct | 解码器输出：timestamp_ns 与 values |
| [SignalDecoder](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/trait.SignalDecoder.html) | trait | schema 专属 payload 到信号 trait |
| [JsonSignalSpec](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.JsonSignalSpec.html) | struct | 显式 RFC 6901 字段解码器 |
| [read_signal](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/fn.read_signal.html) | fn | 有界收集解码结果为 Signal |

## mcap_ops_io::video

| 符号 | 类型 | 用途 |
| --- | --- | --- |
| [probe_video](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/video/fn.probe_video.html) | fn | 有超时限制的视频流元数据读取 |
| [VideoValidation](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/video/struct.VideoValidation.html) | struct | 完整解码完成报告 |
| [validate_video](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/video/fn.validate_video.html) | fn | 探测并完整解码第一个视频流 |

## Rust 独有接口

`gate`、`IntervalSet`、`map_clock`、`inspect_time`、`expand_batch_timestamps`、`RawReader`、`SignalDecoder`、独立 `probe_video` 没有 Python 导出。`map_clock` 使用调用方提供的参数，不拟合时钟。

| 接口 | 输入与输出 | 行为和错误 |
| --- | --- | --- |
| `require_strict` | `&[i64] -> Result<()>` | 空/单样本通过；重复或回退返回 Invalid |
| `inspect_time` | times、非负 max_gap_ns -> `TimeStats` | 检查原始顺序，只汇总正间隔，使用插值 median/p95；estimated_hz 为 1e9/median；不可用统计为 None |
| `map_clock` | times、origin、offset（ns）、rate_ppb -> `Vec<i64>` | 计算 `origin + round((t-origin)*(1+rate_ppb/1e9)) + offset`；缩放必须为正；半数远离零舍入；检查 int64 溢出 |
| `expand_batch_timestamps` | message_times、counts、扁平 offsets（ns）-> `Vec<i64>` | 每条消息对应一个 count；sum(counts) 等于 offsets.len()；每个偏移加对应消息时间并检查溢出 |
| `gate` | `&QualityReport`、`&GatePolicy` -> `GateDecision` | 样本太少、标记比例超限或包含拒绝代码时拒绝；明细截断不影响内部完整标记；空输入比例为 0 |
| `IntervalSet` | 规范半开区间 -> 集合 / 掩码 | 见[方法契约](types.md#interval-intervalset)；无效区间或上下文扩展溢出时失败 |
| `RawReader::open` | path、filter、limits -> 可失败的消息迭代器 | 保留文件顺序与 CRC/错误处理；提前结束不能证明 EOF 或完整源已验证 |
| `read_signal` | path、filter、limits、`&dyn SignalDecoder`、max_samples -> `Signal` | 在正上限内收集样本并验证通道数，保留顺序；损坏的相关消息或没有解码样本时失败 |
| `decode` | PNG/JPEG 字节、`&ImageOptions` -> `image::DynamicImage` | 返回解码图像前检查格式、尺寸、像素和分配限制 |
| `probe_video` | 本地路径、ffprobe 可执行文件、`Duration` -> `serde_json::Value` | 在有界超时内要求工具成功且存在视频流；不解码帧，也不证明画面质量 |

`map_clock` 返回新时间，不覆盖源时钟、不排序、不去重，
也不保证舍入后仍严格递增。应保存映射参数并保留原始时间。
批次展开同样不会猜测采样频率或保证全局有序。

完整的带断言质量 gate、区间筛选和重采样例子见
[quality_pipeline.rs](../../../crates/core/examples/quality_pipeline.rs)。
实现 `SignalDecoder` 的方式见 [Rust 扩展指南](../rust.md)。

[类型与契约](types.md) · [Rust 使用与扩展](../rust.md) · [Python API](index.md)
