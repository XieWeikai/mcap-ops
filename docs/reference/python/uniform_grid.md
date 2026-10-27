# mcap_ops.uniform_grid

**Language: English | [Chinese](../../zh/reference/python/uniform_grid.md)**

Construct a rational-rate nanosecond timeline.

```python
mcap_ops.uniform_grid(start_ns, end_ns, rate_num, rate_den, max_points)
```

## Parameters

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `start_ns / end_ns` | `int64` | `required` | Half-open [start_ns,end_ns); ordered bounds. |
| `rate_num / rate_den` | `uint32` | `required` | Positive numerator/denominator; frequency in Hz. |
| `max_points` | `int` | `required` | Positive bound on output length. |

## Returns

list[int], not a NumPy array. Equal start/end returns an empty list. Convert with np.asarray(..., dtype=np.int64).

## Errors

ValueError for reversed bounds, zero rate/count, sub-nanosecond period, or exceeding max_points. OverflowError for integer conversion/arithmetic overflow.

## Semantics and boundaries

Integer arithmetic avoids floating-point epoch conversion. Points use rounded rational periods, so 30000/1001 Hz is supported without accumulating rounded-period drift. The end is excluded.

Numeric inputs follow the [common contracts](../index.md): no implicit dtype conversion, contiguous time arrays, copied inputs with no mutation. Python/PyO3 conversion can also raise TypeError or OverflowError.

## Example

```python
import mcap_ops as ops
grid = ops.uniform_grid(0, 21_000_000, 100, 1, 10)
assert grid == [0, 10_000_000, 20_000_000]
```

[API index](../index.md) · [Results and types](../types.md) · [Python source](../../../python/mcap_ops/__init__.py) · [Rust / PyO3](../../../crates/python/src/lib.rs)
