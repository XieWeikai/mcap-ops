# mcap_ops.rgb_histogram

**语言：中文 | [English](../../../reference/python/rgb_histogram.md)**

```python
mcap_ops.rgb_histogram(image)
```

输入为 uint8 RGB 图像 (高,宽,3)，允许非连续裁剪视图。返回 (3,256) 的独立 int64 计数，按 R、G、B 依次排列；每个原始像素计一次，空图块各项为零。没有时钟或缺帧策略，不做编码、插值或颜色转换；调用方应用原始帧的重复权重。形状或类型不匹配会失败。

```python
import numpy as np
import mcap_ops as ops

a = np.array([[[0, 1, 2], [0, 3, 2]]], dtype=np.uint8)
h = ops.rgb_histogram(a)
assert h[0, 0] == h[2, 2] == 2 and h[1, 1] == 1
```
