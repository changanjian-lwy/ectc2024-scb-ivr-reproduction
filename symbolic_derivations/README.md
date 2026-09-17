# Symbolic and Event-Driven Analysis

This directory keeps the equation-first analysis separate from LTspice
experiments. It contains three evidence branches; none may silently borrow a
rule from another branch.

## Reading order

1. [`00_Common_Symbols_and_Boundaries.md`](00_Common_Symbols_and_Boundaries.md)
   — shared notation and non-negotiable boundaries.
2. [`01_P24_native/DERIVATION.md`](01_P24_native/DERIVATION.md) — 2024-native
   topology and explicitly reported operations only.
3. [`02_P25_native/DERIVATION.md`](02_P25_native/DERIVATION.md) — native
   three-phase, six-mode calibration.
4. [`02_P25_native/30_P25_NATIVE_METHOD_CALIBRATION.md`](02_P25_native/30_P25_NATIVE_METHOD_CALIBRATION.md)
   — fixed-slot, event-timed and periodic-shooting comparisons.
5. [`02_P25_native/31_P25_INDUCTANCE_OPERATING_POINT_CLOSURE.md`](02_P25_native/31_P25_INDUCTANCE_OPERATING_POINT_CLOSURE.md)
   — independent 22 nH / 500 ns / peak-current consistency audit.
6. [`02_P25_native/32_STRICT_JOINT_OPTIMIZATION.md`](02_P25_native/32_STRICT_JOINT_OPTIMIZATION.md)
   — hard-gated joint feasibility analysis.
7. [`03_P24_primary_P25_supplement/DERIVATION.md`](03_P24_primary_P25_supplement/DERIVATION.md)
   — P24 four-phase topology with each P25-derived supplement labelled.
8. `03_P24_primary_P25_supplement/01_...md` through `29_...md` — the detailed
   derivation and numerical-audit sequence in chronological order.

## Branch boundaries

| Branch | Topology and timing source | Limitation |
|---|---|---|
| `01_P24_native` | P24 native structure and stated operations | Unreported states remain unknown |
| `02_P25_native` | P25 native three-phase structure and six modes | Never presented as a P24 result |
| `03_P24_primary_P25_supplement` | P24 four-phase structure; missing details explicitly supplemented from P25 | Four-phase extension is an assumption under test |

The analysis does not pre-impose 36/24/12 V as a zero-start result, alter a
paper rule to force closure, or treat a local ZVS event as a full-period proof.
`nP` and `nM` remain explicit, and single-module equations are not presented as
multi-module validation.

Raw optimizer traces are intentionally ignored by Git. The concise Markdown
reports, model source and acceptance tests are tracked and are sufficient to
audit or regenerate the reported calculations.
