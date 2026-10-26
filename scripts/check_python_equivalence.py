#!/usr/bin/env python3
"""Compare public wrapper results from two package snapshots, including NaNs/types."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

import numpy as np
from mcap.writer import CompressionType, Writer


def load(name, root):
    package = Path(root).resolve() / "mcap_ops"
    spec = importlib.util.spec_from_file_location(name, package / "__init__.py",
        submodule_search_locations=[str(package)])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def equal(a, b, path="result"):
    if isinstance(a, np.ndarray):
        assert isinstance(b, np.ndarray), path
        assert a.dtype == b.dtype and a.shape == b.shape, path
        if a.dtype.kind == "f":
            np.testing.assert_allclose(a, b, rtol=1e-10, atol=1e-10, equal_nan=True, err_msg=path)
        else:
            np.testing.assert_array_equal(a, b, err_msg=path)
    elif isinstance(a, dict):
        assert isinstance(b, dict) and a.keys() == b.keys(), path
        assert list(a) == list(b), f"{path}: mapping iteration order changed"
        for key in a:
            equal(a[key], b[key], f"{path}.{key}")
    elif isinstance(a, (list, tuple)):
        assert type(a) is type(b) and len(a) == len(b), path
        for i, (x, y) in enumerate(zip(a, b)):
            equal(x, y, f"{path}[{i}]")
    elif isinstance(a, float):
        assert isinstance(b, float), path
        np.testing.assert_allclose(a, b, rtol=1e-10, atol=1e-10, equal_nan=True, err_msg=path)
    else:
        assert type(a) is type(b) and a == b, (path, a, b)


def invoke(module, operation_name, *args, **kwargs):
    try:
        return getattr(module, operation_name)(*args, **kwargs)
    except Exception as error:
        return {"exception_type": type(error).__name__, "message": str(error)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    args = parser.parse_args()
    old = load("_rsi_before", args.before)
    new = load("_rsi_after", args.after)
    rng = np.random.default_rng(2319)
    checks = 0
    def compare(operation_name, *args, **kwargs):
        nonlocal checks
        equal(invoke(old, operation_name, *args, **kwargs), invoke(new, operation_name, *args, **kwargs), operation_name)
        checks += 1
    for count in [0, 1, 3, 17, 64]:
        times = np.arange(count, dtype=np.int64) * 10
        base = rng.normal(size=(count, 8))
        arrays = [base[:, :4], base[:, ::2], np.asfortranarray(base[:, :4]), base[:, 0]]
        for data in arrays:
            if count > 3:
                data = data.copy()
                data.flat[1] = np.nan
                data.flat[3] = np.inf
            target = np.arange(-5, count * 10 + 10, 5, dtype=np.int64)
            for method in ["previous", "nearest", "linear"]:
                for future in [False, True]:
                    compare("resample", times, data, target, method=method,
                            max_age_ns=10, max_gap_ns=20, allow_future=future)
            compare("history_windows", times, data, times, np.array([-20,-10,0],dtype=np.int64), max_age_ns=10)
            compare("inspect_signal", times, data)
            compare("ema", times, data, 0.05, 20)
            compare("fir", times, data, np.array([0.25,0.5,0.25]), period_ns=10)
            compare("unwrap_angles", times, data, max_gap_ns=20)
        compare("align_timestamps", times, target, max_past_ns=10)
        compare("uniform_grid", 0, 1_000_000, 30000, 1001, 100)
    for invalid in [np.array([2,1],dtype=np.int64), np.array([0,0],dtype=np.int64)]:
        compare("resample", invalid, np.ones((2,1)), invalid, max_age_ns=20)
    compare("resample", np.arange(8,dtype=np.int64)[::2], np.ones(4), np.array([0],dtype=np.int64))
    compare("lowpass_taps", 200.0, 20.0, 31)
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "data.mcap"
        with path.open("wb") as stream:
            writer = Writer(stream, compression=CompressionType.NONE)
            writer.start()
            channel = writer.register_channel("/q", "json", 0)
            for i in range(30):
                writer.add_message(channel, i*10, json.dumps({"q":[i,2,3]}).encode(), i*10)
            writer.finish()
        compare("inspect_mcap", str(path), max_gap_ns=20)
        compare("read_json_signal", str(path), "/q", ["/q"], 3)
    result = new.resample(np.array([0,10],dtype=np.int64), np.array([1.,2.]),
                          np.array([0,10],dtype=np.int64), max_age_ns=10)
    result["values"][0,0] = 42.0
    assert result["values"].flags.writeable
    print(f"Python public-interface equivalence: {checks} comparisons passed")


if __name__ == "__main__":
    main()
