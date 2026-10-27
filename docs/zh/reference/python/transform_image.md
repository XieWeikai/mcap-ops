# mcap_ops.transform_image

**语言：中文 | [English](../../../reference/python/transform_image.md)**

先裁剪，再缩放，以 Python 整数列表返回 PNG 字节。

```python
mcap_ops.transform_image(bytes, options_json=None, crop=None, resize=None, filter="lanczos3")
```

## 参数

| 参数 | 类型 | 默认值 | 含义 |
| --- | --- | --- | --- |
| `bytes` | `bytes` | `required` | 压缩 PNG/JPEG 输入。 |
| `options_json` | `str or None` | `None` | JSON 编码的 ImageOptions；不同于 image_quality，这里不是 dict。 |
| `crop` | `list[int] or None` | `None` | [x,y,width,height]，必须位于输入图像内。 |
| `resize` | `list[int] or None` | `None` | [width,height]，正数且不超过配置上限。 |
| `filter` | `str` | `"lanczos3"` | nearest、triangle 或 lanczos3。 |

### 配置默认值

| 字段 | 默认值 | 含义 |
| --- | --- | --- |
| `max_width / max_height` | `16384` | 正的尺寸上限。 |
| `max_pixels` | `64000000` | 正的总像素上限。 |
| `dark_threshold` | `10` | 包含等号的低亮度阈值，uint8。 |
| `bright_threshold` | `245` | 包含等号的高亮度阈值；dark < bright。 |

## 返回值

包含 PNG 编码字节的 list[int]。写入或解码前使用 bytes(result)。源字节保持不变。

## 错误

JSON/选项非法、裁剪越界、缩放/filter 非法、图像解码/编码失败时 ValueError。

## 语义与边界

按精确尺寸缩放，可能改变宽高比。先按原图坐标裁剪，再缩放。不隐式进行模型归一化、通道布局转换、标定修正或视频帧提取。

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
out = bytes(ops.transform_image(data, crop=[0, 0, 4, 4], resize=[2, 2], filter="nearest"))
r = ops.image_quality(out)
assert (r["width"], r["height"]) == (2, 2)
```

[接口索引](../index.md) · [结果与类型](../types.md) · [Python 源码](../../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../../crates/python/src/lib.rs)
