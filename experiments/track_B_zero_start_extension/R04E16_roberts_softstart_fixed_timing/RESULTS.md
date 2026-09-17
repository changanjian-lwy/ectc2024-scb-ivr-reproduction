# R04E16 result - Roberts' soft-start mechanism on fixed-timing 4-phase PWM

## Outcome, stated first

**All 6 of 6 grid cells now reached completion (grid COMPLETE). Every
cell avoids R03A's diagnosed catastrophic current runaway** (R03A's own
phase-current maxima were `563-884 A`; every completed R04E16 cell stays
under `151 A`, well inside the `+/-250 A` safety bound). **But the
control cell (near-instantaneous ramp, `Tramp=1 us`) ALSO avoids it**,
settling to essentially the SAME steady-state operating point as every
slow-ramp cell (`Vout~=0.558-0.564 V`, `LADDER_ERR~=1.33-1.40` across all
six cells, spanning `Tramp` from `1 us` to `228.71 us` and `Cfly` from
`0.6` to `8.7 uF`). This is exactly the failure mode BOUNDARY.md Section
10 itself flagged as a possible, separately-reportable outcome: **the
counterfactual this experiment's own design depends on did not hold** --
the near-instant-ramp control case does not reproduce runaway-like
behavior, so the absence of runaway in the slow-ramp cells cannot be
cleanly attributed to the `Vin` ramp mechanism itself. The most likely
alternative explanation, developed in Section 6 below: removing R02B's
passive-divider precharge network (this experiment's own explicit scope
choice, BOUNDARY.md Section 4) eliminates the specific mismatch R03A's
own diagnosis identified (a PRE-CHARGED capacitor ladder suddenly exposed
to full-strength PWM while `Vout` is still cold) -- and that mismatch,
not the ramp speed, is plausibly what R03A's runaway actually depended
on. **The two cells completed last (`Cfly=8.7 uF` at `30x` margin, and
`Cfly=3 uF` at `100x` margin) REINFORCE this picture rather than change
it** -- see Sections 5-7 for the full, now-complete quantitative detail,
including a genuine (if modest) `Cfly` sensitivity trend and a clean
4-point margin-factor sensitivity trend that were not previously
available.

**Grid completion status: 6 of 6 cells reached completion and are fully
verified below.** The first 4 (the control cell, both Grid-2/Grid-1
`Cfly=3 uF` cells at `10x` and `30x` margin, and the Grid-1
`Cfly=0.6 uF`/`30x`-margin cell) were reported complete in this
document's prior revision. The remaining 2 (`Cfly=8.7 uF` at `30x`
margin, real LTspice wall time `2165.2 s`, `~36.1` min; and `Cfly=3 uF`
at `100x` margin, real LTspice wall time `2525.2 s`, `~42.1` min) were
run to completion, one at a time, never concurrently, in a subsequent
session -- both verified to have a `.log` `Total elapsed time` line and
full `.meas` output, and independently checked for the solver-corruption
fingerprint documented in Section 3a (neither shows it; see Section 3b
for the updated runtime-variance picture, which these two data points
extend rather than upend). Section 3 documents the tooling findings that
explain why completion took multiple sessions; this document now reports
the complete, final 6-cell grid.

A second, independently important, load-bearing finding: **the netlist
as literally specified in BOUNDARY.md (R03A's own default LTspice
solver, `.options reltol=1e-5 abstol=1e-9 chgtol=1e-16`) is NOT
numerically tractable** -- every cell, run that way, hit a reproducible,
forensically-confirmed solver breakdown (Section 3) well before
completing, regardless of `Cfly`/`Tramp`. A solver-stabilization fix
already established as this project's own standing convention for
`TMAX=50 ps` on this class of circuit (`solver=alt cshunt=1e-15
plotwinsize=0`, used verbatim in every one of R04E5-R04E10's own build
scripts) was applied, is reported transparently here, and resolved the
corruption issue completely for every cell re-run with it (though it did
not resolve the separate runtime-variance issue above).

## 1. Pilot verification (BOUNDARY.md's required pilot-first step)

A minimal, power-stage-free netlist (`cases/e16_pilot_gates.cir`) with
only the 8 gate B-sources (`BH1..BH4`/`BL1..BL4`, copied unchanged from
R03A except `TSTART=0`) was run first, per BOUNDARY.md's own explicit
requirement to verify the `TSTART=0` gating in isolation before trusting
the full grid.

**Result: PASS.** Directly measured from the raw `.log` `.meas` output:

- `TON_MEAS = GH1_FALL1-GH1_RISE1 = 16.668 ns` (target `D*T = 1/12 *
  200 ns = 16.667 ns` -- matches).
- `T_MEAS = GH1_RISE2-GH1_RISE1 = 199.998 ns` (target `T=200 ns` --
  matches).
- `PHASE21_MEAS = PHASE32_MEAS = PHASE43_MEAS = 50.0 ns` (target
  `T/4=50 ns` for all three inter-phase spacings -- matches exactly).
- All four phases (`gh1..gh4`) toggle correctly from `t=0` in the
  intended non-overlapping, `T/4`-shifted pattern.

**One negligible artifact found and reported, not silently ignored**:
`V(gh1)` and `V(gl1)` both read `0` at the exact timepoint `t=0`
(neither high nor low side driven for an instant), and the first real
rising edge of `gh1` lands at `t=5.00e-17 s`, not exactly `t=0`. Root
cause, confirmed directly: `mod(time-TSTART+T,T)` evaluates
`mod(T,T)=T` (not `0`) at the exact floating-point value `time=0`, so
the `<TON` condition is momentarily false; the very next solver
timepoint (`~5e-17 s` later) resolves correctly. This is `7` orders of
magnitude smaller than the `TMAX=50 ps` resolution actually used in the
full grid and has zero measurable effect on any grid cell's results --
reported here per this project's own transparency convention, not
treated as a logic defect.

## 2. Cells built and their status

Per BOUNDARY.md Section 6, 6 cells total, `TSTOP = TRAMP + 300 us` each:

| Grid | Case | `Cfly` | `Tramp` | Margin | `TSTOP` | Status |
|---|---|---:|---:|---|---:|---|
| control | `e16_ctrl_f3_t1` | 3 uF | 1 us | n/a | 301 us | **COMPLETE** |
| 2 | `e16_g2_f3_t22p87` | 3 uF | 22.87 us | 10x | 322.87 us | **COMPLETE** |
| 1 | `e16_g1_f3_t68p61` | 3 uF | 68.61 us | 30x | 368.61 us | **COMPLETE** |
| 1 | `e16_g1_f0p6_t30p68` | 0.6 uF | 30.68 us | 30x | 330.68 us | **COMPLETE** (finished unattended overnight, `11842.4 s` wall time, added in a same-day follow-up commit) |
| 1 | `e16_g1_f8p7_t116p84`| 8.7 uF | 116.84 us| 30x | 416.84 us | **COMPLETE** (`2165.2 s` wall time) |
| 2 | `e16_g2_f3_t228p71`  | 3 uF | 228.71 us| 100x| 528.71 us | **COMPLETE** (`2525.2 s` wall time) |

Fixed for every cell, unchanged from R03A per BOUNDARY.md Section 5:
four-phase power-stage connectivity (`SH1-4`/`CF1-3`/`SL1-4`/`L1-4`,
`out` node), gate-generation B-source formulas (`D=1/12`, `TON=D*T`,
fixed `T/4`-shifted, complementary, no dead time), `COUT=4.672 mF`,
`RLOAD=Vout^2/Pout`, ideal `SWI` switch (`Ron=1u`/`Roff=1T`/`Vt=2.5`/
`Vh=0`), `RLDAMP=1u`, true-zero-energy IC (`UIC`, no `IC=`), `TMAX=50 ps`,
IPEC2018 `LPAR=5n`/`RPAR=10m` source parasitics. Changed per BOUNDARY.md
Section 4: `TSTART=0`, `LPHASE=1.4666667 nH` (was R03A's `2.68 nH`),
`CFLY` swept (was R03A's fixed `53.8 uF`), R02B's passive-divider
precharge network (`CIN1-4`/`RLEAK1-4`/`DPC1-3`/`CDIV`/`DPRE`) removed
entirely.

## 3. Two tooling findings, both reported transparently rather than worked around silently

### 3a. Solver breakdown at R03A's own default options, and the fix applied

**Before any grid cell was accepted, every cell was first attempted with
R03A's own literal `.options` line (`reltol=1e-5 abstol=1e-9
chgtol=1e-16`, the default "Normal" solver) -- and every one of the 6
failed.** This is reported in full because it directly bears on how much
trust to place in "large current" readings anywhere in this family of
circuits, per the task's own explicit instruction to check for and flag
the project's documented solver-retry/chatter fingerprint before
reporting any implausible number as physical.

**Forensic evidence (two cells fully analyzed by direct binary
inspection of the `.raw` trace, byte-for-byte):**

- `e16_g2_f3_t22p87` (10x margin): clean, physically plausible state up
  to `t=3.599999999978676e-06 s` (`Vout=0.00987 V`, `Vin=7.5557 V`
  matching the commanded ramp exactly, `IL1=20.40 A`) is followed by SIX
  near-duplicate-timestamp records (`3.599999999381913e-06` through
  `3.5999999999997716e-06`, all agreeing on every value -- classic
  solver-retry chatter, the same fingerprint this project documented for
  R04E10/R04E11's unrelated `.machine`-based construct), then the very
  next record shows **the independent PWL source `V(vin)` itself
  reading `-20885.65625 V`**, then `5.33e24 V`, then settling into an
  absurd `~-2.05e17 V` chatter plateau -- `I(L1)` similarly jumps to
  `2.76e21 A` then plateaus near `6.4e7 A`. Since `V(vin)` is an ideal,
  exactly-PWL-prescribed source with **no dependence on any circuit
  state**, it cannot legitimately read anything but its commanded value
  (`7.5557 V` at this instant) -- this is unambiguous proof of a solver/
  Newton-iteration corruption, not a physical result.
- `e16_g1_f3_t68p61` (30x margin, `Cfly=3 uF`): the identical signature
  recurs at a DIFFERENT absolute time (`t=5.6 us`, clean state
  `Vin=3.918 V` matching the commanded ramp, `IL1=10.10 A`, `IL2=3.00 A`)
  -- `V(vin)` jumps to `-5171.47 V` then `4.04e24 V` then plateaus near
  `-1.01e17 V`.
- All four remaining cells (control, `Cfly=0.6 uF`, `Cfly=8.7 uF`, the
  100x-margin cell) were each independently run at the R03A-default
  options and, within a bounded diagnostic window, ALL showed the same
  unambiguous corruption (raw trace time and/or state values reading
  physically impossible garbage).
- In every case examined, the corruption's onset occurred while all real
  circuit state was still completely benign (`IL1` `10-20 A`, `Vout`
  under `0.01 V`) -- nowhere near even R03A's own runaway scale
  (`563-884 A`) -- ruling out "the current got too large for the
  solver" as the direct cause, and occurred at DIFFERENT absolute times
  and different period counts for different `(Cfly,Tramp)` -- ruling out
  one specific parameter combination as the cause.

**Fix applied, with full justification:** R03A's own default "Normal"
solver settings are the ONLY thing changed; nothing physical, and
nothing in BOUNDARY.md's own "what changed" or "what did not change"
lists. `solver=alt cshunt=1e-15 plotwinsize=0` was added to `.options`
-- verified to be the EXACT solver-stabilization convention already used
verbatim in every one of this track's own prior build scripts that use
`TMAX=50 ps` (`build_b01` through `build_b06`, i.e. R04E5 through
R04E10, with zero exceptions), which is precisely the convention
BOUNDARY.md Section 5 itself cites as the source of the `TMAX=50 ps`
choice ("matching R04E9-R04E15's own numerical-resolution convention for
this class of circuit"). `cshunt=1e-15` adds a physically-negligible
femtofarad-scale shunt capacitance to every node (a standard SPICE
convergence aid for many-ideal-switch circuits); `solver=alt` selects
LTspice's alternate matrix solver; `plotwinsize=0` disables output
compression (matching R03A's own implicit uncompressed default).
`TMAX` itself is untouched, still exactly `50 ps`. **With this fix,
every re-run cell completed WITHOUT further corruption** -- all 6
completed cells' results (Section 4) are clean, fully self-consistent,
and show no trace of the corruption signature at any point.

### 3b. Severe, unpredictable per-cell runtime variance at `TMAX=50 ps`

Independent of the corruption issue (already fixed), all 6 completed
cells' real LTspice "Total elapsed time" (as printed in each cell's own
`.log`), sorted by `TSTOP`, were:

| `TSTOP` (us) | Cell | Wall time (s) | Rate (ns simulated / s wall) |
|---:|---|---:|---:|
| 301.00 | control | 1302.6 | 231.1 |
| 322.87 | g2 10x | 1932.1 | 167.1 |
| 330.68 | g1 0.6uF 30x | 11842.4 | 27.9 |
| 368.61 | g1 3uF 30x | 7937.0 | 46.4 |
| 416.84 | g1 8.7uF 30x | 2165.2 | 192.5 |
| 528.71 | g2 100x | 2525.2 | 209.3 |

**Runtime does NOT scale with `TSTOP` at all, in either direction, and
the final 2 cells make this MORE extreme, not less**: the two LARGEST
`TSTOP` cells (`416.84` and `528.71 us`) each finished FASTER in
wall-clock terms than the two SMALLER-`TSTOP` cells at `330.68` and
`368.61 us` -- `416.84 us` took `2165.2 s`, barely a third of the
`330.68 us` cell's `11842.4 s`, despite having a `26%` LARGER `TSTOP`.
The full observed rate range across all 6 cells is `27.9-231.1 ns/s`, an
`8.3x` spread. This is consistent with the underlying cause being the
SAME class of stiff, difficult-to-resolve transient events (Section 3a)
recurring at varying, apparently near-random frequency across different
`(Cfly,Tramp)` combinations -- even after the `solver=alt` fix prevents
these episodes from corrupting the result, they still cost substantial
extra wall-clock time to resolve correctly, and how often they occur is
not predictable from `TSTOP`, `Cfly`, or `Tramp` in any simple way.
Running multiple cells concurrently was also directly tested (before
this final 2-cell run) and found to make this dramatically WORSE, not
better: each LTspice process requests up to `10` threads (`Maximum
thread count: 10` in every `.log`), and this machine has only `10`
physical cores, so running `6` cells at once caused roughly `20x`
oversubscription and cut observed per-cell throughput to as little as
`~11.6 ns/s` (confirmed directly by timestamped polling during the
6-way-parallel attempt before it was abandoned in favor of running cells
one at a time). **The final 2 cells were run strictly sequentially, one
at a time, with the first (`e16_g1_f8p7_t116p84`) confirmed complete via
its own `.log` before the second (`e16_g2_f3_t228p71`) was ever
launched**, per this same finding.

**This is reported as a genuine tooling/runtime characteristic of this
netlist class at the `TMAX=50 ps` resolution BOUNDARY.md specifies, not
silently worked around** -- per the task's own explicit instruction,
`TMAX` was not coarsened at any point to make the grid finish faster.
Total real LTspice compute time across all 6 cells, run one at a time
across multiple sessions: `27704.5 s` (`~7.7` hours).

## 4. Full results table (6 of 6 cells -- grid COMPLETE)

| Case | `Cfly` | `Tramp` | `VC1` final (V) | `VC2` final (V) | `VC3` final (V) | `Vout` final (V) | `Vout` pk (V) | `LADDER_ERR` | `IL1` max (A) | `IL2` max (A) | `IL3` max (A) | `IL4` max (A) | max\|IL\| (A) | Within +/-250A? | LTspice wall time (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| control (`Tramp=1us`) | 3uF | 1us | 19.877 | 13.157 | 6.660 | 0.5588 | 0.5605 | 1.345 | 150.07 | 94.41 | 86.50 | 84.02 | 150.07 | YES | 1302.6 |
| g2 10x margin | 3uF | 22.87us | 19.863 | 13.409 | 6.573 | 0.5589 | 0.5591 | 1.342 | 111.59 | 70.77 | 70.81 | 70.78 | 111.59 | YES | 1932.1 |
| g1 30x margin | 3uF | 68.61us | 19.914 | 13.220 | 6.578 | 0.5588 | 0.5591 | 1.348 | 86.94 | 70.37 | 70.25 | 70.48 | 86.94 | YES | 7937.0 |
| g1 30x margin | 0.6uF | 30.68us | 18.991 | 13.546 | 6.107 | 0.5642 | 0.5643 | 1.399 | 92.24 | 71.66 | 70.21 | 71.18 | 92.24 | YES | 11842.4 |
| g1 30x margin | 8.7uF | 116.84us | 20.068 | 13.323 | 6.652 | 0.5579 | 0.5581 | 1.333 | 90.18 | 70.23 | 70.25 | 70.25 | 90.18 | YES | 2165.2 |
| g2 100x margin | 3uF | 228.71us | 19.860 | 13.357 | 6.636 | 0.5588 | 0.5591 | 1.339 | 75.05 | 70.37 | 70.37 | 70.44 | 75.05 | YES | 2525.2 |

Trajectory checkpoints (`VC1-3`/`Vout` at `t=Tramp`, i.e. the instant the
`Vin` ramp completes) for the four cells with a `Tramp` long enough to be
well-separated from `t=0`: `30x`-margin `Cfly=3uF` reaches `VC1=16.01 V`,
`VC2=10.61 V`, `VC3=5.29 V`, `Vout=0.449 V` at `t=68.61 us`; `30x`-margin
`Cfly=0.6uF` reaches `VC1=14.12 V`, `VC2=10.52 V`, `VC3=4.41 V`,
`Vout=0.427 V` at `t=30.68 us`; `30x`-margin `Cfly=8.7uF` reaches
`VC1=15.33 V`, `VC2=10.17 V`, `VC3=5.09 V`, `Vout=0.426 V` at
`t=116.84 us`; `100x`-margin `Cfly=3uF` reaches `VC1=18.68 V`,
`VC2=12.56 V`, `VC3=6.26 V`, `Vout=0.526 V` at `t=228.71 us` -- all four
continue rising through their remaining `300 us` settling window to
their final values above, confirming the system is still actively
charging at `TSTOP`, not stalled, in every case, including the two
longest-`Tramp` cells added in this revision.

All raw `.meas` values (including `IL1-4` minima, `VOUT_ERR`/`VCk_ERR`
component breakdowns) are in `results.csv`/`results.json`.

## 5. Comparison against R03A's own numbers

R03A (fixed `Vin=48 V` reached by `TSTART=150 us`, then PWM switched on
suddenly at full strength onto a cold `Vout`, WITH the passive-divider
network pre-charging the ladder first): phase-current maxima
`884.36/745.07/625.63/563.46 A`, `Vout` overshoot to `1.54 V` (a `54%`
overshoot past the `1 V` target).

All 6 completed R04E16 cells: phase current maxima `150.07/94.41/86.50/
84.02 A` (control), `111.59/70.77/70.81/70.78 A` (10x margin, `Cfly=3uF`),
`86.94/70.37/70.25/70.48 A` (30x margin, `Cfly=3uF`), `92.24/71.66/
70.21/71.18 A` (30x margin, `Cfly=0.6uF`), `90.18/70.23/70.25/70.25 A`
(30x margin, `Cfly=8.7uF`), and `75.05/70.37/70.37/70.44 A` (100x margin,
`Cfly=3uF`) -- comfortably inside the `+/-250 A` safety bound in every
case. **Correcting an arithmetic slip in this document's prior revision**
(which claimed "at least `5.9x` below R03A's own smallest phase peak"
for the 4-cell subset, a figure that does not reconcile with the table
above -- `563.46/150.07=3.75`, not `5.9`): directly recomputing from the
values above, the worst-case (highest-current) cell across all 6 is the
control cell at `150.07 A`, which is `3.75x` BELOW R03A's own smallest
phase-current peak (`563.46 A`); the best-case (lowest-current) cell is
the new `100x`-margin cell at `75.05 A`, `7.51x` below. Every one of the
6 cells' phase maxima falls within this `3.75x-7.51x` below-R03A range.
`Vout` shows NO overshoot in any completed cell (`Vout_pk` essentially
equal to `Vout_final`, both well BELOW the `1 V` target, not above it)
-- the opposite of R03A's `54%` overshoot. This holds for the two newly
completed cells exactly as it did for the first four: `Vout_pk-Vout_final`
is `0.00018 V` (`8.7uF` cell) and `0.00032 V` (`100x` cell), both
negligible.

## 6. Why the control cell also avoids runaway -- the counterfactual did not hold

BOUNDARY.md Section 10 explicitly anticipated this exact possibility:
"The control cell (near-instant ramp) failing to reproduce runaway-like
behavior would itself be a notable, separately-reportable finding... it
would mean removing R02B's passive network or correcting
`Lphase`/`Cfly` changed the outcome independent of the ramp idea." That
is exactly what was found. The most likely explanation: **R03A's own
runaway was driven by a mismatch this experiment's design specifically
eliminated regardless of ramp speed** -- R03A pre-charged the
flying-capacitor ladder to substantial voltages (`34.0/21.8/10.6 V`,
measured directly before its own PWM takeover) via the passive divider
BEFORE applying full-strength PWM to a still-cold `Vout`; this
experiment removes that passive divider entirely (BOUNDARY.md's own
explicit scope choice, Section 4), so the ladder and `Vout` now start
from TRUE zero energy together and must be built up simultaneously by
the switching action itself, gated by however much `Vin` is available at
each instant. With no pre-charged ladder to suddenly discharge into a
cold output, the `Vin` ramp speed may simply not be the dominant factor
this experiment set out to isolate.

A second, corroborating observation, now strengthened by the completed
grid: all FOUR `Cfly=3uF` cells (control, `10x`, `30x`, and the newly
completed `100x`) converge to NEARLY IDENTICAL final state (`Vout`
`0.5588-0.5589 V`, `VC1` `19.86-19.91 V`, `LADDER_ERR` `1.339-1.348`)
despite a `229x` range in `Tramp` (`1` to `228.71 us`, the full margin
sweep). Every trajectory shows `VC1`/`Vout` still RISING at `TSTOP` (not
yet plateaued -- e.g. for the new `100x`-margin cell,
`VOUT_AT_TRAMP=0.526 V` vs `VOUT_FINAL=0.559 V`, still climbing through
the `300 us` post-ramp window), consistent with the same underlying
charge-accumulation process dominating the LONG (`300 us`) post-ramp
settling window in all four cells, largely independent of how the first
`1-229 us` were spent ramping `Vin` up. Both `Cfly=0.6uF` and the new
`Cfly=8.7uF` cell (both `30x` margin) reach similar but not identical
final states (`Vout=0.5642 V`/`LADDER_ERR=1.399` and `Vout=0.5579 V`/
`LADDER_ERR=1.333` respectively) -- see Section 7 for the now-complete
3-point `Cfly` trend this permits.

**A third observation, new in this revision: while the control-cell
counterfactual still falsifies the CLEAN causal claim ("the ramp is what
avoids runaway" -- even `Tramp=1 us` avoids it), the completed 4-point
`Cfly=3uF` margin sweep (control/`10x`/`30x`/`100x` =
`150.07/111.59/86.94/75.05 A` for `IL1_max`) shows ramp speed DOES have
a real, cleanly MONOTONIC, secondary quantitative effect on peak
transient current -- slower ramps produce smaller current peaks, with
diminishing returns (`-25.6%`, then `-22.1%`, then `-13.7%` per
successive margin step). So the ramp mechanism is not the thing that
determines WHETHER runaway happens (that appears governed by the
passive-divider removal, independent of ramp speed, per the reasoning
above) but it does measurably affect HOW LARGE the benign transient is.
This is a real, if secondary, causal role for Roberts' own mechanism,
not previously demonstrable with only 3 margin points.**

**This experiment's own design still cannot cleanly separate "the ramp
avoided runaway" from "removing the passive divider (or the `Lphase`
correction) avoided runaway independent of the ramp" -- both changes
were made simultaneously (BOUNDARY.md Section 4), and the control cell's
result shows the ramp specifically is not NECESSARY for the benign
qualitative outcome observed here, even though it does measurably shape
the transient's magnitude (previous paragraph).** A future experiment
isolating each change (e.g. Vin ramp WITH the divider still removed vs.
instant Vin step WITH the divider still present, holding `Lphase` fixed)
would still be needed to assign the qualitative (runaway/no-runaway)
causality cleanly.

## 7. Sensitivity to margin factor (`Tramp`) at fixed `Cfly=3 uF`
   (four completed data points -- GRID COMPLETE), and to `Cfly` at fixed
   `30x` margin (three completed data points -- GRID COMPLETE)

### 7a. Margin-factor / `Tramp` sensitivity at `Cfly=3 uF` (control, `10x`,
    `30x`, `100x` -- all four now complete)

Four completed cells hold `Cfly=3 uF` fixed and span `Tramp` from `1` to
`228.71 us` (a `229x` range, covering the control point plus the `10x`,
`30x`, and `100x` margin points). Across this whole range:

- **`Vout_final`, `VC1-3_final`, and `LADDER_ERR` remain essentially
  insensitive to `Tramp`** -- all four agree to within `2%` of each
  other (`Vout_final` `0.5588-0.5589 V`; `LADDER_ERR` `1.339-1.348`),
  now confirmed across the FULL margin range including the new `100x`
  point.
- **Peak inductor current (`IL1_max`) DOES vary substantially with
  `Tramp`, and is now confirmed CLEANLY MONOTONIC across all 4 points**:
  `150.07 A` (`Tramp=1 us`, control) -> `111.59 A` (`Tramp=22.87 us`,
  `10x`) -> `86.94 A` (`Tramp=68.61 us`, `30x`) -> `75.05 A`
  (`Tramp=228.71 us`, `100x`) -- a `50%` total drop from the fastest to
  the slowest tested ramp, with clearly DIMINISHING RETURNS at each
  successive step (`-25.6%`, then `-22.1%`, then `-13.7%` per margin
  step, even though `Tramp` itself increases by `23x`, then `3x`, then
  `3.3x` at each step) -- consistent with `IL1_max` being driven mainly
  by the FIRST few switching periods' Coss/LC-type turn-on transient (a
  fast, largely `Tramp`-independent phenomenon at short `Tramp`) rather
  than scaling proportionally with the ramp's own duration, but WITH a
  real, monotonic, secondary sensitivity to how slow the ramp is (see
  Section 6's new third observation).
- `IL2_max`, `IL3_max`, `IL4_max` remain comparatively stable across all
  four cells (`70.2-94.4 A`), much less sensitive to `Tramp` than
  `IL1_max` -- consistent with phase 1 (the only phase with a direct
  `Vin` connection) bearing the brunt of the ramp-related current
  differences, while phases 2-4 (which only see relayed charge through
  the flying capacitors) are comparatively insulated from it. This
  pattern, previously observed on 3 points, holds cleanly on the 4th.

### 7b. `Cfly` sensitivity at `30x` margin (`0.6/3/8.7 uF` -- all three
    now complete)

Three completed cells hold the `30x`-margin convention fixed and span
`Cfly=0.6/3/8.7 uF` (with correspondingly paired `Tramp=30.68/68.61/
116.84 us`, per `ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`'s own
scaling). This is now a genuine, real 3-point trend (the prior revision
of this document had only a single `Cfly=0.6uF` point and explicitly
could not assess monotonicity):

- **`LADDER_ERR` decreases MONOTONICALLY with increasing `Cfly`**:
  `1.399` (`0.6uF`) -> `1.348` (`3uF`) -> `1.333` (`8.7uF`) -- a modest
  but clean, real trend (larger `Cfly` gives modestly better ladder
  convergence toward target by `TSTOP`), though even the best case
  (`1.333`) remains far from `LOCAL_PASS`-style convergence
  (`<0.05-0.1`).
- **`Vout_final` decreases slightly with increasing `Cfly`** in the same
  direction: `0.5642 V` (`0.6uF`) -> `0.5588 V` (`3uF`) -> `0.5579 V`
  (`8.7uF`) -- a small (`~1.1%` total) but monotonic effect, consistent
  with the `LADDER_ERR` trend.
- **`IL1_max` is NOT monotonic with `Cfly`**: `92.24 A` (`0.6uF`) ->
  `86.94 A` (`3uF`) -> `90.18 A` (`8.7uF`) -- a dip-then-rise pattern,
  though all three values stay within a narrow `6%` band
  (`86.94-92.24 A`) of each other, a much smaller spread than the
  margin-factor sensitivity in Section 7a. `IL2-4_max` are essentially
  flat across all three `Cfly` values (`70.2-71.7 A`).
- **Honest summary**: `Cfly` sensitivity is real but modest for the
  ladder-convergence metrics (`LADDER_ERR`, `Vout_final`), and small and
  non-monotonic for peak current (`IL1_max`) -- unlike the margin-factor
  axis (Section 7a), which shows a clean, larger, monotonic effect on
  `IL1_max`. Neither axis changes the qualitative outcome: no cell in
  either sweep approaches runaway or the `+/-250 A` bound.

## 8. What this does and does not establish

**Establishes:**
- On all 6 cells of the now-COMPLETE grid (spanning the full margin
  range from `1` to `228.71 us` `Tramp` at `Cfly=3 uF`, plus `Cfly=0.6`
  and `8.7 uF` at `30x` margin), NONE reproduce R03A's catastrophic
  current runaway or output overshoot -- all stay at least `3.75x` below
  R03A's own smallest phase-current peak (up to `7.51x` below for the
  best case) and well inside the `+/-250 A` safety bound.
- The control cell (near-instantaneous ramp) equally avoids the
  runaway, directly falsifying the clean form of this experiment's own
  hypothesis ("the `Vin` ramp specifically is what avoids R03A's
  diagnosed failure") -- at minimum, removing R02B's passive-divider
  precharge network appears to be doing substantial, possibly dominant,
  work independent of ramp speed. This conclusion is UNCHANGED by
  completing the grid: it holds as strongly with all 6 cells as it did
  with the first 4.
- **New in this revision**: ramp speed DOES have a real, cleanly
  monotonic, SECONDARY quantitative effect on peak transient current
  (`IL1_max` drops `150.07 -> 111.59 -> 86.94 -> 75.05 A` monotonically
  across the full `1-228.71 us` `Tramp` range at `Cfly=3uF`, with
  diminishing returns at each step) -- so while the ramp does not
  determine WHETHER runaway occurs, it does measurably shape HOW LARGE
  the benign transient current is (Section 6, Section 7a).
- **New in this revision**: a real, if modest, `Cfly` sensitivity trend
  now exists (3 points at `30x` margin): `LADDER_ERR` and `Vout_final`
  both decrease monotonically with increasing `Cfly` (a small effect,
  `LADDER_ERR` `1.399->1.348->1.333`), while `IL1_max` is small and
  non-monotonic across the same 3 points (Section 7b).
- R03A's own default LTspice solver options are NOT usable for this
  netlist family at `TMAX=50 ps` -- a genuine, reproducible, forensically
  -confirmed numerical-tooling limitation, not a circuit-physics finding,
  fixed by adopting this project's own already-established
  `solver=alt`/`cshunt` convention for this class of circuit. Both cells
  completed in this revision were independently re-checked for the same
  corruption fingerprint (Section 3b) and show none.
- This netlist class exhibits extreme, `TSTOP`-disproportionate runtime
  variance at `TMAX=50 ps` (`27.9-231.1 ns` of simulated time per
  wall-clock second, an `8.3x` spread now confirmed across all 6 cells)
  and severe throughput collapse under concurrent execution
  (oversubscribed 6-way-parallel throughput measured directly at
  `~11.6 ns/s`, `~20x` worse than solo) -- a second, independent
  tooling/runtime finding, reported honestly per this experiment's own
  task instructions rather than addressed by coarsening `TMAX`. All 6
  cells were run strictly one at a time, never concurrently.

**Does not establish:**
- That the `Vin`-ramp mechanism itself (Roberts' own Sec. 3.5 idea) is
  the thing that determines whether runaway occurs -- the control-cell
  result specifically undermines that clean causal claim (Section 6),
  even though the ramp does measurably affect transient current
  magnitude (see "Establishes" above). This remains true with the full
  6-cell grid.
- Full `LOCAL_PASS`-style convergence to the `36/24/12/1 V` ladder/`Vout`
  targets -- all 6 completed cells reach only `~56%` of `Vout` target and
  `LADDER_ERR~=1.33-1.40` (far from the `<0.05-0.1` range other Track-B
  passive-divider experiments reached) by `TSTOP`; the system is still
  visibly rising, not stalled, but `300 us` is not enough settling time
  at this operating point, for any tested `(Cfly,Tramp)` combination.
- Any GS61008T device-level (`Coss`/dead-time/ZVS) validation -- ideal
  switches only, same limitation as R03A and every other Track-B
  fixed-timing experiment.
- Which single `Cfly` or margin factor is "correct" -- all remain
  `SENSITIVITY_ONLY`; the trends found (Section 7) characterize
  sensitivity, they do not identify a preferred operating point.
- A P24 reproduction claim of any kind (same standing Track-B
  limitation as R04E9-R04E15).

## 9. Provenance and classification (BOUNDARY.md Section 7 cross-check)

All values used match BOUNDARY.md Section 7's own table exactly (no new
paper-sourced values introduced). The one addition beyond BOUNDARY.md's
own list -- `solver=alt cshunt=1e-15 plotwinsize=0` -- is a
numerical-stabilization-technique choice (not a physical/circuit value),
justified in Section 3a above by direct reference to this project's own
existing, already-committed convention for the identical `TMAX=50 ps`
resolution target; classified `NUMERICAL_IDEALIZATION` /
`TOOLING_NECESSITY`, not `SENSITIVITY_ONLY` and not a paper value of any
kind. `TMAX=50 ps` itself was never altered from BOUNDARY.md's own
locked value at any point across all 6 cells, despite the severe runtime
cost documented in Section 3b.

Overall classification: **`CONTROLLER_GUARD_PASS`-style success on the
`+/-250 A` current-safety bar for all 6 of 6 cells** (grid now COMPLETE);
**NOT `LOCAL_PASS`** (no completed cell reaches the `Vout`/`VCk` handoff
tolerance bands by `TSTOP`); **the experiment's own core causal
hypothesis (ramp specifically responsible for WHETHER runaway occurs) is
`NOT CONFIRMED` / `UNDERMINED`** by the control-cell counterfactual, per
BOUNDARY.md Section 10's own explicit anticipation of this exact
outcome -- **but the ramp DOES have a confirmed, monotonic, secondary
causal role in the MAGNITUDE of the transient current** (new in this
revision, Section 6/7a); **`SENSITIVITY_ONLY`** for every swept
parameter, now WITH completed, characterized trends for both the
margin-factor axis (clean, monotonic, sizeable effect on `IL1_max`) and
the `Cfly` axis (modest, monotonic effect on `LADDER_ERR`/`Vout_final`;
small, non-monotonic effect on `IL1_max`); **`CROSS_PAPER_EXTENSION`**
for the overall mechanism, unchanged from BOUNDARY.md Section 7. **Grid
status: `GRID_COMPLETE` (6/6 cells)** -- the `GRID_INCOMPLETE` status in
this document's prior revision is resolved; all 6 cells reached
completion, were verified against the solver-corruption fingerprint
(Section 3a/3b), and are reported in full above.
