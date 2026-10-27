# 算子清单 · 0.1.0

**语言：中文 | [English](../operators.md)**

[文档导航](README.md) · [Python 签名](python.md) · [Rust 接口](rust.md)

所有输入源只读；变换返回新结果，不原地修改 MCAP 或调用方数组。
“Python”列为 `mcap_ops` 公共接口实际可用性，不能把 Rust 能力自动视为 Python 导出。

## 1. 时间与对齐

| Rust 接口 | 输入 → 输出 | Python |
| --- | --- | --- |
| `require_strict` | 时间戳 → 严格递增校验或错误 | 不独立导出；变换内部校验 |
| `uniform_grid` | 起止 ns、有理频率、点数上限 → 半开目标时间轴 | 同名；返回 list |
| `inspect_time` | 原始顺序时间戳、gap 阈值 → 倒退/重复/缺口、间隔统计 | 不独立导出；见 inspect_signal 的 time |
| `align_timestamps` | 有序源/目标、前后容差 → 索引、偏移、valid | 同名 |
| `map_clock` | 时间、origin、offset、rate_ppb → 显式修正后的时间 | Rust-only |
| `expand_batch_timestamps` | 消息时间、每消息数量、样本 offsets → 样本时间 | Rust-only |

## 2. 质检

| Rust 接口 | 输入 → 输出 | Python |
| --- | --- | --- |
| `inspect_signal` | Signal、QualityConfig → 统计与 Issue 证据 | 同名；输入为 NumPy |

检测覆盖 non-finite、范围、时钟倒退/重复/缺口、变化速率、加速度、局部 Hampel 尖峰和平线
候选。保留总异常数与明细截断状态；乱序时标明动态检查未完整执行，不自动修复。
Hampel 的 window 参数为中心两侧各扩展的时间半径，可使用未来样本，属于离线质检。

## 3. 策略与区间

| Rust 接口 | 输入 → 输出 | Python |
| --- | --- | --- |
| `gate` | QualityReport、GatePolicy → passed、reasons、flagged_fraction | Rust-only |
| `IntervalSet::new` | 半开区间 → 排序合并后的集合 | Rust-only |
| `contains` / `mask` | 时间点/数组 → 成员判断/布尔掩码 | Rust-only |
| `intersection` / `difference` | 两个区间集合 → 交集/差集 | Rust-only |
| `affected_centers` | 坏区间、历史/未来上下文长度 → 受影响的中心区间 | Rust-only |

## 4. 重采样与滤波

| Rust 接口 | 输入 → 输出 | Python |
| --- | --- | --- |
| `resample` | Signal、target、SampleOptions → Sampled | 同名 |
| `history_windows` | Signal、centers、非正 offsets → Windowed | 同名；values 三维，mask 仍平坦 |
| `ema` | 有序 Signal、tau 秒、gap → Filtered | 同名 |
| `lowpass_taps` | 采样率/截止频率 Hz、奇数 taps → 归一化低通系数 | 同名；返回 list |
| `fir` | 规则信号、系数、模式、周期/容差 → Filtered | 同名；valid 为 list |
| `unwrap_angles` | 周期数值信号、period、gap → 展开后的 Signal | 同名 |

resample 支持 previous、nearest、linear、SLERP。previous 因果且有最大年龄；nearest
只有显式允许才取未来；linear/SLERP 要有效双侧支撑和 gap 限制。降采样不自动低通。
SLERP 为 xyzw、最短路径，输入模长距 1 不超过 0.01。滤波不跨缺失支撑。

## 5. MCAP 与解码

| Rust 接口 | 输入 → 输出 | Python |
| --- | --- | --- |
| `RawReader` | 文件、MessageFilter、ReadLimits → 原顺序原始消息迭代器 | Rust-only |
| `inspect_mcap` | 文件、过滤、限额、gap → channel/schema/时钟/完整性报告 | 同名 |
| `JsonSignalSpec::decode` | JSON 消息、字段指针、通道与时钟规则 → 解码样本 | 经 read_json_signal |
| `read_signal` / `SignalDecoder` | 文件与明确 Decoder → Signal | 内置 JSON 路径为 read_json_signal |

未知 CDR/Protobuf 需要上游适配；容器可检查不代表载荷已支持。只校验文件中存在的 CRC；
提前结束 RawReader 不等于完整文件验证。源身份在 EOF 检查，调用者应保证读取中源不变。

## 6. 图片与视频

| Rust 接口 | 输入 → 输出 | Python |
| --- | --- | --- |
| `image_ops::decode` | 有界 PNG/JPEG bytes → DynamicImage | 不独立导出 |
| `image_quality` | 图片 bytes、限额 → 尺寸/亮度/曝光比例/Laplacian/RGB 哈希 | 同名 |
| `transform_image` | 图片、裁剪/缩放/filter → 新 PNG bytes | 同名；返回 list[int] |
| `probe_video` | 本地视频、ffprobe、timeout → metadata | Rust-only；validate_video 内部使用 |
| `validate_video` | 视频、工具路径、timeout → 完整首视频流解码报告 | 同名 |

图像指标不是学习型判断；视频解码成功不保证视觉内容有效。FFmpeg 用参数数组调用，
有超时和诊断限额；工具不可用不能算质量通过。

## 清单与优化计数

公开函数、类型方法、内部处理单元是不同统计口径。Python 有 14 个处理函数；RSI 覆盖
30 个实现单元，其中包括 IntervalSet 各操作、内部解码与 Python bridge。具体覆盖见
[RSI 历史索引](../../RSI/zh/evidence.md)，不把十次候选当成十个新增算子。
