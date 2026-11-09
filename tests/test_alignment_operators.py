"""Independent public-interface oracles on generated inputs; no recordings required."""
import math

import numpy as np
import pytest

import mcap_ops as ops


def test_support_matches_original_rows_and_never_hides_reversals():
    rng = np.random.default_rng(27)
    for n in (0, 1, 200):
        t = 1_700_000_000_000_000_000 + rng.integers(1, 50, size=n).cumsum()
        q = np.r_[t[::-1], t + 1, t - 1]
        r = ops.sample_support(t, q, 19)
        low = np.searchsorted(t, q, "right") - 1
        high = np.searchsorted(t, q, "left")
        np.testing.assert_array_equal(r["previous"], low)
        np.testing.assert_array_equal(r["next"], np.where(high == n, -1, high))
        assert r["supported"].tolist() == [l >= 0 and h < n and int(t[h])-int(t[l]) <= 19 for l, h in zip(low, high)]
    limits = np.array([-(2**63), 2**63-1], np.int64)
    assert ops.sample_support(limits, np.array([0]), 2**63-1)["supported"].tolist() == [False]
    for bad in (limits[::-1].copy(), np.array([2, 2])):
        with pytest.raises(ValueError):
            ops.sample_support(bad, limits, 10)


def test_motion_keeps_margin_and_interior_pause():
    rng = np.random.default_rng(7)
    for n in (2, 51, 151):
        t = np.arange(n, dtype=np.int64) * 20_000_000
        for d in (1, 16):
            a = np.zeros((n, d))
            a[n//3:n//2] = rng.random(d) + 1
            a[2*n//3:3*n//4] = 2
            limit = np.full(d, 0.1)
            first = np.median(a[t <= t[0]+200_000_000], axis=0)
            last = np.median(a[t >= t[-1]-200_000_000], axis=0)
            f = np.where(np.any(abs(a-first) > limit, axis=1))[0]
            l = np.where(np.any(abs(a-last) > limit, axis=1))[0]
            expected = (max(0, f[0]-1), min(n, l[-1]+2)) if len(f) and len(l) else None
            assert ops.motion_bounds(t, a, limit, 200_000_000) == expected
    assert ops.motion_bounds(np.arange(3), np.array([0., 1., 0.]), np.ones(1), 0) is None


@pytest.mark.parametrize("up,down", [(1,4), (3,7), (5,2), (6,14), (1,1)])
def test_polyphase_matches_explicit_upsampled_convolution(up, down):
    rng = np.random.default_rng(47)
    a = rng.normal(size=(43, 6))[:, ::2]
    taps = np.kaiser(35, 5.0) * np.sinc(np.arange(-17,18)/7)
    taps /= taps.sum()
    g = math.gcd(up, down)
    u, d = up//g, down//g
    pad = len(taps)
    t = np.arange(-pad, len(a)+pad)
    slope = (a[-1]-a[0])/(len(a)-1)
    x = np.stack([a[i] if 0 <= i < len(a) else a[0]+i*slope for i in t])
    result = ops.polyphase_fir(a, up, down, taps)
    expect = []
    for column in x.T:
        zeros = np.zeros(len(x)*u)
        zeros[::u] = column
        whole = np.convolve(zeros, taps*u)
        first = pad*u+len(taps)//2
        expect.append(whole[first:first+len(a)*u:d])
    np.testing.assert_allclose(result, np.array(expect).T, rtol=2e-13, atol=2e-14)


def test_histogram_counts_rgb_and_strided_tiles_exactly():
    a = np.random.default_rng(73).integers(256, size=(110, 192, 3), dtype=np.uint8)
    for tile in (a, a[:, ::-2, :], a[:0]):
        expected = [np.bincount(ch.ravel(), minlength=256) for ch in tile.transpose(2,0,1)]
        np.testing.assert_array_equal(ops.rgb_histogram(tile), expected)
    with pytest.raises(ValueError):
        ops.rgb_histogram(a[:,:,:2])


@pytest.mark.parametrize("up,down", [(1, 4), (3, 7), (2, 1), (50, 199)])
def test_kaiser_linear_edges_match_scipy(up, down):
    from scipy.signal import firwin, resample_poly
    x = np.random.default_rng(411).normal(size=(107, 14))
    rate = max(up, down)
    taps = firwin(20*rate+1, 1/rate, window=("kaiser", 5.0))
    y = ops.polyphase_fir(x, up, down, taps)
    reference = resample_poly(x, up, down, axis=0, padtype="line")
    np.testing.assert_allclose(y, reference, rtol=2e-13, atol=2e-14)
