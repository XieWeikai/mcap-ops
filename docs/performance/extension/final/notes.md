All final checks passed on Linux execution environment: rustfmt, Clippy, 36 Rust tests, 180 randomized
core scenarios, 13 image fixtures, two MCAP fixtures, 3630 clock edge cases,
168 grid cases, 75 Hampel cases, 50 SLERP cases, five Python smoke tests and
236 public-interface comparisons. The installed release wheel separately passed
five tests and 236 interface comparisons. Its SHA-256 is recorded in
`verification.json`; the local download was independently hash-checked.

The final whole-suite timings are not identical to isolated trial timings.
An independent eight-block repeat (`focused-native.json`) found clock offset
effectively unchanged (-0.07%) after -21.90% in the full run. Dense interval
intersection measured -2.59% in that repeat, within the 3% per-case gate; late
intersection remained +98.68%.

**Remaining performance limitations:** raw MCAP topic selection measured
-7.28% in the full run and -8.15% in the focused repeat. Additional FIR workload
checks measured short-vector -13.69%, small-vector -7.08% and invalid-support
-5.35%, although the FIR operator body was restored exactly. The full-suite
31-tap FIR cases went in the opposite direction (+25.20%/+17.65%). No FIR
transposition optimization remains in production.

`unchanged-source.json` verifies that the FIR and map_clock function bodies,
and the entire MCAP adapter source, are byte-identical to the extension baseline.
The eight-block identical-source control (`sensitivity-control.json`) measured
short-vector FIR +0.57% and invalid-support FIR -0.20%; it therefore does not
explain away the final differences. Their cause is not established. They must
remain visible rather than being attributed to an unimplemented FIR optimization
or described as universal speedups. Final acceptance records refer to their
stated operator workloads and gates, not a guarantee across every input shape
or combined binary layout.

The first unconditional FIR acceptance was explicitly withdrawn in commit
`2c913ba`, and its guarded follow-up failed the expanded gate. Original evidence
and the rejected patches are retained. These diagnostic repeats and controls
are validation of the same twenty candidates, not extra optimization rounds.

The wheel targets Linux x86-64 / glibc 2.39+ with CPython abi3 (3.10+).
Execution was verified with CPython 3.12.3 and NumPy 2.5.4. No package was published
to an external registry.
