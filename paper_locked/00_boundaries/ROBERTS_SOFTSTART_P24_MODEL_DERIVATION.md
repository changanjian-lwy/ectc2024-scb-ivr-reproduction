# Roberts dissertation Section 3.5 soft-start mechanism: P24-specific
   model derivation (2026-09-16) -- derivation only, no SPICE built yet

## Why this exists and its scope

Per explicit user direction 2026-09-16 ("你先建立模型 不着急跑先" -- build
the model first, no rush to run it), this document derives P24-specific
numbers from Roberts' PhD dissertation Chapter 3 (`ROBERTS_PRODIC_2024_
LITERATURE_REVIEW.md`'s "Follow-up" section already summarizes the
mechanism itself) so that a future experiment has a defensible starting
point instead of guessing a ramp time. **No `.cir` file is built or run
in this document.** It is a pure analytical derivation, the same kind of
artifact `CFLY_FIRST_PRINCIPLES_ESTIMATE.md` was for the flying-capacitor
value.

## Method validation (done before trusting the P24 application)

Before applying Roberts' own resonance formula to P24, it was checked
against his own worked numeric example (dissertation Fig. 3.12, a
2-inductor, `Vin=5 V`/`Vout~0.8 V`/`L=120 nH`/`C1=10 uF` SCB, stated FC
resonance `~65.7 kHz`). His Eq. 3.44 general form is
`ωk,N = (2D/√(L·Cfly))·sin(kπ/2N)`, and for `N=2` there is only one such
frequency, `ω1,2 = D√2/√(L·Cfly)` (his own stated special case). Using
the conventional SCB duty ratio `D = N·Vout/Vin` (`=2×0.8/5=0.32` for his
example), direct computation gives `f1,2 = 65.75 kHz` -- matching his
own stated `65.7 kHz` to the printed precision. **This confirms the
formula and the `D=N·Vout/Vin` convention are being applied correctly**
before use on P24's own numbers below.

## P24's own inputs (all already `LOCKED`, not re-derived here)

From `SOURCE_COVERAGE_MATRIX.md`/`CFLY_FIRST_PRINCIPLES_ESTIMATE.md`,
already-established values: `Vin=48 V`, `Vout=1 V`, `nP=N=4`,
`fsw=5 MHz` (`T=200 ns`), `Ton=16.667 ns`, giving
`D = Ton/T = 16.667/200 = 0.083335` (equivalently `D=N·Vout/Vin
=4×1/48=0.08333`, the same two conventions agreeing, as they must).
`L = Lphase = 1.4666667 nH` (Eq.-4 branch, the same value R04E3-R04E15's
entire active-netlist lineage already uses). `Cfly` is NOT a single
locked value -- it remains the `0.6-8.7 uF` first-principles
`SENSITIVITY_ONLY` range (`CFLY_FIRST_PRINCIPLES_ESTIMATE.md`), so every
result below is computed across that whole range, not at one arbitrarily
chosen point.

## Step 1: `N=4` flying-capacitor resonant frequencies (Eq. 3.44 applied
   to P24)

`ωk,4 = (2D/√(L·Cfly))·sin(kπ/8)`, `k∈{1,2,3}` (three resonances for a
4-inductor SCB, per Roberts' own `N-1` count), equivalently the N=4
closed forms he gives directly: `ω1,4=D√(2-√2)/√(LCfly)`,
`ω2,4=D√2/√(LCfly)`, `ω3,4=D√(2+√2)/√(LCfly)`.

| `Cfly` | `f1,4` (kHz) | `f2,4` (kHz) | `f3,4` (kHz) |
|---:|---:|---:|---:|
| `0.6 uF` | 342.20 | 632.30 | 826.14 |
| `1.45 uF` | 220.12 | 406.74 | 531.43 |
| `2.89 uF` | 155.92 | 288.10 | 376.42 |
| `3.0 uF` (project's standard middle value) | 153.04 | 282.77 | 369.46 |
| `4.34 uF` | 127.24 | 235.10 | 307.17 |
| `8.68/8.7 uF` | 89.97/89.87 | 166.24/166.05 | 217.20/216.95 |

`f1,4` (the LOWEST of the three) is the binding constraint for any
Vin-ramp bandwidth target, since a ramp slow enough to stay below the
lowest resonance is automatically slow enough for the other two as well.
As expected from `ωk,N∝1/√Cfly`, every frequency falls as `Cfly` rises
(a `14.5x` `Cfly` span produces a `3.8x` frequency span on `f1,4`).

## Step 2: candidate ramp-time target (Roberts' own bandwidth-margin
   method, Appendix B's `Δt0.8≈0.35/BW` relation)

Following Roberts' own worked-example method exactly (compute the
10%-90% rise time whose bandwidth equals the binding resonance, then
apply his own `30x` safety margin): `Δt(BW=f1,4) = 0.35/f1,4`, final
recommended rise time `= 30 × Δt(BW=f1,4)`.

| `Cfly` | `Δt(BW=f1,4)` (us) | `30x`-margin ramp time (us) |
|---:|---:|---:|
| `0.6 uF` | 1.023 | 30.68 |
| `1.45 uF` | 1.590 | 47.70 |
| `2.89 uF` | 2.245 | 67.34 |
| `3.0 uF` | 2.287 | 68.61 |
| `4.34 uF` | 2.751 | 82.52 |
| `8.68/8.7 uF` | 3.890/3.895 | 116.71/116.84 |

**At the project's standing `Cfly=3 uF` candidate, P24's own operating
point implies a Vin ramp time on the order of `~69 us`** (compare
Roberts' own 2-inductor/5 V example, which needed `160 us` of margin time
on top of a `5.3 us` bandwidth-matching rise time -- P24's much smaller
per-phase inductance and larger phase count push the resonances higher,
requiring a proportionally shorter ramp for the same margin convention).
Across the full first-principles `Cfly` range, the implied ramp time
spans roughly **`31-117 us`**, monotonically increasing with `Cfly` (a
larger flying capacitor resonates at a lower frequency, so a slower ramp
is needed to stay safely below it).

## What this derivation does and does not establish

**Establishes**: a first-principles, P24-specific candidate ramp-time
range (`~31-117 us` depending on the still-unconfirmed `Cfly`), derived
entirely from Roberts' own published `N`-inductor resonance formula and
his own stated `30x` margin convention, applied to P24's own `LOCKED`
operating-point values -- not an arbitrary guess, and not a re-use of his
own 2-inductor/5 V numbers.

**Does not establish**:
- That `30x` is the "correct" margin -- it is Roberts' own chosen
  convention for his own worked example, reused here for lack of any
  other stated criterion; his own text only says the margin should be
  "significantly below" the resonance and offers `30x` as what he
  himself judged sufficient for his example, not a derived optimum. A
  future experiment could sensitivity-sweep this margin (e.g. `10x`,
  `30x`, `100x`) the same way this project treats every other
  engineering-choice axis (`SENSITIVITY_ONLY`).
- Which single `Cfly` value to use -- the whole `31-117 us` range is
  carried forward, exactly as `CFLY_FIRST_PRINCIPLES_ESTIMATE.md` itself
  is not a single value.
- Whether gating should start at `t=0` (Vin and switching ramp up
  together from the start, matching Roberts' own plotted Fig. 3.12
  example -- his text confirms this is what his own figure shows,
  contrasting it with "another realistic scenario" of delayed gating as
  an alternative he mentions but does not himself simulate) or only once
  Vin reaches some threshold fraction of `48 V`. This project has not yet
  chosen between these two; Roberts' own demonstrated case is
  gate-from-the-start, so that is the more directly literature-grounded
  default, but this is a design choice a future experiment's own
  `BOUNDARY.md` must state explicitly, not assume silently.
- Any peak-current, `LADDER_ERR`, or `Vout`-bootstrap number -- this
  document contains no SPICE result. It only derives the ramp-time INPUT
  a future experiment would need to construct its `Vin` source waveform;
  R04E9-R04E15's own active four-phase netlist family (or a new one)
  would still need to be built and actually run to know whether this
  ramp rate, applied to P24's real four-phase switching netlist, actually
  produces a working ladder/Vout bootstrap.
- Whether this mechanism, once built, out-performs R04E14/R04E15's own
  passive-divider result or R04E9-R04E13's admission-order family -- no
  comparison is possible without a built and run model.

## Provenance and classification

| Item | Source | Category |
|---|---|---|
| Eq. 3.44 resonance formula, `30x` margin convention, `Δt≈0.35/BW` relation | Roberts' PhD dissertation, Chapter 3 (verbatim method, validated against his own worked example above) | `CROSS_PAPER_EXTENSION` (author's own general SCB theory) |
| `D=0.083335`, `L=1.4666667 nH` | P24's own `LOCKED` operating point (`SOURCE_COVERAGE_MATRIX.md`) | `P24_EXPLICIT` |
| `Cfly` range `0.6-8.7 uF` | `CFLY_FIRST_PRINCIPLES_ESTIMATE.md` | `SENSITIVITY_ONLY`, inherited |
| The resulting `f1,4`/ramp-time numbers in this document | New: Roberts' formula applied to P24's own values, neither he nor P24/P25 worked this out numerically | `CROSS_PAPER_EXTENSION` (method borrowed, operating point is P24's own) |
| Gate-from-`t=0` vs. delayed-threshold-gating choice | Undecided; Roberts' own plotted example uses gate-from-start | Open design choice for a future experiment's own `BOUNDARY.md`, not decided here |
| `30x` margin itself | Roberts' own chosen value for his own example, not independently justified by him or re-derived here | `SENSITIVITY_ONLY` candidate for a future sweep |

No P24/P25 numeric value is altered by this document. This is a
preparatory derivation only; the next step (building and running an
actual SPICE model using this ramp-time range) has not been started.
