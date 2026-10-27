# mcap_ops.fir

**Language: English | [Chinese](../../zh/reference/python/fir.md)**

Filter regular-grid samples with explicitly bounded support.

```python
mcap_ops.fir(timestamps, values, taps, *, mode="causal", period_ns=1, tolerance_ns=0)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `timestamps` | `int64[N]` | `required` | Contiguous 1-D source timestamps, nanoseconds. |
| `values` | `float64[N] or [N,D]` | `required` | Numeric samples; strided views accepted. |
| `taps` | `float64[K]` | `required` | Contiguous finite coefficients, 1 <= K <= 4095. |
| `mode` | `str` | `"causal"` | causal or centered; centered requires odd K. |
| `period_ns` | `int` | `1` | Positive expected input period, ns. |
| `tolerance_ns` | `int` | `0` | 0 <= tolerance < period; spacing tolerance, ns. |

## Returns

Filtered dictionary: timestamps int64[N], values float64[N,D], channels, valid list[bool], mode, lookahead_samples, group_delay_samples (float or None).

## Errors

ValueError for unordered time, invalid taps, period/tolerance, or centered even-length coefficients. Irregular/missing support invalidates affected outputs.

## Semantics and boundaries

Causal output i is sum(taps[k] * x[i-k]). Centered mode shifts output by floor(K/2). Edges are not padded; gaps and nonfinite rows reset support. Symmetric causal taps report (K-1)/2 delay; asymmetric causal taps report None. Centered delay is 0 with K//2 lookahead.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

```python
import numpy as np
import mcap_ops as ops

t = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
x = np.array([0.0, 1.0, 2.0], dtype=np.float64)
r = ops.fir(t, x, np.array([0.5, 0.5], dtype=np.float64), period_ns=10_000_000)
assert r["valid"] == [False, True, True]
np.testing.assert_allclose(r["values"][1:, 0], [0.5, 1.5])
assert r["group_delay_samples"] == 0.5
```

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
