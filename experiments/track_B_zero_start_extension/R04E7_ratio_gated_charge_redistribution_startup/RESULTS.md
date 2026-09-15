# R04E7 result - voltage-ratio-gated EPE2019 charge-redistribution ladder bootstrap

## Outcome, stated first

All 3 cells (`TOL` in `{2%, 5%, 10%}`, `TCAP_TOTAL=50 us` fixed) completed
normally and converged. **Replacing R04E6's blind fixed-hold-time gating
with voltage-ratio gating fixes the problem R04E6 diagnosed: `LADDER_ERR`
now decreases monotonically on every single cycle, at every tested
tolerance, all the way to convergence.** This is the opposite of R04E6's
own finding, where every cycle beyond the first made the ladder *worse*.
None of the three cells hit the `50 us` safety cap; all reached the `DONE`
state well before it (`t=3.90-4.24 us`, i.e. under `4.3 us` out of the
`50 us` budget -- roughly a `12x` margin). Grade: `LOCAL_PASS` for all
3/3 cells (see Section 6 for exactly what "pass" means and does not mean
here).

## Charge-conservation check (BOUNDARY.md Section 3)

Confirmed by direct algebraic derivation before any netlist was built:
with equal flying capacitors and `Vin=48 V`, a single (a)-(b)-(c) pass
cannot reach `36/24/12 V` because it would require state (a) to charge
`C1` to `60 V`, which exceeds `Vin`. This predicted that convergence would
require multiple cycles even in the corrected design -- confirmed
directly: the fastest-converging cell (`TOL=10%`) still took 5 full
cycles, none converged in 1.

## Per-tolerance results

| `TOL` | Cycles to converge | Final `VC1` | Final `VC2` | Final `VC3` | Final `LADDER_ERR` | Converged? | Convergence time |
|---|---:|---:|---:|---:|---:|---|---:|
| 2% | 8 | 35.597 V | 23.597 V | 11.798 V | 0.0448 | YES (`DONE`) | 4.2395 us |
| 5% | 6 | 34.880 V | 22.880 V | 11.440 V | 0.1244 | YES (`DONE`) | 4.0708 us |
| 10% | 5 | 34.134 V | 22.134 V | 11.067 V | 0.2074 | YES (`DONE`) | 3.9003 us |

`LADDER_ERR = |VC1-36|/36 + |VC2-24|/24 + |VC3-12|/12` (0 = perfect; the
same metric R02B and R04E6 already use). None of the three cells hit
`SAFETY_CAP_HIT_NOT_CONVERGED` -- there is no cap-without-convergence
result to report honestly avoid hiding in this grid; had one occurred it
would be listed here as such.

**Direction, stated explicitly and unambiguously**: a *tighter* tolerance
requires *more* cycles (`10%`->5 cycles, `5%`->6 cycles, `2%`->8 cycles)
and takes slightly *longer* wall-clock-in-the-simulation time to reach
(`3.90 us` -> `4.07 us` -> `4.24 us`), and produces a *smaller* (better)
final `LADDER_ERR`, because it keeps cycling until the ladder is closer to
target before declaring success. This is the expected, sensible direction
for a tolerance-gated stopping rule and is not a surprising result -- it
confirms the convergence-check logic is wired correctly (a looser band is
satisfied earlier, by construction).

## Cycle-by-cycle convergence trend (2% cell, the longest-running; earlier cycles are shared with the 5%/10% cells' own logs to within simulator precision, since `TOL` only affects the stopping decision, not the per-cycle redistribution dynamics)

| Cycle | `VC1` | `VC2` | `VC3` | `LADDER_ERR` | Change from previous cycle |
|---:|---:|---:|---:|---:|---|
| 1 | 21.603 V | 9.600 V | 4.800 V | 1.600 | (start) |
| 2 | 27.361 V | 15.360 V | 7.680 V | 0.960 | -0.640, improving |
| 3 | 30.815 V | 18.816 V | 9.408 V | 0.576 | -0.384, improving |
| 4 | 32.890 V | 20.890 V | 10.445 V | 0.346 | -0.230, improving |
| 5 | 34.134 V | 22.134 V | 11.067 V | 0.207 | -0.139, improving (10% band satisfied here) |
| 6 | 34.880 V | 22.880 V | 11.440 V | 0.124 | -0.083, improving (5% band satisfied here) |
| 7 | 35.328 V | 23.328 V | 11.664 V | 0.075 | -0.049, improving |
| 8 | 35.597 V | 23.597 V | 11.798 V | 0.045 | -0.030, improving (2% band satisfied here) |

**`LADDER_ERR` decreases on every single cycle, with no exception, at a
roughly geometric rate (each cycle's improvement is about `60%` of the
previous cycle's).** This is the direct opposite of R04E6's own table,
where `LADDER_ERR` *increased* on every cycle beyond the first at every
hold time `>=1 us`. The mechanism change (ratio gating instead of blind
timing) is the only difference between the two experiments' controllers,
so this reversal is attributed to that change, exactly as intended by the
task's diagnosis.

## Why this works -- a causal account, not just a correlation

R04E6/RESULTS.md diagnosed the root cause of its own failure: states (b)
and (c) are unbiased pairwise-equalizing loops -- left to run to
completion (or for a long-enough fixed hold time), they drive the two
capacitors they touch toward a common voltage, not toward the required
`3:2:1` split. R04E7's states (b) and (c) never run to equalization: they
stop the instant the *measured* voltage ratio crosses the target ratio
(`3/2` for b, `2/1` for c), which is a different physical endpoint than
"the two capacitors are equal." Because the exit condition is a ratio, not
an absolute value, it is self-correcting regardless of what state (a) or
the previous cycle left behind -- exactly the "self-correcting regardless
of `C1`'s actual present voltage" property the task specified as the
target mechanism. The cycle-by-cycle table above shows this working as
designed: every cycle recharges `C1` toward `36 V` and redistributes a
ratio-correct slice down the chain, so the whole ladder walks toward
target monotonically instead of drifting toward equalization.

## Peak currents (t>1 ns; same qualitative-flag convention as R04E6, no numeric pass/fail threshold -- BOUNDARY.md Section 4 item 5)

| Quantity | Value (consistent across all 3 `TOL` cells to within the final cycle's small difference) |
|---|---:|
| `IL1` max / min | 2201.9 A / -413.9 A |
| `ICS1` max / min | 4566.9 A / -2032.5 A |
| `ICS2` max / min | 3330.5 A / -835 to -852 A (varies slightly by final cycle) |
| `ICS3` max / min | 1016.1 A / -71.3 A |

These are large relative to P24's `125 A` per-phase boundary-mode
reference, tens of amps to several kilo-amps flowing capacitor-to-capacitor
through only switch `Ron` (a few `mOhm`) -- the same qualitative
observation R04E6 already made about this mechanism family (zero added
impedance, zero dead time). The values are nearly identical across the
three `TOL` cells because the first several cycles' dynamics are shared;
only the very last cycle (which differs by `TOL`) contributes any small
variation, visible only in `ICS2_MIN`. No numeric threshold is applied
(the source gives none); this is a plain finding, not a graded failure.

## Comparison against R04E6 and R02B

| Experiment | Mechanism | Best `LADDER_ERR` |
|---|---|---|
| R02B (tuned passive divider) | passive divider, swept `CDIV`/`TRAMP` | 0.260 |
| R04E6 (blind timer, best single cell) | EPE2019 3-state sequence, fixed `TH`, `NCYC=1` | 0.836 |
| R04E7 `TOL=10%` (this experiment) | EPE2019 3-state sequence, voltage-ratio gated | **0.207** |
| R04E7 `TOL=5%` (this experiment) | EPE2019 3-state sequence, voltage-ratio gated | **0.124** |
| R04E7 `TOL=2%` (this experiment) | EPE2019 3-state sequence, voltage-ratio gated | **0.045** |

**All three R04E7 cells beat R02B's own best result (0.260), and all three
beat R04E6's own best single-cell result (0.836) by a wide margin.** The
loosest tested tolerance (`10%`) already outperforms R02B; the tightest
(`2%`) reaches an aggregate ladder error of under `5%`, the closest any
Track-B zero-start bootstrap experiment in this project has come to the
`36/24/12 V` target so far. Stated plainly: **the voltage-ratio-gated fix
works, in the sense the task set out to test** -- it reaches the target
ladder (within a chosen, honestly-labelled tolerance) where R04E6's blind
timer could not, and does so through *repeated, self-correcting* cycles
rather than a single lucky pass, exactly matching the charge-conservation
prediction that multiple cycles would be required.

## Chatter check result (BOUNDARY.md Section 8)

No comparator chatter was observed in any of the three cells: each
`.meas` sequence is clean and monotonic, each run completed in
`117-135` real seconds without a runaway/hung solve, and the final state
is a clean, unambiguous `DONE` in all three. No hysteresis band or
state-memory workaround was needed for this grid (reasoning for why this
family of comparator is structurally less chatter-prone than R03B's
current-based one is in BOUNDARY.md Section 8).

## What this resolves and what it does not

Resolves: confirms that gating EPE2019's Fig. 5 mechanism by measured
voltage ratios, instead of a blind fixed timer, reverses R04E6's
diagnosed failure mode (drift toward equalization) into monotonic,
repeated, self-correcting convergence toward `36/24/12 V`; establishes
that convergence is reachable (at 3 tested tolerances) well inside a
generous safety cap, with no safety-cap-without-convergence result in
this grid; and outperforms both prior zero-start bootstrap results in this
project (R02B and R04E6) at every tested tolerance.

Does not resolve (same scope limits as R04E6, restated per BOUNDARY.md
Section 11): any `Vout`/P24 steady-state handoff; hardware switch-stress
validation of the multi-kilo-amp capacitor-to-capacitor currents;
four-phase interleaving (phase 4 is never driven); whether this specific
`TOL`/`TCAP_TOTAL` choice is "correct" rather than a sensitivity choice;
or general chatter-immunity outside this experiment's own tested grid.

## Next permitted action

The next reasonable step for this specific mechanism is a handoff study:
whether the converged ladder state (e.g. the `TOL=2%` cell's `35.60/23.60/
11.80 V`) can serve as a usable initial condition for the existing,
already-validated event-gated P24 steady-state controller (R04E3/R04E5
lineage), matching the task framing's own suggested next step ("an
explicit handoff into the existing, already-validated strict event-gated
controller only once `Vout`/the capacitor ladder is already close to
target," per `experiments/track_B_zero_start_extension/README.md`'s R04E5
lesson). That handoff is out of scope for this experiment and is not
attempted here.
