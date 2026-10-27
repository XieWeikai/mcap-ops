# mcap_ops.validate_video

**Language: English | [Chinese](../../zh/reference/python/validate_video.md)**

Probe a local video, then completely decode its first video stream.

```python
mcap_ops.validate_video(path, *, ffmpeg="ffmpeg", ffprobe="ffprobe", timeout_seconds=600.0)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `path` | `str` | `required` | Regular local video file. |
| `ffmpeg / ffprobe` | `str` | `"ffmpeg" / "ffprobe"` | Executable names or explicit paths; installed by caller. |
| `timeout_seconds` | `float` | `600.0` | Total budget across both tools, in (0,86400]. |

## Returns

VideoValidation dictionary: complete, decoded, decoded_frames, elapsed_seconds, probe (FFprobe JSON). Success requires at least one decoded frame and a completion marker.

## Errors

ValueError for missing executables/files, missing streams, tool diagnostics/failure, timeout, oversized output, or incomplete decoding.

## Semantics and boundaries

Each captured stdout/stderr is capped at 2 MiB. Only the first video stream is decoded; audio and visual quality are not certified. This does not extract or synchronize frames. Standalone probe_video is Rust-only.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

Requires caller-installed FFmpeg/FFprobe.

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

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
