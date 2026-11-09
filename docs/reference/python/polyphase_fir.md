# mcap_ops.polyphase_fir

**Language: English | [Chinese](../../zh/reference/python/polyphase_fir.md)**

```python
mcap_ops.polyphase_fir(values, up, down, taps)
```

Offline centered FIR on a complete regular run. Pass a finite float64 (N,D) matrix (N >= 2, D > 0), positive integer rate ratio up/down, and finite contiguous 1-D odd-length float64 coefficients designed at the reduced upsampled rate. The operator multiplies taps by reduced up. Output is (ceil(N*up/down),D), centered at original row coordinate j*down/up, in source units. Outside the run the boundary line goes through the first and last rows. No timestamps, gap filling, phase shift or hidden filter design. Segment outages and choose coefficients before calling.

```python
import numpy as np
import mcap_ops as ops

x = np.arange(8., dtype=np.float64)[:, None]
y = ops.polyphase_fir(x, 1, 2, np.array([0.25, 0.5, 0.25]))
np.testing.assert_allclose(y[:, 0], [0., 2., 4., 6.])
```
