#!/usr/bin/env python3
"""Python bridge benchmarks. Run only on reference-linux with an explicit package snapshot."""
import argparse
import cProfile
import io
import json
import os
from pathlib import Path
import statistics
import subprocess
import tempfile
import time

import numpy as np
from PIL import Image
from mcap.writer import CompressionType, Writer
import mcap_ops as ops


def measure(name, operation, args):
    if args.case and name not in args.case.split(","):
        return
    operation()
    if args.profile:
        profile = cProfile.Profile()
        profile.runcall(operation)
        profile.dump_stats(args.profile)
        return
    iterations = 1
    millis = float(os.getenv("RSI_MILLIS", "20"))
    while True:
        start = time.perf_counter_ns()
        for _ in range(iterations):
            operation()
        if (time.perf_counter_ns() - start) / 1e6 >= millis or iterations >= 65536:
            break
        iterations *= 2
    samples = []
    for _ in range(int(os.getenv("RSI_SAMPLES", "7"))):
        start = time.perf_counter_ns()
        for _ in range(iterations):
            operation()
        samples.append((time.perf_counter_ns() - start) / iterations)
    print(json.dumps({"case": name, "median_ns": statistics.median(samples),
                      "samples_ns": samples, "iterations": iterations}), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--case")
    parser.add_argument("--profile")
    args = parser.parse_args()
    expected = os.getenv("RSI_PYTHON_ROOT")
    if expected and not Path(ops.__file__).resolve().is_relative_to(Path(expected).resolve()):
        raise RuntimeError(f"wrong package imported: {ops.__file__}")
    n, d = 30_000, 6
    timestamps = np.arange(n, dtype=np.int64) * 1_000_000
    values = np.sin(np.arange(n * d, dtype=np.float64).reshape(n, d) * 0.001)
    target = np.arange(10_000, dtype=np.int64) * 2_000_000 + 500_000
    centers = timestamps[10:8010:2]
    offsets = np.array([-3_000_000, -2_000_000, -1_000_000, 0], dtype=np.int64)
    taps = np.array(ops.lowpass_taps(1000, 50, 31), dtype=np.float64)
    measure("python.inspect_signal", lambda: ops.inspect_signal(timestamps, values), args)
    for method in ("previous", "linear"):
        measure(f"python.resample.{method}", lambda: ops.resample(
            timestamps, values, target, method=method, max_gap_ns=2_000_000,
            max_age_ns=2_000_000, allow_future=True), args)
    measure("python.history_windows", lambda: ops.history_windows(
        timestamps, values, centers, offsets, max_age_ns=2_000_000), args)
    measure("python.align_timestamps", lambda: ops.align_timestamps(
        timestamps, target, max_past_ns=2_000_000), args)
    measure("python.uniform_grid", lambda: ops.uniform_grid(0, 20_000_000_000, 1000, 1, 30_000), args)
    measure("python.ema", lambda: ops.ema(timestamps, values, 0.05, 2_000_000), args)
    measure("python.fir", lambda: ops.fir(timestamps, values, taps, period_ns=1_000_000), args)
    measure("python.lowpass_taps", lambda: ops.lowpass_taps(1000, 50, 63), args)
    measure("python.unwrap_angles", lambda: ops.unwrap_angles(timestamps, values, max_gap_ns=2_000_000), args)
    pixels = (np.arange(320 * 240 * 3) % 256).astype(np.uint8).reshape(240, 320, 3)
    buffer = io.BytesIO()
    Image.fromarray(pixels).save(buffer, format="PNG")
    image = buffer.getvalue()
    measure("python.image_quality", lambda: ops.image_quality(image), args)
    measure("python.transform_image", lambda: ops.transform_image(image, resize=[160, 120]), args)
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "input.mcap"
        with path.open("wb") as stream:
            writer = Writer(stream, compression=CompressionType.NONE)
            writer.start()
            cid = writer.register_channel("/q", "json", 0)
            for i in range(5000):
                writer.add_message(cid, i*1_000_000, json.dumps({"q":[i,1,2,3]}).encode(), i*1_000_000)
            writer.finish()
        measure("python.inspect_mcap", lambda: ops.inspect_mcap(str(path), max_gap_ns=2_000_000), args)
        measure("python.read_json_signal", lambda: ops.read_json_signal(str(path), "/q", ["/q"], 4), args)
        if args.case is None or "python.validate_video" in args.case.split(","):
            video = Path(directory) / "clip.mp4"
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-f", "lavfi",
                "-i", "testsrc=size=320x240:rate=30", "-t", "2", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", str(video)], check=True)
            measure("python.validate_video", lambda: ops.validate_video(str(video)), args)


if __name__ == "__main__":
    main()
