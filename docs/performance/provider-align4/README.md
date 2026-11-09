# Offline alignment and media operators: RSI contract

The functional baseline includes four independent operations. Evaluation uses
only generated data. The provider remains responsible for interpreting topics,
policy, filter design, source clock selection, media encoding and cache identity.

| Operation | Generated timed cases | Required invariant |
| --- | --- | --- |
| sample_support | scalar/multi episode lengths, targets every third jittered observation plus 1 ns | original previous/next indices and support mask exact, including empty input, unsorted queries and extreme epochs |
| motion_bounds | 1 and 16 channels at 1 kHz, 200 ms endpoint windows | inclusive median windows, strict thresholds, one original neighbour, half-open output or no selection |
| polyphase_fir | 3:7 scalar and 1:4 multichannel, centered 81-tap FIR | compare to explicit upsample/convolve/decimate, rtol 2e-13, atol 2e-14, including global linear boundary extension |
| rgb_histogram | textured and constant RGB8 | exact integer counts including non-contiguous crops before encoding |

Four separate candidate changes per operation, each against its last accepted
implementation. Native profiles and measurements use the same release build
flags; each trial runs workspace, Python and independent oracle checks before
four interleaved AB/BA blocks (seven calibrated samples per side). Accept only
if the geometric latency reduction reaches 8% in every block and no median
case regresses more than 3%, with complexity reviewed. Archive rejected patches.
Operator timings do not measure provider throughput.

## Results

All 16 experiments completed. Two changes met the acceptance gate. Final comparisons use independent, initially empty Cargo target directories at the functional baseline and reviewed source revisions. A shared-cache exploratory comparison failed binary identity verification and is excluded.

| Operation | Round | Decision | Worst block reduction | Worst case median reduction |
| --- | ---: | --- | ---: | ---: |
| motion_bounds | 1 | [rejected](results/align4-motion-bounds-01.json) | -0.29% | 0.62% |
| motion_bounds | 2 | [rejected](results/align4-motion-bounds-02.json) | -5.97% | -6.70% |
| motion_bounds | 3 | [rejected](results/align4-motion-bounds-03.json) | -0.59% | 0.34% |
| motion_bounds | 4 | [rejected](results/align4-motion-bounds-04.json) | 4.82% | 1.53% |
| polyphase_fir | 1 | [rejected](results/align4-polyphase-fir-01.json) | 0.24% | 1.15% |
| polyphase_fir | 2 | [accepted](results/align4-polyphase-fir-02.json) | 55.18% | 49.20% |
| polyphase_fir | 3 | [rejected](results/align4-polyphase-fir-03.json) | 0.91% | -2.23% |
| polyphase_fir | 4 | [rejected](results/align4-polyphase-fir-04.json) | -1.76% | -3.34% |
| rgb_histogram | 1 | [rejected](results/align4-rgb-histogram-01.json) | -4.52% | -8.05% |
| rgb_histogram | 2 | [rejected](results/align4-rgb-histogram-02.json) | 3.81% | -10.16% |
| rgb_histogram | 3 | [rejected](results/align4-rgb-histogram-03.json) | -2.58% | -5.01% |
| rgb_histogram | 4 | [rejected](results/align4-rgb-histogram-04.json) | -96.85% | -168.72% |
| sample_support | 1 | [accepted](results/align4-sample-support-01.json) | 56.11% | 0.36% |
| sample_support | 2 | [rejected](results/align4-sample-support-02.json) | -4.91% | 0.49% |
| sample_support | 3 | [rejected](results/align4-sample-support-03.json) | -95.41% | -308.17% |
| sample_support | 4 | [rejected](results/align4-sample-support-04.json) | -10.87% | -8.20% |

[Integrated raw samples](integrated.json) · [Native profile identities](evidence/manifest.json). The rebuilt non-editable release wheel passed all 90 Python tests with SciPy 1.18.1 as the FIR oracle. Linux x86-64 wheel SHA-256: `9454a2137942a9e9e0f1064bb211ca2573e70529461f8ea42e53daf77e80349b`. Unchanged kernels can vary with binary layout and measurement noise. No provider or recording throughput is inferred from these numbers.
