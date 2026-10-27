# mcap_ops.image_quality

**语言：中文 | [English](../../../reference/python/image_quality.md)**

测量 PNG/JPEG 解码质量指标与确定性 RGB 指纹。

```python
mcap_ops.image_quality(data, options=None)
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `data` | `bytes` | `required` | 压缩 PNG 或 JPEG 字节。 |
| `options` | `dict or None` | `None` | ImageOptions 上限与曝光阈值。 |

### 配置默认值

| 字段 | 默认值 | 含义 |
| --- | --- | --- |
| `max_width / max_height` | `16384` | 正的尺寸上限。 |
| `max_pixels` | `64000000` | 正的总像素上限。 |
| `dark_threshold` | `10` | 包含等号的低亮度阈值，uint8。 |
| `bright_threshold` | `245` | 包含等号的高亮度阈值；dark < bright。 |

## 返回值

ImageQuality 字典：width、height、pixels、luminance_mean/std、dark_fraction、bright_fraction、laplacian_variance、rgb_sha256。亮度范围 [0,255]，比例范围 [0,1]；小于 3x3 时 Laplacian 方差为 None。

## 错误

格式不支持、图像损坏、选项非法、尺寸/像素/分配超限时 ValueError。

## 语义与边界

RGB 亮度权重为 0.2126/0.7152/0.0722，曝光阈值包含等号。hash 包含宽高和解码 RGB 字节，不是压缩文件 hash。模糊/曝光的接收阈值由调用方决定，这些指标不证明语义质量。

所有数值输入遵循[共同输入契约](../index.md)：dtype 不自动转换，时间数组必须连续，输入复制且不被修改。类型转换错误也可能由 Python/PyO3 抛出 TypeError 或 OverflowError。

## 示例

需要 Pillow，仅用于生成图像。

```python
from io import BytesIO
from PIL import Image
import mcap_ops as ops

buffer = BytesIO()
Image.new("RGB", (8, 8), (128, 128, 128)).save(buffer, format="PNG")
data = buffer.getvalue()
r = ops.image_quality(data)
assert r["width"] == 8 and r["pixels"] == 64
assert r["laplacian_variance"] == 0.0
assert len(r["rgb_sha256"]) == 64
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
