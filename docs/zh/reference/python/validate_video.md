# mcap_ops.validate_video

**语言：中文 | [English](../../../reference/python/validate_video.md)**

探测本地视频，再完整解码第一个视频流。

```python
mcap_ops.validate_video(path, *, ffmpeg="ffmpeg", ffprobe="ffprobe", timeout_seconds=600.0)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `path` | `str` | `required` | 本地普通视频文件。 |
| `ffmpeg / ffprobe` | `str` | `"ffmpeg" / "ffprobe"` | 可执行文件名或显式路径，由调用方安装。 |
| `timeout_seconds` | `float` | `600.0` | 两个工具共用的总时间预算，范围 (0,86400] 秒。 |

## 返回值

VideoValidation 字典：complete、decoded、decoded_frames、elapsed_seconds、probe（FFprobe JSON）。成功要求至少一帧且收到完成标记。

## 错误

可执行文件/文件缺失、无视频流、工具诊断/失败、超时、输出超限、解码不完整时 ValueError。

## 语义与边界

每路捕获 stdout/stderr 上限为 2 MiB。只解码第一个视频流，不证明音频或画面质量。不提取或同步帧。独立 probe_video 仅有 Rust 接口。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

需要调用方安装 FFmpeg/FFprobe。

```python
import subprocess
import tempfile
from pathlib import Path
import mcap_ops as ops

with tempfile.TemporaryDirectory() as directory:
    path = Path(directory) / "generated.mkv"
    subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i",
                    "color=c=green:s=32x32:r=5:d=1", "-c:v", "ffv1", str(path)], check=True)
    r = ops.validate_video(str(path), timeout_seconds=30.0)
    assert r["complete"] and r["decoded_frames"] == 5
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
