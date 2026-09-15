# R04E12 result - phase-1 precharge admission gate

## Outcome, stated first

**The `N_PRECHARGE=1` baseline cell is confirmed IDENTICAL to R04E10's own
committed `I_LIMIT=60 A`/`T_CHARGE_MAX=50 ns` cell to full printed
precision** on every checked quantity (`STATE_FINAL`, `VOUT_FINAL`,
`VC1-3_FINAL`, all `IL1-4_MAX/MIN`, all `ICS1-3_MAX/MIN`, `T_ROT1`) --
Section 2 below. The new precharge admission-gate construct (a
compile-time-unrolled chain of `N_PRECHARGE-1` extra state pairs
electrically mirroring `CHARGE1`/`FREE1`, chained before the real
`CHARGE1`, see Section 1) was pilot-verified directly against the raw
`.machine` state trace for both `N_PRECHARGE=3` and `N_PRECHARGE=10`
**and passes all three verification checks in both cases**: the machine
visits every precharge pair exactly once, in strictly increasing order,
before ever reaching the real `CHARGE1`, and the precharge chain is never
re-entered after the machine first reaches `CHARGE2` (Section 3).

Across the 5-cell grid (`N_PRECHARGE in {1,3,5,10,20}`, `I_LIMIT=60 A`,
`T_CHARGE_MAX=T_FREEWHEEL_MAX=50 ns` fixed), **`Vout` improves
monotonically and unambiguously with `N_PRECHARGE`** (`0.0141 -> 0.0145 ->
0.0157 -> 0.0163 -> 0.0197 V`, `40%` higher at `N_PRECHARGE=20` than at
the baseline) -- the cleanest, least ambiguous result in this grid.
**`VC2` -- the axis this experiment was specifically designed to help
(BOUNDARY.md Section 7) -- does NOT improve monotonically**: it is better
than baseline at `N_PRECHARGE=3` (`+16%`) and best of the whole grid at
`N_PRECHARGE=20` (`+38%`), but WORSE than baseline at `N_PRECHARGE=5`
(`-18%`) and essentially flat at `N_PRECHARGE=10` (`+0.5%`). This is
reported plainly as a **non-monotonic, mixed result**, per Ground Rule 7 --
not forced into either a clean "it helps" or "it doesn't help" verdict.
A genuine new trade-off was found: at `N_PRECHARGE=20` (the cell with the
single best `VC2` value in the grid), `VC3` goes **negative**
(`-0.170 V`, the only negative final value for any state variable in this
entire grid, worse than baseline's small positive `+0.087 V`) -- the best
`VC2` cell is also the worst `VC3` cell. No cell reaches the handoff
condition; every cell remains `CONTROLLER_GUARD_PASS`. Phase currents stay
safely bounded in every cell (worst case `IL1_max=60.18 A`, `24%` of the
`+/-250 A` safety bound). The R04E11-diagnosed retry/chatter dynamic and
its coincident `ICS1-3` numerical artifact recur in **every one of the 5
cells**, at essentially the SAME severity regardless of `N_PRECHARGE`
(`19-22%` of settled-state dwell transitions are reversals in every cell,
matching R04E10's own `19%` figure for its representative cell) -- this is
the already-diagnosed R04E10/R04E11 phenomenon recurring exactly as
BOUNDARY.md Section 1 anticipated, not a new mystery, and is flagged (not
silently trusted) using the same `>1000 A` `ICS1-3` filter, with `IL1-4`
treated as the trustworthy peak-current indicator.

## 1. The implementation construct actually used, and why

BOUNDARY.md Section 2's own suggested approach describes a runtime counter
node that gates `FREE1`'s single `.rule` transition target between
`CHARGE1` and `CHARGE2`. Before building anything, every existing
`.machine` construct in this project's own R04E5-R04E11 lineage was
grepped directly (not assumed): **every single state, in every one of the
dozens of committed case files checked, has EXACTLY ONE `.rule <from> <to>
<cond>` line** -- never two rules sharing the same `<from>` state with
different `<to>` targets. Rather than rely on unverified multi-rule-per-
state branching semantics (a genuinely new, never-before-used feature of
this project's own `.machine` usage, and an unnecessary risk in an already
solver-stiff construct family per R04E11's own finding), this experiment
implements the IDENTICAL admission-gate behavior BOUNDARY.md Section 2
describes using a **compile-time-unrolled static chain**: for a given
`N_PRECHARGE=N`, the generated netlist (`scripts/build_r04e12_cases.py`)
contains `N-1` extra state pairs (`PCHG1_k`/`PFREE1_k`, `k=1..N-1`), each
an EXACT electrical mirror of `CHARGE1`/`FREE1` (same current-limit-OR-
timeout / zero-crossing-OR-timeout rule, using the SAME shared `timer`/
`timer_chg` nodes and `I_LIMIT`/`T_CHARGE_MAX`/`T_FREEWHEEL_MAX`
parameters `CHARGE1`/`FREE1` already use, same phase-1-only gate drive),
chained `PCHG1_1->PFREE1_1->PCHG1_2->PFREE1_2->...->PCHG1_{N-1}->
PFREE1_{N-1}->CHARGE1(real)->FREE1(real)->CHARGE2->...->FREE4->
CHARGE1(real, permanent round robin -- the precharge chain is never
re-entered)`.

Because this project already generates one netlist per grid cell (its
established convention), the "counter" BOUNDARY.md Section 2 describes is
realized as this per-cell topology choice rather than a runtime SPICE
node -- functionally identical (each precharge pass is a bona fide,
independently-timed-out repeat visit to phase 1's own current-limit-OR-
timeout charge state and zero-crossing-OR-timeout free state), while
avoiding introducing an additional, unvalidated counter/comparator
construct into the machine. For `N_PRECHARGE=1` the generator emits ZERO
extra state pairs -- `CHARGE1` is state `0`, exactly R04E10's own
numbering -- making the `N_PRECHARGE=1` cell mechanism-identical to
R04E10's own committed cell BY CONSTRUCTION, confirmed directly in Section
2 below.

The whole extended state numbering (`0 .. 2*(N-1)+7`) strictly alternates
charge-role (even code) / free-role (odd code), exactly as R04E10's own
original `0..7` numbering did. This was exploited to generalize the
existing per-machine-wide (not per-phase) `timer`/`timer_chg` reset-gate
construct cleanly: the timer boolean expressions were extended from
R04E10's original 4-term OR-chains to cover every charge-role state (all
`PCHG1_k` plus `CHARGE1-4`) and every free-role state (all `PFREE1_k` plus
`FREE1-4`) respectively -- up to 23 terms each at `N_PRECHARGE=20`. This
structural property (state-code parity = role) was verified directly by
script (Section 4 below), not assumed.

Subcircuit renamed `SCB4P_P24_R04E12` only to avoid a same-name-different-
netlist collision with R04E10's own files, electrically identical.

## 2. `N_PRECHARGE=1` baseline-match sanity check (done first, per
   BOUNDARY.md Section 2's explicit requirement)

`cases/r04e12_npre_1.cir` was generated, run in LTspice (real LTspice
26.0.2, via `tools/ltspice_runner.sh`, exit code 0, non-empty `.log`
(14,645 bytes) and `.raw` (49,455,144 bytes)), and its `.log` `.meas`
output compared directly against R04E10's own already-committed
`results.csv` row for `i_limit_a=60.0, t_charge_max_ns=50.0`. **Every
single value matches to full printed precision:**

| Quantity | R04E10 committed (`I=60A,T_CHG=50ns`) | R04E12 `N_PRECHARGE=1` | Match? |
|---|---:|---:|---|
| `STATE_FINAL` | `4.0` (`CHARGE3`) | `4.0` (`CHARGE3`) | YES |
| `VOUT_FINAL` | `0.0140987895429` | `0.0140987895429` | YES |
| `VC1_FINAL` | `1.98250246048` | `1.98250246048` | YES |
| `VC2_FINAL` | `0.618512749672` | `0.618512749672` | YES |
| `VC3_FINAL` | `0.0872458964586` | `0.0872458964586` | YES |
| `IL1_MAX` | `60.1728401184` | `60.1728401184` | YES |
| `IL1_MIN` | `-40.7915039062` | `-40.7915039062` | YES |
| `IL2_MAX` | `29.7785701752` | `29.7785701752` | YES |
| `IL2_MIN` | `-52.840713501` | `-52.840713501` | YES |
| `IL3_MAX` | `9.50633716583` | `9.50633716583` | YES |
| `IL3_MIN` | `-17.8017406464` | `-17.8017406464` | YES |
| `IL4_MAX` | `2.35930109024` | `2.35930109024` | YES |
| `IL4_MIN` | `-6.67299890518` | `-6.67299890518` | YES |
| `ICS1_MAX` | `6959.71533203` | `6959.71533203` | YES |
| `ICS1_MIN` | `-1610.13061523` | `-1610.13061523` | YES |
| `ICS2_MAX` | `3961.38696289` | `3961.38696289` | YES |
| `ICS2_MIN` | `-148926.734375` | `-148926.734375` | YES |
| `ICS3_MAX` | `148929.046875` | `148929.046875` | YES |
| `ICS3_MIN` | `-8331.77832031` | `-8331.77832031` | YES |
| Rotations completed | `12` | `12` | YES |

This is not a numerical coincidence -- Section 1 above explains why it is
guaranteed by construction (the generated `.machine`/timer-boolean text
for `N_PRECHARGE=1` was separately confirmed byte-identical to R04E10's
own template, differing only in header comments; see
`scripts/build_r04e12_cases.py`'s own inline verification note). This
match is the required sanity check before trusting the other 4 cells
(BOUNDARY.md Section 2), and it passes cleanly.

## 3. Pilot verification of the precharge-gate construct (BOUNDARY.md
   Section 5, done before trusting the full grid)

`scripts/verify_precharge_gate.py` directly parses the raw `.raw` binary
transient trace (reusing R04E11's own `ltspice_raw_parser.py` unchanged)
and reconstructs the settled (near-integer, tolerance `0.01`) dwell
sequence of `V(state_mon)`, then checks three things against the exact
state-code map `scripts/build_r04e12_cases.py` generates for that
`N_PRECHARGE`: (1) the FIRST admission pass visits every precharge pair in
strictly increasing `k` order before the real `CHARGE1`; (2) no
precharge-mirror state (`PCHG1_*`/`PFREE1_*`) is ever visited again after
the machine's first arrival at the real `CHARGE2` (the gate is a one-time
admission condition, never re-triggering); (3) the exact count of
precharge-role dwells in the settled sequence equals `2*(N_PRECHARGE-1)`.

Run on both `N_PRECHARGE=3` and `N_PRECHARGE=10` (BOUNDARY.md Section 5's
required minimum), directly on the actual `.raw` files from the real
LTspice runs (not a separate throwaway isolation netlist -- unlike
R04E10's pilot, no isolation from another live rule branch was needed
here, since this construct's routing is fully static/hardcoded per cell,
not a runtime race between two conditions):

**`N_PRECHARGE=3`** (`cases/r04e12_npre_3.raw`): expected admission
prefix `['PCHG1_1', 'PFREE1_1', 'PCHG1_2', 'PFREE1_2', 'CHARGE1']`;
**actual: identical**. Zero re-entries into the precharge chain after the
first `CHARGE2` dwell. Precharge dwell count: expected `4`, got `4`.
**All three checks: PASS. Overall: PASS.**

**`N_PRECHARGE=10`** (`cases/r04e12_npre_10.raw`): expected admission
prefix `['PCHG1_1','PFREE1_1','PCHG1_2','PFREE1_2','PCHG1_3','PFREE1_3',
'PCHG1_4','PFREE1_4','PCHG1_5','PFREE1_5','PCHG1_6','PFREE1_6','PCHG1_7',
'PFREE1_7','PCHG1_8','PFREE1_8','PCHG1_9','PFREE1_9','CHARGE1']`; **actual:
identical** (18 states, all visited exactly once, in order). Zero
re-entries into the precharge chain after the first `CHARGE2` dwell.
Precharge dwell count: expected `18`, got `18`. **All three checks: PASS.
Overall: PASS.**

A separate, independent structural check (`scripts/build_r04e12_cases.py`
run standalone, plus an ad-hoc verification pass) confirmed for all 5
generated netlists, before any LTspice run: every declared state has
EXACTLY ONE outgoing `.rule` (no ambiguous/duplicate transitions), every
rule target is a declared state, state codes are contiguous `0..N_states-1`
with no gaps or duplicates, and the charge-role/free-role code sets are
disjoint and perfectly parity-aligned (even=charge-role, odd=free-role) --
confirming the timer-boolean generalization described in Section 1 is
correct for every grid cell, not just the two pilot cells.

**Conclusion: the precharge admission-gate construct does exactly what
BOUNDARY.md Section 2 specifies, confirmed by direct raw-trace inspection,
not merely assumed from the construct's intended logic**, satisfying
BOUNDARY.md Section 5's explicit requirement.

## 4. Parameters actually used

Fixed for every cell (BOUNDARY.md Section 4, R04E10's own best-performing
cell): `Vin=48 V`, `nP=4`, `nM=4`, full four-phase P24 connectivity
(unchanged from R04E9/R04E10), `LPHASE=1.4666667 nH`, `CFLY=3 uF`,
`COUT=4.672 mF`, GS61008T device data (1 HS / 2 parallel LS), true-zero-
energy initial conditions (`ic=0` throughout, `UIC`), `I_LIMIT=60 A`,
`T_CHARGE_MAX=50 ns`, `T_FREEWHEEL_MAX=50 ns`, `TSTOP=20 us`,
`TMAX=50 ps`. Swept: `N_PRECHARGE` in `{1, 3, 5, 10, 20}`, 5 cells, all
run to completion in real LTspice 26.0.2 (batch mode, exit code 0;
`.log` files `14.6-14.9 KB`, `.raw` files `49.3-49.5 MB` -- all 5 cells,
confirming completed `TSTOP=20 us` transient runs, none truncated).

## 5. The 5-cell grid

Same table columns as R04E10's own `RESULTS.md` Section 3, plus
`N_PRECHARGE` and a `Handoff?` column.

| `I_LIMIT` (A) | `N_PRECHARGE` | Final state | Rotations | `Vout` final (V) | `VC1` final (V) | `VC2` final (V) | `VC3` final (V) | `IL1_max` (A) | Handoff? |
|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 60 | 1  | CHARGE3 (code 4)  | 12 | 0.014099 | 1.98250 | 0.61851  | 0.08725  | 60.173 | NO |
| 60 | 3  | CHARGE2 (code 6)  | 12 | 0.014484 | 1.87374 | 0.71581  | 0.10664  | 60.173 | NO |
| 60 | 5  | CHARGE3 (code 12) | 13 | 0.015659 | 2.23965 | 0.50609  | 0.03353  | 60.175 | NO |
| 60 | 10 | FREE1 (code 19)   | 13 | 0.016323 | 2.02011 | 0.62161  | 0.10401  | 60.178 | NO |
| 60 | 20 | CHARGE3 (code 42) | 14 | 0.019730 | 2.24073 | 0.85290  | **-0.16987** | 60.178 | NO |

Targets for reference: `Vout=1 V`, `VC1=36 V`, `VC2=24 V`, `VC3=12 V`.
Full numeric detail (min currents, `ICS1-3` values, all five trajectory
checkpoints, every per-rotation measurement, trend statistics) is in
`results.csv`/`results.json`, generated directly from each cell's `.log`
by `scripts/analyze_r04e12_grid.py` (adapted from R04E10's own
`analyze_b06_...py`, same parsing logic, extended with the per-cell
state-code map Section 1 describes).

Every `IL1-4` value in the grid stays comfortably inside the `+/-250 A`
safety bound (BOUNDARY.md Section 9) -- worst case `IL1_max=60.178 A`
(`N_PRECHARGE=10/20`), `24%` of the bound, essentially unchanged from
R04E10's own `60.17 A` figure. `IL2_max` shows a small, real increase at
`N_PRECHARGE=20` (`34.27 A` vs `~29.7-30.0 A` at every other
`N_PRECHARGE`), still `14%` of the safety bound. **No
`PHYSICAL_BOUNDARY_FAIL` in any cell.**

## 6. Does `Vout` improve with `N_PRECHARGE`? Yes, monotonically and
   unambiguously

`Vout_final` rises strictly monotonically across the whole swept range:
`0.014099 -> 0.014484 -> 0.015659 -> 0.016323 -> 0.019730 V` at
`N_PRECHARGE=1,3,5,10,20` -- a `39.9%` increase from baseline to
`N_PRECHARGE=20`. This is the single cleanest, most unambiguous positive
result in this grid: every one of the 4 non-baseline cells beats the
baseline, with no reversal at any tested point. Rotation count also rises
mildly and monotonically (`12,12,13,13,14`), and `T_ROT1` (time of the
first completed FULL four-phase rotation, i.e. after the precharge stage
finishes) is NOT monotonically delayed by the added precharge passes
(`3.755, 3.858, 3.500, 3.803, 4.188 us` at `N_PRECHARGE=1,3,5,10,20` --
`N_PRECHARGE=5` actually completes its first rotation EARLIER than the
baseline) -- confirming BOUNDARY.md Section 4's own expectation that the
retry/chatter dynamic (Section 8 below), not the added precharge passes
themselves, dominates per-rotation timing variability; the precharge
stage's own worst-case added time (`<=19*100 ns~=1.9 us` at
`N_PRECHARGE=20`) does not consume a problematic fraction of the `20 us`
window.

## 7. Does `VC2` improve with `N_PRECHARGE`? No -- a non-monotonic, mixed
   result (the question BOUNDARY.md Section 7 poses directly)

**`VC2_final` relative to the `N_PRECHARGE=1` baseline (`0.618513 V`):**

| `N_PRECHARGE` | `VC2_final` (V) | vs. baseline | Direction |
|---:|---:|---:|---|
| 1 (baseline) | 0.618513 | -- | -- |
| 3  | 0.715811 | **+0.097 (+15.7%)** | improves |
| 5  | 0.506090 | **-0.112 (-18.2%)** | regresses |
| 10 | 0.621613 | +0.003 (+0.5%) | essentially flat |
| 20 | 0.852904 | **+0.234 (+37.9%)** | improves, best of grid |

This is NOT a clean "more precharge always helps `VC2`" result:
`N_PRECHARGE=5` is measurably WORSE than the baseline, `N_PRECHARGE=10` is
statistically indistinguishable from the baseline, and only
`N_PRECHARGE=3` and `N_PRECHARGE=20` show genuine improvement --
satisfying BOUNDARY.md Section 8's `CONTROLLER_GUARD_PASS`-with-
improvement bar (at least one of `{5,10,20}` shows a measurably better
`VC2` trajectory than the baseline -- `N_PRECHARGE=20` does, clearly) but
NOT supporting a general claim that precharging phase 1 more helps `VC2`
monotonically or reliably. The per-rotation `VC2` TREND (not just the
final value) is positive (net increasing) in all 5 cells including the
baseline, so this experiment does not reproduce R04E10's own worst finding
(3 of R04E10's 6 multi-rotation cells had `VC2` trending in the WRONG
direction entirely, BOUNDARY.md Section 1) -- but the FINAL VALUE
comparison above shows the precharge stage's effect on how far `VC2` gets
is genuinely non-monotonic in `N_PRECHARGE`, not a smooth improvement
curve.

**A new trade-off, not present in R04E10's own grid**: `N_PRECHARGE=20` --
the cell with the single BEST `VC2` value in this entire grid -- has the
single WORST `VC3` value: `-0.16987 V`, the ONLY negative final value for
any state variable anywhere in this grid (baseline `VC3_final=+0.0872 V`;
every other cell's `VC3_final` is also positive, `0.034-0.107 V`).
Direct inspection of `VC3`'s per-rotation trend at `N_PRECHARGE=20`
(`results.json`) shows it net-increases only slightly
(`+0.0009 V` over 14 rotations, `first=0.0326`, `last=0.0335`) while the
FINAL single-point value at `t=20 us` sits well below even its own
trend's minimum during the run -- consistent with the same retry/chatter-
driven volatility (Section 8) landing this cell's final sample on a
transient dip, not a sustained negative trend. This is reported as an
observed final-value trade-off, not a claim that `VC3` is systematically
driven negative by higher `N_PRECHARGE` (the per-rotation trend data does
not support that stronger claim).

**`VC1` also does not improve monotonically**: `1.983 -> 1.874 (dip) ->
2.240 -> 2.020 -> 2.241 V` -- net higher at large `N_PRECHARGE` than
baseline, but with a real dip at `N_PRECHARGE=3` and a non-monotonic step
between `N_PRECHARGE=5` and `10`.

**Summary answer to BOUNDARY.md Section 7's question**: front-loading
charge onto `C1` via a repeated-admission precharge stage measurably helps
`VC2` at SOME tested `N_PRECHARGE` values (`3`, and especially `20`) but
not at others (`5`, `10`), and the one clearly-positive `VC2` result
(`N_PRECHARGE=20`) comes with a new `VC3` trade-off not seen at any other
tested value. `Vout` is the only axis that improves cleanly and
monotonically. This is reported exactly as observed, per Ground Rule 7 --
not smoothed into a single "precharge helps" or "precharge doesn't help"
verdict.

## 8. Recurrence of the R04E10/R04E11-diagnosed retry/chatter dynamic and
   `ICS1-3` artifact

BOUNDARY.md Section 1 explicitly anticipated that reusing R04E10's own
`CHARGE_k`/`FREE_k` current-limit-OR-timeout construct unchanged means the
same retry/chatter episode and `ICS1-3` artifact "may recur here too,"
and that this is an already-diagnosed phenomenon (R04E11), not a new
mystery. **It recurs in every one of the 5 cells, at essentially uniform
severity regardless of `N_PRECHARGE`:**

`scripts/count_reversals.py` (a small generalization of R04E11's own
`state_sequence.py` reversal count, correcting its hardcoded `7->0`
wraparound test to this experiment's own per-cell-shifted `FREE4->CHARGE1`
wraparound codes) finds, over the full `20 us` run of each cell:

| `N_PRECHARGE` | Settled dwell transitions | Reversals | Reversal rate |
|---:|---:|---:|---:|
| 1  | 409 | 89 | 21.8% |
| 3  | 411 | 89 | 21.7% |
| 5  | 414 | 85 | 20.6% |
| 10 | 417 | 84 | 20.2% |
| 20 | 433 | 83 | 19.2% |

All five rates sit in a tight `19.2-21.8%` band, closely matching R04E10's
own reported `19%` figure (113/595) for its representative
`I_LIMIT=30 A/T_CHARGE_MAX=20 ns` cell -- **the same phenomenon, not a new
or worsened one, and (contrary to what might have been expected) NOT
concentrated or amplified specifically at `N_PRECHARGE=20`** -- if
anything the reversal rate drifts slightly DOWN as `N_PRECHARGE` grows in
this grid, though the small range (`19.2%` to `21.8%`) does not support
reading this as a strong trend either way. No cell's retry/chatter episode
prevented rotations from completing (unlike R04E10's own
`T_CHARGE_MAX=5 ns` cells) -- every R04E12 cell completes `12-14`
rotations.

The coincident `ICS1-3` `.meas` artifact (`analyze_r04e12_grid.py`'s own
`>1000 A` flag, same threshold R04E10/R04E11 used) is present in every
cell: `ICS2_MIN`/`ICS3_MAX` reach `~93-149 kA` magnitude in 4 of the 5
cells (`N_PRECHARGE=1,3,5,20`), the same order of magnitude as R04E10's
own worst cells. **`N_PRECHARGE=10` is a partial, incidental exception**:
its `ICS3_MAX=63.7 A` falls BELOW the `1000 A` flag threshold (the only
unflagged `ICS` branch anywhere in this grid), while its `ICS2_MIN`
(`-7926.9 A`) and `ICS3_MIN` (`-6557.5 A`) are far smaller in magnitude
than the `~90-150 kA` seen elsewhere -- consistent with R04E10/R04E11's
own characterization of this artifact's magnitude as an unpredictable
function of exactly where in the run a difficult solver-retry episode
happens to occur, not a smooth function of any single swept parameter.
**Per BOUNDARY.md Section 1/9: `IL1-4` (Section 5 above) are the
trustworthy peak-current indicator in every cell; `ICS1-3` magnitudes are
flagged, not reported as physical currents**, exactly as R04E10/R04E11
established.

## 9. What this experiment establishes

- The compile-time-unrolled precharge admission-gate construct
  (Section 1) works exactly as BOUNDARY.md Section 2 specifies, confirmed
  by direct raw-trace inspection at two different `N_PRECHARGE` values
  (Section 3), and the `N_PRECHARGE=1` baseline is confirmed identical to
  R04E10's own committed result to full printed precision (Section 2).
- `Vout` improves monotonically and substantially (`+40%` at
  `N_PRECHARGE=20` vs. baseline) as more precharge passes are added --
  the clearest positive result of this experiment.
- `VC2` does NOT improve monotonically with `N_PRECHARGE`; it is better at
  `N_PRECHARGE in {3,20}`, worse at `N_PRECHARGE=5`, flat at
  `N_PRECHARGE=10`. A precharge-admission-gate stage of this kind can help
  `VC2`, but not reliably or monotonically at the 5 tested points.
- A new trade-off was found at the single best-`VC2` cell
  (`N_PRECHARGE=20`): `VC3_final` goes negative, the only negative
  state-variable final value in this grid.
- The R04E10/R04E11-diagnosed retry/chatter dynamic and its coincident
  `ICS1-3` artifact recur in every cell at essentially uniform severity
  (`19-22%` reversal rate), confirming this is a property of the reused
  `CHARGE_k`/`FREE_k` construct itself, not something the precharge stage
  either causes or fixes.
- No cell approaches the handoff condition; every cell remains
  `CONTROLLER_GUARD_PASS`. `IL1-4` stay safely bounded in every cell
  (worst case `24%` of the `+/-250 A` limit).

## 10. What this experiment cannot prove

- It does not close the handoff gap even at its best cell
  (`N_PRECHARGE=20`'s `Vout=0.0197 V` is still `98%` short of the `1 V`
  target) -- R04E10's own Section 10 finding (this whole inductor-mediated
  family converges far more slowly per-cycle than R04E7/E8's switch-only
  mechanism) is a separate, structural limitation this experiment does not
  address.
- It does not validate `Cout=4.672 mF`, still an unconfirmed inherited
  value.
- It does not build or exercise the handoff into the existing strict
  steady-state controller -- out of scope, same as R04E9/R04E10/R04E11.
- A result here is specific to this exact fixed-parameter combination
  (`I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`, `T_FREEWHEEL_MAX=50 ns`,
  `CFLY=3 uF`, `COUT=4.672 mF`); it must not be read as a general
  statement about precharge-admission-gating independent of these values
  (BOUNDARY.md Section 10).
- It does not establish that `N_PRECHARGE=20` (or any tested value) is
  "optimal" -- the swept axis is `SENSITIVITY_ONLY`, an order-of-magnitude
  first exploration, and the non-monotonic `VC2`/`VC1` results (Section 7)
  mean a finer sweep between the tested points could show different
  behavior, untested here.
- It does not evaluate R04E9 Section 11's options (a) (direct topology
  change) or (b) (passive precharge circuit) -- those remain separate,
  unstarted candidate directions.
- The `ICS1-3` artifact and its underlying solver-stiffness cause remain
  exactly as undiagnosed-at-the-LTspice-internals-level as R04E11 left
  them; this experiment adds five more data points confirming the same
  phenomenon recurs, not a further diagnosis of its root cause.

## 11. Provenance and classification (BOUNDARY.md Section 6)

| Value | Source | Category |
|---|---|---|
| Precharge admission-gate construct (compile-time-unrolled state-pair chain, Section 1) | This experiment's single new mechanism, implementing R04E9 `RESULTS.md` Section 11 option (c) / this experiment's own `BOUNDARY.md` Section 2 verbatim in intent, with an explicitly-documented implementation-detail choice (Section 1) made within `BOUNDARY.md`'s own stated latitude ("implementation detail is yours to design") | `NUMERICAL_IDEALIZATION`/engineering construct -- no physical counterpart, a controller/sequencing choice |
| `N_PRECHARGE` swept values `{1, 3, 5, 10, 20}` | New for this experiment; `1` is the R04E10-equivalent baseline (confirmed identical, Section 2), `{3,5,10,20}` are an order-of-magnitude first exploration | `SENSITIVITY_ONLY` |
| `I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`, `T_FREEWHEEL_MAX=50 ns` | R04E10's own best-performing cell, fixed here rather than re-swept | inherited, `SENSITIVITY_ONLY` (R04E10 provenance) |
| `scripts/ltspice_raw_parser.py`, `state_sequence.py`, `find_extremum.py` | Reused verbatim (unmodified) from R04E11's own committed, already-validated diagnostic tooling | Diagnostic tooling, not simulation input |
| `scripts/verify_precharge_gate.py`, `scripts/count_reversals.py` | New for this experiment, built on top of the reused `ltspice_raw_parser.py` | Diagnostic tooling, not simulation input |
| Every value carried over from R04E9/R04E10 (`Vin`, `nP`, `nM`, topology, `LPHASE`, `CFLY`, `COUT`, GS61008T data, handoff tolerance bands, `CHARGE_k`/`FREE_k` exit rules) | See R04E10 `BOUNDARY.md` Section 6 | unchanged |

**No new paper-sourced, cross-paper, or external-device data is
introduced.** Nothing here bears on any `P24_EXPLICIT` or
`P25_SUPPLEMENT` boundary.

**Overall grade**: `CONTROLLER_GUARD_PASS` (5/5 cells: rotations complete,
currents stay bounded, handoff never reached in any cell), with a
**mixed, non-monotonic improvement finding** on the specific question
BOUNDARY.md Section 7 poses (`VC2`) -- `Vout` improves cleanly and
monotonically, `VC2`/`VC1` improve at some but not all tested
`N_PRECHARGE` values, and a new `VC3` trade-off appears at the single best
`VC2` cell. `SENSITIVITY_ONLY` overall (BOUNDARY.md Section 9's failure
condition "no measurable improvement... a legitimate, informative negative
result" does NOT apply cleanly either, since `N_PRECHARGE=20` DOES show
measurable `VC2` improvement -- the honest label for this result is
mixed/non-monotonic, not a clean pass or fail).

## 12. Files produced

- `scripts/build_r04e12_cases.py` -- generates the 5 case netlists from
  R04E10's own committed `r04e10_ilimit_60a_tchg_50ns.cir` template (see
  its own module docstring for the full construct design rationale).
- `scripts/verify_precharge_gate.py` -- pilot verification tool (Section
  3): confirms the precharge admission order, one-time-gating, and dwell
  count directly from a cell's `.raw` file.
- `scripts/count_reversals.py` -- generalizes R04E11's own reversal count
  to this experiment's per-cell-shifted state numbering (Section 8).
- `scripts/analyze_r04e12_grid.py` -- parses all 5 cells' `.log` files
  into `results.csv`/`results.json` (adapted from R04E10's own
  `analyze_b06_...py`).
- `scripts/ltspice_raw_parser.py`, `state_sequence.py`, `find_extremum.py`
  -- reused verbatim from R04E11.
- `cases/r04e12_npre_{1,3,5,10,20}.cir` -- the 5 committed grid netlists.
- `results.csv`/`results.json` -- full grid results, same format as
  R04E10's own.

`.raw`/`.log`/`.db` outputs from all 5 LTspice runs are gitignored
(`*.raw`, `*.log`, `*.db`, this repository's existing convention -- same
as R04E10/R04E11's own `cases/` directories, which contain only `.cir`
files), consistent with the committed netlists being fully sufficient to
reproduce every number in this document by re-running them.
