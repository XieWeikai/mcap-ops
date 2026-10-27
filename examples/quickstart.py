"""Generated arrays only. Run with the installed package on the test host."""
import numpy as np
import mcap_ops as ops


def main():
    times = np.array([0, 10, 20], dtype=np.int64) * 1_000_000
    values = np.array([[0.0], [1.0], [2.0]], dtype=np.float64)
    target = np.asarray(ops.uniform_grid(0, 25_000_000, 200, 1, 100), dtype=np.int64)

    linear = ops.resample(
        times, values, target, method="linear",
        max_gap_ns=15_000_000, allow_future=True,
    )
    held = ops.resample(
        times, values, target, method="previous", max_age_ns=15_000_000,
    )
    np.testing.assert_allclose(linear["values"].ravel(), [0.0, 0.5, 1.0, 1.5, 2.0])
    np.testing.assert_array_equal(held["values"].ravel(), [0.0, 0.0, 1.0, 1.0, 2.0])
    assert linear["valid"].all() and not held["uses_future"].any()
    assert not np.shares_memory(linear["values"], values)

    bad = values.copy()
    bad[1, 0] = 100.0
    report = ops.inspect_signal(times, bad, {
        "lower": [-5.0], "upper": [5.0], "max_gap_ns": 15_000_000,
    })
    issues = [(issue["code"], issue["start_index"]) for issue in report["issues"]]
    assert issues == [("above_range", 1)] and bad[1, 0] == 100.0

    history = ops.history_windows(
        times, values,
        np.array([20_000_000], dtype=np.int64),
        np.array([-20_000_000, -10_000_000, 0], dtype=np.int64),
        max_age_ns=15_000_000,
    )
    assert history["values"].shape == (1, 3, 1)
    assert history["valid"].shape == (3,)
    assert history["valid"].all()
    print("linear:", linear["values"].ravel().tolist())
    print("previous:", held["values"].ravel().tolist())
    print("quality:", issues)
    print("history shape:", history["values"].shape)


if __name__ == "__main__":
    main()
