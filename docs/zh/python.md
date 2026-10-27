# Python API · 0.1.0

**语言：中文 | [English](../python.md)**

[文档导航](README.md) · [安装](getting-started.md) · [完整示例](../../examples/quickstart.py)

公共入口为 `import mcap_ops as ops`。以下对应 [Python wrapper](../../python/mcap_ops/__init__.py)
和 [PyO3 绑定](../../crates/python/src/lib.rs) 的现有实现；不要直接依赖 `_native` 私有接口。

## 通用输入和返回类型

- 时间、target、centers、offsets：连续一维 `np.int64`，单位 ns。
- values：一维或二维 `np.float64`，二维为 `(samples, channels)`；跨步/反向视图可用。
- 不原地改写输入；创建 Rust 自有快照，输出不与输入共享缓冲。
- Signal 型结果包含 `timestamps: ndarray[int64]`、`values: ndarray[float64]`、`channels: int`。
- 诊断报告为普通字典；个别接口直接返回 list，详见各节。
- 当前持有 GIL；上游可用进程并发 episode，不能据此声称多线程加速。

## 1. inspect_signal

```python
ops.inspect_signal(timestamps, values, config=None) -> dict
```

| config 字段 | 默认值 | 单位 / 含义 |
| --- | --- | --- |
| `max_gap_ns` | int64 最大值 | 正时间间隔的缺口阈值 |
| `lower`, `upper` | None | 长度 D 的有限阈值列表；数值单位 |
| `max_rate` | None | 长度 D，非负；数值单位/秒 |
| `max_acceleration` | None | 长度 D，非负；数值单位/秒² |
| `hampel_window_ns` | None | 中心两侧各扩展的时间半径，正数；可能使用未来样本 |
| `hampel_sigma` | 3.0 | MAD 比例阈值 |
| `hampel_min_deviation` | 0.0 | 最小绝对偏差，数值单位 |
| `max_hampel_samples` | 4096 | 每个窗口的样本上限；至少 3 |
| `flatline_duration_ns` | None | 平线候选持续时间阈值 |
| `flatline_tolerance` | 0.0 | 平线数值容差 |
| `max_issues` | 10000 | 保留的 Issue 明细上限；总数单独记录 |

返回 time、channels 统计、issues、total_issues、issues_truncated、flagged_sample_count、
dynamic_checks_completed。Issue code 为 `non_finite`、`below_range`、`above_range`、
`clock_reversal`、`duplicate_time`、`gap`、`rate`、`acceleration`、`spike`、`flatline`。
阈值必须对应通道数；不会将标量广播成 D 个阈值。没有自动删除或修复。

## 2. uniform_grid

```python
ops.uniform_grid(start_ns, end_ns, rate_num, rate_den, max_points) -> list[int]
```

在 `[start,end)` 建立有理频率 `rate_num/rate_den` Hz 的整数纳秒网格；例如 30000/1001 Hz。
返回 Python list，传给数值算子前用 `np.asarray(..., dtype=np.int64)`。
参数必须有效，数量超过 max_points 或频率超过纳秒分辨率时报错。

## 3. align_timestamps

```python
ops.align_timestamps(source, target, *, nearest=False,
                     max_past_ns=0, max_future_ns=0) -> dict
```

只匹配时间，不插值数值。源严格递增、目标非递减。返回 `indices: int64[M]`、
`offsets_ns: int64[M]`、`valid: bool[M]`；偏移为 source-minus-target。
默认只找过去；nearest=True 才考虑未来，并分别限制两侧容差。平局选过去。
无效 indices=-1，offsets_ns=0 不代表真的零偏移，必须检查 valid。

## 4. resample

```python
ops.resample(timestamps, values, target, *, method="previous",
             max_gap_ns=0, max_age_ns=0, allow_future=False) -> dict
```

方法为 previous、nearest、linear、slerp；具体时间语义见[契约](concepts.md)。

| 返回字段 | dtype / shape |
| --- | --- |
| timestamps | int64 `(M,)` |
| values | float64 `(M,D)` |
| channels | Python int |
| status | uint8 `(M,)`；0 为有效，1–6 见契约 |
| valid | bool `(M,)`，等于 status==0 |
| source_left, source_right | int64 `(M,)`，无效为 -1 |
| alpha | float64 `(M,)` |
| uses_future | bool `(M,)` |

源严格递增、target 非递减。linear/SLERP 使用 max_gap；previous/nearest 用 max_age。
精确匹配不需要未来；超出支撑不自动插零。SLERP 输入 D=4、顺序 xyzw，模长检查容差 0.01。

## 5. history_windows

```python
ops.history_windows(timestamps, values, centers, offsets, *, method="previous",
                    max_gap_ns=0, max_age_ns=0, allow_future=False) -> dict
```

请求 `centers[i] + offsets[j]`；centers 严格递增，offsets 非空、严格递增、非正。
返回 resample 字段以及 centers、offsets。
values 为 `(T,W,D)`，timestamps 为 `(T,W)`；**valid/status/source/alpha/uses_future 仍为
`(T*W,)`**。例如 `result["valid"].reshape(T, W)`。

## 6–9. 滤波与角度

```python
ops.ema(timestamps, values, tau_seconds, max_gap_ns) -> dict
ops.lowpass_taps(sample_rate_hz, cutoff_hz, taps) -> list[float]
ops.fir(timestamps, values, taps, *, mode="causal",
        period_ns=1, tolerance_ns=0) -> dict
ops.unwrap_angles(timestamps, values, *, period=2*np.pi, max_gap_ns=0) -> dict
```

EMA/FIR 返回 Signal 字段及 `valid: list[bool]`、mode、lookahead_samples、
group_delay_samples（float 或 None）。unwrap 只返回 Signal 字段，不提供 valid。

lowpass_taps 的 tap 数为 [3,4095] 的奇数，`0 < cutoff < sample_rate/2`。
FIR taps 要转换为连续一维 `np.float64`，长度 1–4095；centered 模式还要求奇数。
`period_ns>0` 且 `0<=tolerance_ns<period_ns`。支撑不完整时输出 NaN，不做边缘 padding。

```python
coefficients = np.asarray(ops.lowpass_taps(200.0, 20.0, 31), dtype=np.float64)
# t200/x200 是调用方已有的规则 200 Hz 信号。
filtered = ops.fir(t200, x200, coefficients, period_ns=5_000_000)
valid = np.asarray(filtered["valid"], dtype=bool)
# 对称 31 taps 的因果 FIR：群延迟 15 点；前 30 点支撑不足。
```

## 10–11. MCAP

```python
ops.inspect_mcap(path, *, filter=None, limits=None, max_gap_ns=0) -> dict
ops.read_json_signal(path, topic, fields, channels, *, filter=None, limits=None,
                     timestamp_pointer=None, publish_clock=False,
                     max_samples=10_000_000) -> dict
```

path 使用字符串。JSON `fields` 为 RFC 6901 指针列表，字段必须是数值或一维数值数组；
按 fields 顺序展平，长度必须等于 channels。默认以 log_time 作为输出时间。
`timestamp_pointer` 若指定，必须指向 int64 纳秒；否则 publish_clock 控制输出时钟。

| 配置 | 字段与默认值 |
| --- | --- |
| filter | `topics=[]`（全部）、`start_ns=None`、`end_ns=None`、`publish_clock=False` |
| limits | `max_record_bytes=67108864`、`max_messages=10000000` |

过滤时间窗口采用 filter.publish_clock 指定的 MCAP 时钟，**独立于**解码时间选择。
选择 payload 时间戳不会自动改变过滤时钟。limits 作用于读取扫描，不是只数选中的消息。
大 chunk 可能超过记录限额；限额不是 RSS 上界。

inspect_mcap 返回 source、file_bytes、scanned_messages、selected_messages、complete、
crc_validation、filter、channels 等。channels 包含 topic、schema 元信息/哈希和两个时钟统计。
默认 max_gap_ns=0 会将每个正间隔视为 gap，实际调用应明确阈值。没有 CRC 的记录不能
被称为已通过对应 CRC 校验；完整读到 EOF 才有完整性结论。

read_json_signal 返回 Signal 字段。CDR/Protobuf 数值解码不在该接口内。

## 12–13. 图片

```python
ops.image_quality(data, options=None) -> dict
ops.transform_image(bytes, options_json=None, crop=None,
                    resize=None, filter="lanczos3") -> list[int]
```

data/bytes 为压缩 PNG/JPEG 的 Python bytes。image_quality 的 options 为字典；
**transform_image 当前直接暴露 options_json 字符串**，可用 `json.dumps(options)`。
crop 为 `[x,y,width,height]`，resize 为 `[width,height]`，filter 可选 nearest/triangle/lanczos3。
变换结果是 PNG 的整数列表，转为 `bytes(result)` 后再保存或传递。

ImageOptions 默认 max_width=16384、max_height=16384、max_pixels=64000000、
dark_threshold=10、bright_threshold=245。必须满足合法尺寸及 dark<bright。
报告包含 width、height、pixels、luminance_mean/std、dark_fraction、bright_fraction、
laplacian_variance、rgb_sha256。小于 3×3 的图像 Laplacian 指标为 None。
示例见[媒体指南](guides/media.md)。

## 14. 视频

```python
ops.validate_video(path, *, ffmpeg="ffmpeg", ffprobe="ffprobe",
                   timeout_seconds=600.0) -> dict
```

对本地文件执行 probe，再完整解码第一路视频流；返回 complete、decoded、decoded_frames、
elapsed_seconds、probe。总超时预算在 (0,86400] 秒，单工具诊断输出有 2 MiB 限额。
工具不存在、超时、诊断错误、空视频或未完成解码均失败。没有 Python 独立 probe_video 接口。

## Rust-only 与版本

`gate`、`IntervalSet`、`map_clock`、`inspect_time`、`expand_batch_timestamps`、
`RawReader`、`SignalDecoder`、独立 `probe_video` 目前仅 Rust 可用。
时间异常也可经 Python inspect_signal/inspect_mcap 的 time 报告获得。
`ops.__version__` 是包版本字符串，不是处理算子。
