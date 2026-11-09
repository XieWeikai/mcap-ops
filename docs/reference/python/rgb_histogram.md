# mcap_ops.rgb_histogram

**Language: English | [Chinese](../../zh/reference/python/rgb_histogram.md)**

```python
mcap_ops.rgb_histogram(image)
```

Pass uint8 RGB in (height,width,3), including strided crops. Returns owned int64 counts (3,256) in R,G,B order. Each source pixel contributes once, before compression or color conversion; empty tiles have zero counts. No time/gap policy or statistics from synthesized frames. Apply source frame repeat weights in the caller. Wrong shape or dtype fails.

```python
import numpy as np
import mcap_ops as ops

a = np.array([[[0, 1, 2], [0, 3, 2]]], dtype=np.uint8)
h = ops.rgb_histogram(a)
assert h[0, 0] == h[2, 2] == 2 and h[1, 1] == 1
```
