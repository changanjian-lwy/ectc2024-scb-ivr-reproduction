# R04E16 result - Roberts' soft-start mechanism on fixed-timing 4-phase PWM

## Outcome, stated first

**Every one of the 4 cells that reached completion avoids R03A's diagnosed
catastrophic current runaway** (R03A's own phase-current maxima were
`563-884 A`; every completed R04E16 cell stays under `151 A`, well inside
the `+/-250 A` safety bound). **But the control cell (near-instantaneous
ramp, `Tramp=1 us`) ALSO avoids it**, settling to essentially the SAME
steady-state operating point as the slow-ramp cells (`Vout~=0.559-0.564 V`,
`LADDER_ERR~=1.34-1.40` across all four cells directly checked, spanning
`Tramp` from `1 us` to `68.61 us` and `Cfly` from `0.6` to `3 uF`). This is
exactly the failure mode BOUNDARY.md Section 10 itself flagged as a
possible, separately-reportable outcome: **the counterfactual this
experiment's own design depends on did not hold** -- the near-instant-ramp
control case does not reproduce runaway-like behavior, so the absence of
runaway in the slow-ramp cells cannot be cleanly attributed to the `Vin`
ramp mechanism itself. The most likely alternative explanation, developed
in Section 6 below: removing R02B's passive-divider precharge network
(this experiment's own explicit scope choice, BOUNDARY.md Section 4)
eliminates the specific mismatch R03A's own diagnosis identified (a
PRE-CHARGED capacitor ladder suddenly exposed to full-strength PWM while
`Vout` is still cold) -- and that mismatch, not the ramp speed, is
plausibly what R03A's runaway actually depended on.

**Grid completion status, reported honestly per this project's own
transparency convention rather than silently forced to appear complete:
4 of 6 cells reached completion and are fully verified below (the control
cell, both Grid-2/Grid-1 `Cfly=3 uF` cells at `10x` and `30x` margin, and
-- added in a same-day follow-up commit once it finished running
unattended overnight -- the Grid-1 `Cfly=0.6 uF`/`30x`-margin cell, real
LTspice wall time `11842.4 s`, `~3.29` hours). The remaining 2 cells
(`Cfly=8.7 uF` at `30x` margin, and the `100x`-margin cell) were built and
launched but were still running, unfinished, when the background process
hosting them was terminated (no `.log` `Total elapsed time` line, no
`.meas` output for either) -- Section 3 documents a second, independent,
load-bearing finding that explains why completion is so slow: this
netlist class exhibits extreme and UNPREDICTABLE per-cell runtime
variance (`1302.6 s`, `1932.1 s`, `7937.0 s`, and `11842.4 s` of real
LTspice compute time for the four completed cells, which do NOT scale
proportionally with `TSTOP`: the `368.61 us`-`TSTOP` cell took `4.1x`
longer than the `322.87 us`-`TSTOP` cell despite only a `14%` longer
target, and the `330.68 us`-`TSTOP` `Cfly=0.6 uF` cell took LONGER than
the `368.61 us`-`TSTOP` `Cfly=3 uF` cell despite a SHORTER `TSTOP`).
Extrapolating the observed variance, the remaining 2 cells (with `TSTOP`
up to `528.71 us`) could plausibly require several additional hours each
-- reported honestly as a tooling/runtime characteristic of this circuit
class at `TMAX=50 ps`, not silently worked around by coarsening the
timestep (explicitly prohibited by this experiment's own task
instructions). Completing them would require a further, separately
launched run; this document does not claim they are complete.

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
| 1 | `e16_g1_f8p7_t116p84`| 8.7 uF | 116.84 us| 30x | 416.84 us | built, not yet run to completion |
| 2 | `e16_g2_f3_t228p71`  | 3 uF | 228.71 us| 100x| 528.71 us | built, not yet run to completion |

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
every re-run cell completed WITHOUT further corruption** -- the 3
completed cells' results (Section 4) are clean, fully self-consistent,
and show no trace of the corruption signature at any point.

### 3b. Severe, unpredictable per-cell runtime variance at `TMAX=50 ps`

Independent of the corruption issue (already fixed), the 3 completed
cells took `1302.6 s`, `1932.1 s`, and `7937.0 s` of real LTspice
"Total elapsed time" (as printed in each cell's own `.log`) respectively
for `TSTOP` values of `301`, `322.87`, and `368.61 us` -- i.e. simulated-
time-per-wall-second rates of `231`, `167`, and only `46.4 ns/s`
respectively. **Runtime does NOT scale proportionally with `TSTOP`**:
the `368.61 us` cell (only `14%` longer `TSTOP` than the `322.87 us`
cell) took `4.1x` longer in wall-clock terms. This is consistent with
the underlying cause being the SAME class of stiff, difficult-to-resolve
transient events (Section 3a) recurring at varying frequency across
different `(Cfly,Tramp)` combinations -- even after the `solver=alt`
fix prevents these episodes from corrupting the result, they still cost
substantial extra wall-clock time to resolve correctly, and how often
they occur is not simply proportional to `TSTOP`. Running multiple
cells concurrently was also directly tested and found to make this
dramatically WORSE, not better: each LTspice process requests up to
`10` threads (`Maximum thread count: 10` in every `.log`), and this
machine has only `10` physical cores, so running `6` cells at once
caused roughly `p20x` oversubscription and cut observed per-cell
throughput to as little as `~11.6 ns/s` (confirmed directly by
timestamped polling during the 6-way-parallel attempt before it was
abandoned in favor of running cells one at a time).

**This is reported as a genuine tooling/runtime characteristic of this
netlist class at the `TMAX=50 ps` resolution BOUNDARY.md specifies, not
silently worked around** -- per the task's own explicit instruction,
`TMAX` was not coarsened to make the grid finish faster. Extrapolating
the observed `46-231 ns/s` range to the 3 remaining cells' `TSTOP`
values (`330.68`-`528.71 us`) implies each could plausibly require
`1400`-`11000+` seconds (`23 min`-`>3 hours`) of real compute time,
individually, run one at a time (parallel execution would only make this
worse per the finding above) -- ruling out completing all 6 within a
practical single-session time budget while still respecting the
locked `TMAX=50 ps` and the prohibition on parallel-induced slowdown.

## 4. Full results table (4 of 6 cells; see Section 2 for pending-cell status)

| Case | `Cfly` | `Tramp` | `VC1` final (V) | `VC2` final (V) | `VC3` final (V) | `Vout` final (V) | `Vout` pk (V) | `LADDER_ERR` | `IL1` max (A) | `IL2` max (A) | `IL3` max (A) | `IL4` max (A) | max\|IL\| (A) | Within +/-250A? | LTspice wall time (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| control (`Tramp=1us`) | 3uF | 1us | 19.877 | 13.157 | 6.660 | 0.5588 | 0.5605 | 1.345 | 150.07 | 94.41 | 86.50 | 84.02 | 150.07 | YES | 1302.6 |
| g2 10x margin | 3uF | 22.87us | 19.863 | 13.409 | 6.573 | 0.5589 | 0.5591 | 1.342 | 111.59 | 70.77 | 70.81 | 70.78 | 111.59 | YES | 1932.1 |
| g1 30x margin | 3uF | 68.61us | 19.914 | 13.220 | 6.578 | 0.5588 | 0.5591 | 1.348 | 86.94 | 70.37 | 70.25 | 70.48 | 86.94 | YES | 7937.0 |
| g1 30x margin | 0.6uF | 30.68us | 18.991 | 13.546 | 6.107 | 0.5642 | 0.5643 | 1.399 | 92.24 | 71.66 | 70.21 | 71.18 | 92.24 | YES | 11842.4 |

Trajectory checkpoints (`VC1-3`/`Vout` at `t=Tramp`, i.e. the instant the
`Vin` ramp completes) for the two cells with a `Tramp` long enough to be
well-separated from `t=0`: `30x`-margin `Cfly=3uF` reaches `VC1=16.01 V`,
`VC2=10.61 V`, `VC3=5.29 V`, `Vout=0.449 V` at `t=68.61 us`; `30x`-margin
`Cfly=0.6uF` reaches `VC1=14.12 V`, `VC2=10.52 V`, `VC3=4.41 V`,
`Vout=0.427 V` at `t=30.68 us` -- both continue rising through their
remaining `300 us` settling window to their final values above,
confirming the system is still actively charging at `TSTOP`, not stalled,
in both cases.

All raw `.meas` values (including `IL1-4` minima, `VOUT_ERR`/`VCk_ERR`
component breakdowns) are in `results.csv`/`results.json`.

## 5. Comparison against R03A's own numbers

R03A (fixed `Vin=48 V` reached by `TSTART=150 us`, then PWM switched on
suddenly at full strength onto a cold `Vout`, WITH the passive-divider
network pre-charging the ladder first): phase-current maxima
`884.36/745.07/625.63/563.46 A`, `Vout` overshoot to `1.54 V` (a `54%`
overshoot past the `1 V` target).

All 4 completed R04E16 cells: phase current maxima `150.07/94.41/86.50/
84.02 A` (control), `111.59/70.77/70.81/70.78 A` (10x margin, `Cfly=3uF`),
`86.94/70.37/70.25/70.48 A` (30x margin, `Cfly=3uF`), and `92.24/71.66/
70.21/71.18 A` (30x margin, `Cfly=0.6uF`) -- ALL at least `5.9x` BELOW
R03A's own SMALLEST phase peak, and all comfortably inside the
`+/-250 A` safety bound. `Vout` shows NO overshoot in any completed
cell (`Vout_pk` essentially equal to `Vout_final`, both well BELOW the
`1 V` target, not above it) -- the opposite of R03A's `54%` overshoot.

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

A second, corroborating observation: the three `Cfly=3uF` cells converge
to NEARLY IDENTICAL final state (`Vout` `0.5588-0.5589 V`, `VC1`
`19.86-19.91 V`, `LADDER_ERR` `1.342-1.348`) despite a `69x` range in
`Tramp` (`1` to `68.61 us`). Every trajectory shows `VC1`/`Vout` still
RISING at `TSTOP` (not yet plateaued -- e.g. for the 30x-margin cell,
`VOUT_AT_TRAMP=0.449 V` vs `VOUT_FINAL=0.559 V`, still climbing through
the `300 us` post-ramp window), consistent with the same underlying
charge-accumulation process dominating the LONG (`300 us`) post-ramp
settling window in all three cells, largely independent of how the
first `1-69 us` were spent ramping `Vin` up. The `Cfly=0.6uF` cell (30x
margin) reaches a similar but not identical final state (`Vout=0.5642 V`,
`LADDER_ERR=1.399`, modestly worse than the `Cfly=3uF` group) -- see
Section 7 for whether this `Cfly` difference is meaningful given only one
`Cfly=0.6uF` data point exists.

**This experiment's own design cannot cleanly separate "the ramp
avoided runaway" from "removing the passive divider (or the `Lphase`
correction) avoided runaway independent of the ramp" -- both changes
were made simultaneously (BOUNDARY.md Section 4), and the control cell's
result shows the ramp specifically is not necessary for the benign
outcome observed here.** A future experiment isolating each change (e.g.
Vin ramp WITH the divider still removed vs. instant Vin step WITH the
divider still present, holding `Lphase` fixed) would be needed to assign
causality cleanly.

## 7. Sensitivity to `Tramp` at fixed `Cfly=3 uF` (three completed data
   points), plus one new `Cfly=0.6 uF` data point; `Cfly=8.7 uF` and the
   `100x` margin point remain untested (Section 2/3b)

Three completed cells hold `Cfly=3 uF` fixed and span `Tramp` from `1` to
`68.61 us` (a `69x` range, covering the control point plus the `10x` and
`30x` margin points). Across this whole range:

- **`Vout_final`, `VC1-3_final`, and `LADDER_ERR` are essentially
  insensitive to `Tramp`** -- all agree to within `2%` of each other
  (`Vout_final` `0.5588-0.5589 V`; `LADDER_ERR` `1.342-1.348`).
- **Peak inductor current (`IL1_max`) DOES vary substantially with
  `Tramp`, but NOT monotonically**: `150.07 A` (`Tramp=1 us`) ->
  `111.59 A` (`Tramp=22.87 us`) -> `86.94 A` (`Tramp=68.61 us`) -- a
  `42%` drop from the fastest to the slowest tested ramp, but the
  ordering (control highest, 30x-margin lowest) IS monotonic with
  `Tramp` even though the two intermediate values are not evenly
  spaced relative to `Tramp` itself (`Tramp` increases `23x` between
  the first two points for only a `26%` `IL1_max` drop, then increases
  only `3x` more for a further `22%` drop) -- consistent with `IL1_max`
  being driven mainly by the FIRST few switching periods' Coss/LC-type
  turn-on transient (a fast, largely `Tramp`-independent phenomenon at
  short `Tramp`) rather than scaling smoothly with the ramp's own
  duration.
- `IL2_max`, `IL3_max`, `IL4_max` are comparatively stable across all
  three cells (`70.25-94.41 A`), much less sensitive to `Tramp` than
  `IL1_max` -- consistent with phase 1 (the only phase with a direct
  `Vin` connection) bearing the brunt of the ramp-related current
  differences, while phases 2-4 (which only see relayed charge through
  the flying capacitors) are comparatively insulated from it.
- **One `Cfly=0.6 uF` data point is now available** (30x margin,
  `Tramp=30.68 us`, the pairing this project's own derivation model
  specifies for that `Cfly`). Its `LADDER_ERR` (`1.399`) is
  `~4-4.2%` HIGHER (worse) than the three `Cfly=3 uF` cells' own
  `1.342-1.348` range, and its `IL1_max` (`92.24 A`) sits between the
  10x-margin (`111.59 A`) and 30x-margin (`86.94 A`) `Cfly=3uF` cells --
  a modest, not dramatic, difference. **With only ONE `Cfly=0.6uF` point
  and no `Cfly=8.7uF` point at all, this cannot establish a `Cfly`-
  sensitivity trend** (a single point cannot show monotonicity or its
  absence) -- it only shows the `Cfly=0.6uF`/`Tramp=30.68us` combination
  does not qualitatively change the picture (still no runaway, still a
  similar `LADDER_ERR`/`Vout` order of magnitude). Full `Cfly` sensitivity
  (the `8.7 uF` cell) and the `100x` margin-factor sensitivity point
  remain untested (Section 2/3b) -- an honest, explicit gap in this
  experiment's own completed grid, not a claim that `Cfly`/margin-factor
  sensitivity is small.

## 8. What this does and does not establish

**Establishes:**
- On the 4 cells that could be completed (spanning the full `Tramp`
  range from `1` to `68.61 us` at `Cfly=3 uF`, plus one `Cfly=0.6 uF`
  point), NONE reproduce R03A's catastrophic current runaway or output
  overshoot -- all stay at least `5.9x` below R03A's own smallest
  phase-current peak and well inside the `+/-250 A` safety bound.
- The control cell (near-instantaneous ramp) equally avoids the
  runaway, directly falsifying the clean form of this experiment's own
  hypothesis ("the `Vin` ramp specifically is what avoids R03A's
  diagnosed failure") -- at minimum, removing R02B's passive-divider
  precharge network appears to be doing substantial, possibly dominant,
  work independent of ramp speed.
- R03A's own default LTspice solver options are NOT usable for this
  netlist family at `TMAX=50 ps` -- a genuine, reproducible, forensically
  -confirmed numerical-tooling limitation, not a circuit-physics finding,
  fixed by adopting this project's own already-established
  `solver=alt`/`cshunt` convention for this class of circuit.
- This netlist class exhibits extreme, `TSTOP`-disproportionate runtime
  variance at `TMAX=50 ps` (`46-231 ns` of simulated time per wall-clock
  second, a `5x` spread across only 3 cells) and severe throughput
  collapse under concurrent execution (oversubscribed 6-way-parallel
  throughput measured directly at `~11.6 ns/s`, `~20x` worse than
  solo) -- a second, independent tooling/runtime finding, reported
  honestly per this experiment's own task instructions rather than
  addressed by coarsening `TMAX`.

**Does not establish:**
- That the `Vin`-ramp mechanism itself (Roberts' own Sec. 3.5 idea) is
  responsible for the benign outcome -- the control-cell result
  specifically undermines a clean causal claim here (Section 6).
- Full `LOCAL_PASS`-style convergence to the `36/24/12/1 V` ladder/`Vout`
  targets -- all 4 completed cells reach only `~56%` of `Vout` target and
  `LADDER_ERR~=1.34-1.40` (far from the `<0.05-0.1` range other Track-B
  passive-divider experiments reached) by `TSTOP`; the system is still
  visibly rising, not stalled, but `300 us` is not enough settling time
  at this operating point.
- A `Cfly` sensitivity TREND -- only one `Cfly=0.6 uF` point exists
  (Section 7), not enough to show monotonicity or its absence; `Cfly=8.7
  uF` and the `100x` margin-factor sensitivity point remain uncompleted
  (Section 2/3b), an explicit, honestly-reported gap.
- Any GS61008T device-level (`Coss`/dead-time/ZVS) validation -- ideal
  switches only, same limitation as R03A and every other Track-B
  fixed-timing experiment.
- Which single `Cfly` or margin factor is "correct" -- all remain
  `SENSITIVITY_ONLY`.
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
locked value, despite the severe runtime cost documented in Section 3b.

Overall classification: **`CONTROLLER_GUARD_PASS`-style success on the
`+/-250 A` current-safety bar for all 4 completed cells**; **NOT
`LOCAL_PASS`** (no completed cell reaches the `Vout`/`VCk` handoff
tolerance bands by `TSTOP`); **the experiment's own core causal
hypothesis (ramp specifically responsible) is `NOT CONFIRMED` /
`UNDERMINED`** by the control-cell counterfactual, per BOUNDARY.md
Section 10's own explicit anticipation of this exact outcome;
**`SENSITIVITY_ONLY`** for every swept parameter, with `Cfly=8.7uF` and
the `100x`-margin axis left explicitly untested and `Cfly=0.6uF`
represented by only a single point (insufficient for a trend claim);
**`CROSS_PAPER_EXTENSION`** for the overall mechanism, unchanged from
BOUNDARY.md Section 7; **`GRID_INCOMPLETE`** (4/6 cells) with the
remaining incompleteness attributed to a documented, honestly-reported
tooling/runtime cause (Section 3b), not a physical-circuit cause and not
a silent omission.
