# mcap_ops.transform_image

**Language: English | [Chinese](../../zh/reference/python/transform_image.md)**

Crop, then resize, and return PNG bytes as a Python integer list.

```python
mcap_ops.transform_image(bytes, options_json=None, crop=None, resize=None, filter="lanczos3")
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `bytes` | `bytes` | `required` | Compressed PNG/JPEG input. |
| `options_json` | `str or None` | `None` | JSON-encoded ImageOptions; unlike image_quality, not a dict. |
| `crop` | `list[int] or None` | `None` | [x,y,width,height], within the input image. |
| `resize` | `list[int] or None` | `None` | [width,height], positive and within configured limits. |
| `filter` | `str` | `"lanczos3"` | nearest, triangle, or lanczos3. |

### Configuration defaults

| Field | Default | Meaning |
| --- | --- | --- |
| `max_width / max_height` | `16384` | Positive dimension limits. |
| `max_pixels` | `64000000` | Positive total pixel limit. |
| `dark_threshold` | `10` | Inclusive lower luma threshold, uint8. |
| `bright_threshold` | `245` | Inclusive upper threshold; dark < bright. |

## Returns

list[int] containing the encoded PNG. Use bytes(result) before writing or decoding. Source bytes are unchanged.

## Errors

ValueError for invalid JSON/options, crop outside bounds, invalid resize/filter, or image decoding/encoding errors.

## Semantics and boundaries

Resize uses exact dimensions and can change aspect ratio. Crop coordinates are interpreted before resize. No model normalization, channel layout conversion, calibration adjustment, or video frame extraction is implicit.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

Requires Pillow to generate the image.

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

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
