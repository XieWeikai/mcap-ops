# mcap_ops.image_quality

**Language: English | [Chinese](../../zh/reference/python/image_quality.md)**

Measure decoded PNG/JPEG quality and a deterministic RGB fingerprint.

```python
mcap_ops.image_quality(data, options=None)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `data` | `bytes` | `required` | Compressed PNG or JPEG bytes. |
| `options` | `dict or None` | `None` | ImageOptions limits and exposure thresholds. |

### Configuration defaults

| Field | Default | Meaning |
| --- | --- | --- |
| `max_width / max_height` | `16384` | Positive dimension limits. |
| `max_pixels` | `64000000` | Positive total pixel limit. |
| `dark_threshold` | `10` | Inclusive lower luma threshold, uint8. |
| `bright_threshold` | `245` | Inclusive upper threshold; dark < bright. |

## Returns

ImageQuality dictionary: width, height, pixels, luminance_mean/std, dark_fraction, bright_fraction, laplacian_variance, rgb_sha256. Luminance is in [0,255], fractions in [0,1]; Laplacian variance is None below 3x3.

## Errors

ValueError for unsupported/corrupt images, invalid options, or exceeded dimension/pixel/allocation limits.

## Semantics and boundaries

RGB luma weights are 0.2126/0.7152/0.0722; thresholds include equality. The hash includes width, height, and decoded RGB bytes, not the compressed file. Blur/exposure acceptance thresholds are caller policy; these metrics do not certify semantic quality.

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
r = ops.image_quality(data)
assert r["width"] == 8 and r["pixels"] == 64
assert r["laplacian_variance"] == 0.0
assert len(r["rgb_sha256"]) == 64
```

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
