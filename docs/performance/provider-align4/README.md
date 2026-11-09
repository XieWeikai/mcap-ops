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
