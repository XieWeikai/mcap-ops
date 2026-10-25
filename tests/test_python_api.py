import numpy as np
import mcap_ops


def test_python_resample_and_provenance():
    result = mcap_ops.resample(
        np.array([0, 10, 20], dtype=np.int64),
        np.array([[0.0], [10.0], [20.0]], dtype=np.float64),
        np.array([0, 5, 20], dtype=np.int64),
        method="linear", max_gap_ns=20, max_age_ns=20, allow_future=True,
    )
    assert result["status"].tolist() == [0, 0, 0]
    assert result["values"].ravel().tolist() == [0.0, 5.0, 20.0]
    assert result["source_left"].tolist() == [0, 0, 2]


def test_python_quality_does_not_repair_input():
    values = np.array([1.0, 100.0, 1.0])
    report = mcap_ops.inspect_signal(
        np.array([0, 10, 20], dtype=np.int64), values,
        {"hampel_window_ns": 20, "hampel_min_deviation": 1.0},
    )
    assert any(issue["code"] == "spike" for issue in report["issues"])
    assert values[1] == 100.0


def test_python_alignment_is_explicitly_causal_by_default():
    result = mcap_ops.align_timestamps(
        np.array([10, 20], dtype=np.int64), np.array([9, 15, 19], dtype=np.int64),
        max_past_ns=10,
    )
    assert result["valid"].tolist() == [False, True, True]
    assert result["indices"].tolist() == [-1, 0, 0]


def test_python_history_keeps_window_shape():
    result = mcap_ops.history_windows(
        np.array([0, 5, 10, 15], dtype=np.int64),
        np.array([0.0, 5.0, 10.0, 15.0]),
        np.array([10, 15], dtype=np.int64),
        np.array([-10, -5, 0], dtype=np.int64),
        method="previous", max_gap_ns=10, max_age_ns=10,
    )
    assert result["values"].shape == (2, 3, 1)
    assert result["timestamps"].shape == (2, 3)
    assert result["valid"].all()


def test_python_filter_reports_latency_contract():
    result = mcap_ops.fir(
        np.arange(5, dtype=np.int64), np.arange(5, dtype=np.float64),
        np.array([0.25, 0.5, 0.25]), period_ns=1,
    )
    assert result["mode"] == "causal"
    assert result["lookahead_samples"] == 0
    assert result["group_delay_samples"] == 1.0
