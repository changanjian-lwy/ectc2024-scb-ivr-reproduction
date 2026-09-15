# R04E8 result - corrected-Cfly voltage-ratio-gated EPE2019 charge-redistribution ladder bootstrap

## Outcome, stated first

All 3 cells (`Cfly` in `{1 uF, 3 uF, 8.7 uF}`, `TOL=2%` fixed,
`TCAP_TOTAL=10 us` fixed) completed normally and converged to `DONE`.
**The voltage-ratio-gating mechanism validated in R04E7 at `Cfly=53.8 uF`
remains robust when `Cfly` is corrected down to the physically-appropriate
`0.6-8.7 uF` range** -- all three tested points reach the same `DONE` state,
in the same 8 cycles, with essentially the same final `LADDER_ERR`
(`0.044-0.045`) as R04E7's own `TOL=2%` result (`0.045`). None of the three
cells hit the `10 us` safety cap. Grade: `LOCAL_PASS` for all 3/3 cells
(same grading convention and scope limits as R04E7 -- see `BOUNDARY.md`
Section 9 for what this does not prove).

## Per-`Cfly` results

| `Cfly` | Cycles to converge | Final `VC1` | Final `VC2` | Final `VC3` | Final `LADDER_ERR` | Converged? | Convergence time |
|---|---:|---:|---:|---:|---:|---|---:|
| 1 uF | 8 | 35.601 V | 23.601 V | 11.802 V | 0.0442 | YES (`DONE`) | 85.60 ns |
| 3 uF | 8 | 35.598 V | 23.598 V | 11.800 V | 0.0446 | YES (`DONE`) | 256.72 ns |
| 8.7 uF | 8 | 35.597 V | 23.597 V | 11.799 V | 0.0447 | YES (`DONE`) | 741.62 ns |
| **R04E7 (53.8 uF, `TOL=2%`, for comparison)** | **8** | **35.597 V** | **23.597 V** | **11.798 V** | **0.0448** | **YES (`DONE`)** | **4239.5 ns** |

`LADDER_ERR = |VC1-36|/36 + |VC2-24|/24 + |VC3-12|/12` (0 = perfect), the
same metric R02B/R04E6/R04E7 use. None of the three cells hit
`SAFETY_CAP_HIT_NOT_CONVERGED`.

**Cycle count and final voltages are essentially identical across all four
`Cfly` values (1, 3, 8.7 and 53.8 uF)** -- all converge in exactly 8 cycles,
with `LADDER_ERR` landing in a tight `0.0442-0.0448` band. This is expected
from the mechanism's own design (R04E7/BOUNDARY.md Section 2): the
comparators are voltage **ratios** (`V(C1)/V(C2)>=3/2`,
`V(C2)/V(C3)>=2/1`) and absolute-voltage thresholds (`V(C1)>=36V`, and the
`+/-2%` band around `36/24/12 V`), none of which depend on the capacitance
value itself -- only on the charge/voltage relationship, which is
scale-invariant when every capacitor in the ladder is scaled by the same
factor. The per-cycle voltage trajectory (below) confirms this directly:
the `VC1`/`VC2`/`VC3` values at each cycle boundary agree with R04E7's own
table to 3-4 significant figures at every `Cfly`, differing only in **when**
(simulated time) each cycle boundary occurs.

## Cycle-by-cycle voltage trajectory (all three `Cfly` values shown; times only, since the voltages are effectively identical -- see discussion above)

| Cycle | `VC1` (all `Cfly`, ~V) | `t` at 1 uF | `t` at 3 uF | `t` at 8.7 uF |
|---:|---:|---:|---:|---:|
| 1 | 21.59 | 33.53 ns | 100.56 ns | 289.78 ns |
| 2 | 27.36 | 53.17 ns | 159.43 ns | 459.89 ns |
| 3 | 30.82 | 65.94 ns | 197.75 ns | 570.59 ns |
| 4 | 32.89 | 74.13 ns | 222.28 ns | 641.70 ns |
| 5 | 34.13 | 79.28 ns | 237.72 ns | 686.48 ns |
| 6 | 34.88 | 82.46 ns | 247.29 ns | 714.24 ns |
| 7 | 35.33 | 84.42 ns | 253.16 ns | 731.27 ns |
| 8 (final) | 35.60/35.60/35.60 | 85.60 ns | 256.72 ns | 741.62 ns |

(R04E7's own `RESULTS.md` table reports the same cycle-1-through-8 `VC1`
values, e.g. `21.603 V` at cycle 1 -- matching this table's `21.59 V` to 3
significant figures -- but only tabulates the final convergence time,
`t=4239.5 ns`, not a full per-cycle timestamp series; that final value is
the one used in the comparison table below, not a fabricated per-cycle
figure.)

## How convergence speed scales with `Cfly` -- stated explicitly and checked directly, not assumed

**Convergence time grows almost exactly in proportion to `Cfly`, with a
small, very consistent super-linear correction factor.** A pure
linear-in-`Cfly` (RC-scaling) prediction, anchored at R04E7's own
`53.8 uF -> 4239.5 ns` point, gives:

| `Cfly` | Naive linear prediction (`4239.5 ns * Cfly/53.8uF`) | Actual measured | Actual / naive |
|---|---:|---:|---:|
| 1 uF | 78.80 ns | 85.60 ns | 1.086x |
| 3 uF | 236.44 ns | 256.72 ns | 1.086x |
| 8.7 uF | 685.74 ns | 741.62 ns | 1.082x |

The actual/naive ratio is `1.082-1.086` across a nearly `9x` range of
`Cfly` -- essentially constant. **Plain-word statement**: convergence time
scales very close to linearly with `Cfly` (matching the simple `RC`
charging-time intuition stated as the expectation before running anything),
with a small, consistent ~8% "slower than pure-linear" correction whose
origin is not investigated further here (plausibly the compounding effect
of 8 discrete cycles each carrying a small nonlinear residual, or the fixed
device capacitances `CH`/`CL`, which do not scale with `Cfly` and become
relatively less negligible at the smallest `Cfly` values -- not confirmed,
flagged as an open detail, not a claim).

**This confirms the task's first physical expectation directly**:
convergence at the corrected, smaller `Cfly` values is dramatically faster
in simulated time than R04E7's `53.8 uF` case -- by `49.5x` at `1 uF`,
`16.5x` at `3 uF`, and `5.7x` at `8.7 uF`.

## How peak current scales with `Cfly` -- stated explicitly and checked directly, not assumed

**The task's second physical expectation (peak inrush current set by
`V/Ron`, roughly independent of `C`) is confirmed for the flying
capacitors' own MAXIMUM currents, but not uniformly for every current in
the circuit.** Two different behaviors were found, both reported plainly:

| Quantity | 1 uF | 3 uF | 8.7 uF | R04E7 (53.8 uF, `TOL=2%`) | Behavior across the ~54x `Cfly` range |
|---|---:|---:|---:|---:|---|
| `ICS1_MAX` | 4157.7 A | 4431.5 A | 4525.0 A | 4566.9 A | **Roughly flat** (4158-4567 A, <10% spread) |
| `ICS1_MIN` | -3359.9 A | -3307.9 A | -3177.7 A | -2032.5 A | Mildly **less negative** as `Cfly` grows; flat within this grid (-3360 to -3178 A), a larger step to R04E7's -2032.5 A |
| `ICS2_MAX` | 3790.9 A | 3755.7 A | 3668.8 A | 3330.5 A | **Roughly flat**, mild downward drift with larger `Cfly` |
| `ICS2_MIN` | -1020.4 A | -1004.2 A | -964.5 A | -835 to -852 A | Mildly **less negative** as `Cfly` grows |
| `ICS3_MAX` | 1145.4 A | 1128.6 A | 1095.1 A | 1016.1 A | **Roughly flat**, mild downward drift with larger `Cfly` |
| `ICS3_MIN` | -2.6 A | -7.6 A | -20.5 A | -71.3 A | **Does scale up with `Cfly`** -- grows monotonically and substantially (~27x from 1 uF to 53.8 uF, sub-linear relative to `Cfly`'s own ~54x range but a real, consistent trend, unlike the MAX currents |
| `IL1_MAX` | 84.1 A | 242.4 A | 633.1 A | 2201.9 A | **Scales up strongly and monotonically with `Cfly`**, roughly proportional (a different current path -- see below) |
| `IL1_MIN` | -57.1 A | -125.2 A | -237.9 A | -413.9 A | **Scales up with `Cfly`**, sub-linearly but clearly |

**Plain-word summary**: the direct flying-capacitor-to-flying-capacitor
redistribution currents' **peak (maximum) magnitudes**
(`ICS1_MAX`/`ICS2_MAX`/`ICS3_MAX`) stay in essentially the same
multi-kilo-amp range regardless of whether `Cfly` is `1 uF` or `53.8 uF` --
**peak current does NOT shrink with smaller `Cfly`**, confirming the
`V/Ron`-dominated hypothesis for this project's zero-dead-time,
`Ron`-only idealized switch model. However, this is not universal: some of
the **minimum (reverse-direction) currents**, most clearly `ICS3_MIN`, and
the **inductor-branch current** `IL1` (a different physical path -- `L1`
connects the switching node `x1` to the output rail `out`, not
capacitor-to-capacitor, and was not the subject of the task's stated
prediction) both grow substantially with `Cfly`. `IL1` in particular is not
governed by the same `V/Ron` charging-step argument as the flying
capacitors; it is far more plausible that this reverse/inductor current
scales with the amount of charge the ladder redistributes per cycle, which
does grow with `Cfly` even though the per-cycle voltage swings do not
(more coulombs move for the same volt change on a bigger capacitor). This
distinction -- some currents flat, some scaling -- was checked directly
against the data rather than assumed in either direction, per the task's
instruction.

**Nothing here is graded pass/fail against a numeric current threshold**
(same convention as R04E6/R04E7 -- no such threshold exists in any source,
`BOUNDARY.md` Section 4 item 5 as inherited from R04E7). The multi-kilo-amp
`ICS1`/`ICS2` currents remain, as R04E7 already flagged, physically
implausible for a real switch/capacitor path with only a few `mOhm` of
`Ron` and zero dead time -- this experiment's finding that they do **not**
shrink with a more realistic `Cfly` means the earlier, oversized `Cfly`
value was **not** the cause of that implausibility; it is a structural
consequence of the idealized (zero-dead-time, `Ron`-only) switch model
itself, independent of the `Cfly` correction this experiment makes.

## Pilot check (`BOUNDARY.md` Section 6) -- confirmed against the committed grid

The untracked pilot run (`Cfly=3 uF`, `TCAP_TOTAL=2 us`,
`TMAX=55.76 ps`) predicted `t=256.7 ns`, `LADDER_ERR=0.045`,
`ICS1_MAX=4431.5 A`. The committed `3 uF` cell (`TCAP_TOTAL=10 us`,
`TMAX=50 ps`) reproduces this to within simulator/rounding precision
(`t=256.72 ns`, `LADDER_ERR=0.0446`, `ICS1_MAX=4431.5 A`), confirming the
pilot's own resolution settings and safety-cap choice (Section 6 of
`BOUNDARY.md`) were sound before committing the full 3-cell grid.

## Comparison against R04E7 and the wider Track-B family

| Experiment | `Cfly` | Mechanism | Cycles | Convergence time | Final `LADDER_ERR` |
|---|---:|---|---:|---:|---:|
| R04E7 (`TOL=2%`) | 53.8 uF (EPE2019 Table I, cross-topology) | ratio-gated EPE2019 3-state | 8 | 4239.5 ns | 0.0448 |
| R04E8 (this experiment) | 8.7 uF (corrected, high end) | same, unchanged | 8 | 741.6 ns | 0.0447 |
| R04E8 (this experiment) | 3 uF (corrected, mid) | same, unchanged | 8 | 256.7 ns | 0.0446 |
| R04E8 (this experiment) | 1 uF (corrected, low end) | same, unchanged | 8 | 85.6 ns | 0.0442 |

**All three R04E8 cells match R04E7's own best-tested result
(`LADDER_ERR=0.045`) essentially exactly** (the small `0.0442-0.0448` spread
is well within what would be expected from `Cfly`-independent, purely
ratio-driven convergence), while converging `5.7x` to `49.5x` faster in
simulated time. None of R04E8's cells does worse than R04E7's own
`TOL=2%` result on the ladder-error metric.

## Top-level verdict

**The ratio-gating mechanism validated in R04E7 remains robust at the
corrected, physically-appropriate `Cfly` scale (`1-8.7 uF`)**, stated
honestly with the following caveats:

1. This is a **module swap inside an unchanged framework**, not a
   re-derivation -- the truth table, the ratio-gating logic, and the power
   stage were all reused unchanged (`BOUNDARY.md` Section 1); only `Cfly`
   and two solver-resolution settings changed.
2. Convergence quality (final `LADDER_ERR`, cycle count) is essentially
   identical across the entire tested `1-53.8 uF` range -- the mechanism's
   voltage-ratio design makes it structurally insensitive to the absolute
   capacitance value, exactly as the ratio-based comparator logic would
   predict.
3. Convergence speed scales close to linearly with `Cfly` (a small, tight
   `~8%` super-linear correction, Section "How convergence speed scales"
   above) -- the corrected, smaller `Cfly` makes the bootstrap dramatically
   faster in simulated time, not slower or unchanged.
4. Peak capacitor-to-capacitor current does **not** shrink with the
   smaller, corrected `Cfly` -- it stays in the same multi-kilo-amp range
   found (and already flagged as physically implausible for the idealized
   switch model) in R04E6/R04E7. **The `Cfly` correction does not resolve
   the peak-current-plausibility concern**; that concern is attributable to
   the zero-dead-time, `Ron`-only switch idealization, not to the specific
   (now-corrected) `Cfly` value.
5. This does **not** establish which specific value inside `0.6-8.7 uF` (or
   outside it) is hardware-correct -- see `BOUNDARY.md` Section 9 for the
   full list of what this experiment cannot prove (no `Cout` correction, no
   `Vout`/steady-state handoff, no hardware switch-stress validation, no
   four-phase claim).

## Next permitted action

The same next step R04E7 identified remains open and is now additionally
supported at the corrected capacitance scale: whether a converged ladder
state from this family (e.g. this experiment's `1 uF` cell's
`35.60/23.60/11.80 V`, reached in under `100 ns` simulated time) can serve
as a usable initial condition for the existing, already-validated
event-gated P24 steady-state controller (R04E3/R04E5 lineage). A second,
separate, not-yet-attempted next step raised directly by this experiment's
own scope limit (`BOUNDARY.md` Section 4): a first-principles `Cout`
correction analogous to this experiment's `Cfly` correction, once a
load-transient specification becomes available to ground it (currently an
open gap per `CFLY_FIRST_PRINCIPLES_ESTIMATE.md`'s own "Cout is not
estimated here" section). Neither is attempted here.
