# mcap_ops.lowpass_taps

**Language: English | [Chinese](../../zh/reference/python/lowpass_taps.md)**

Design normalized symmetric Hamming-windowed sinc lowpass coefficients.

```python
mcap_ops.lowpass_taps(sample_rate_hz, cutoff_hz, taps)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `sample_rate_hz` | `float` | `required` | Finite input sampling rate, Hz. |
| `cutoff_hz` | `float` | `required` | 0 < cutoff < sample_rate/2, Hz. |
| `taps` | `int` | `required` | Odd coefficient count in [3,4095]. |

## Returns

list[float] of length taps, symmetric and normalized to unit DC gain. Convert to a contiguous float64 array before passing to fir.

## Errors

ValueError for nonfinite frequencies, invalid cutoff, or even/out-of-range tap count.

## Semantics and boundaries

This designs coefficients only. Apply fir separately. Choose bandwidth relative to the new Nyquist limit before downsampling; this is not an automatic filter-design policy.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

```python
import numpy as np
import mcap_ops as ops
h = np.asarray(ops.lowpass_taps(200.0, 20.0, 31), dtype=np.float64)
assert len(h) == 31
np.testing.assert_allclose(h, h[::-1])
np.testing.assert_allclose(h.sum(), 1.0)
```

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
