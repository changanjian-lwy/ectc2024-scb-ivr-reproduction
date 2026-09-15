# R04E11 result - root cause of the CHARGE/FREE reversal and ICS artifact

## Outcome, stated first

**Diagnosis complete, `CONTROLLER_GUARD_PASS`-style partial success; no
fix found.** Direct, fine-time-resolution raw-trace instrumentation of
R04E10's own `I_LIMIT=30 A`/`T_CHARGE_MAX=20 ns` cell (BOUNDARY.md's
primary diagnostic target) shows the CHARGE/FREE reversal is a genuine,
continuous, monotonic sweep of the raw `.machine` internal state variable
(exposed via `V(state_mon)`) through several half-integer bucket
boundaries within a few picoseconds -- **not** a race between this
construct's own two reset-gate booleans, which were directly checked and
found to be perfect, always-consistent complements of `V(state_mon)` at
every one of 231 sampled rows across two independent reversal episodes in
two different grid cells (zero conflicts). A minimal, well-motivated
candidate fix -- adding hysteresis to the zero-hysteresis reset-switch
comparators that gate the two per-state timers -- was built and run as a
controlled isolation test on the exact same cell. **The fix produced a
bit-identical trace to the unmodified baseline** (same row, same
15-significant-figure timestamp, same `V(state_mon)` value, same final
state/voltages/rotation count), directly refuting the hypothesis that
this project's own gate/switch logic is the cause. The reversal is
therefore attributed to LTspice's own `.machine`/`.rule` event-resolution
behavior during genuinely stiff, sub-picosecond-timestep solver-retry
episodes -- the same episodes that separately produce the `ICS1-3`
numerical artifact -- a limitation of the underlying simulation primitive
in this stiff corner of its own state space, not of this project's
constructed B-source logic. Per Ground Rule 7 and this experiment's own
`BOUNDARY.md` Section 2, **no fix is applied and the 9-cell grid is not
re-run** (`BOUNDARY.md` Section 3/6 conditions a grid re-run on a fix
being found; none changed the outcome). A secondary cross-check on the
`T_CHARGE_MAX=5 ns` total-stall cell (same `I_LIMIT=30 A`) confirms the
same phenomena, more severely (273 reversals across the full `20 us`
non-escaping run vs. 113 in the escaping `T_CHARGE_MAX=20 ns` cell), and
the same zero-conflict reset-gate consistency.

One further, unexpected refinement of R04E10's own record: the specific
`t=19.275 us` instant R04E10's `BOUNDARY.md` Section 5b cited as "one
concrete reversal event" is, on direct inspection, **not itself a
reversal** -- at that exact row the machine is mid-transition FREE2(3) ->
CHARGE3(4), moving cleanly *forward*, and goes on to complete the
rotation normally 201 ns later. The `ICS2`/`ICS3` excursion and the
non-integer `V(state_mon)=3.217` R04E10 found there are real and directly
reproduced here, but they coincide with a clean forward transition, not a
backward one. The genuine reversal episodes are a related but temporally
distinct phenomenon, concentrated earlier in the same run (Section 4
below).

## 1. What was instrumented, and why

R04E10's own committed netlists never saved `V(reset_gate)`,
`V(reset_gate_chg)`, `V(timer)`, or `V(timer_chg)` -- only
`V(state_mon)`, `V(out)`, `V(vc1-3_mon)`, `I(L1-4)`, `I(CS1-3)`, and the
flag nodes. This experiment's primary diagnostic instrument
(`scripts/build_r04e11_diagnostic_cases.py`) makes byte-identical copies
of two of R04E10's own already-committed, already-run case netlists --

- `r04e11_diag_i30_tchg20ns_instrumented.cir`, from
  `R04E10_.../cases/r04e10_ilimit_30a_tchg_20ns.cir` (the primary target
  `BOUNDARY.md` Section 3 names: `I_LIMIT=30 A`, `T_CHARGE_MAX=20 ns`,
  known reversal/retry activity and the `t~19.275 us` `ICS` excursion)
- `r04e11_diag_i30_tchg5ns_instrumented.cir`, from
  `.../r04e10_ilimit_30a_tchg_5ns.cir` (the secondary target: one of the
  three `T_CHARGE_MAX=5 ns` total-stall cells, the reversal dynamic in
  its most extreme, never-escaping form)

-- with exactly one change to each: the `.save` line gains
`V(reset_gate) V(reset_gate_chg) V(timer) V(timer_chg)`. `.save` only
controls which nodes LTspice writes to the `.raw` file; it adds no
circuit element, changes no parameter, and cannot alter the solver's own
timestep choices, so this is pure additional observation, not a circuit
or mechanism change (`BOUNDARY.md` Section 4 untouched). Both runs were
executed in this environment via `tools/ltspice_runner.sh` (LTspice
26.0.2 for MacOS, real LTspice, not a stub) and reproduced R04E10's own
`.meas` results for these two cells EXACTLY (`STATE_FINAL`, `VOUT_FINAL`,
`VC1-3_FINAL`, rotation counts and timestamps, `ICS1-3_MAX/MIN` all
match R04E10's committed `results.csv` row for `I_LIMIT=30/T_CHARGE_MAX=
{20,5}` to full printed precision), confirming the added `.save` line
changed nothing about the simulated dynamics.

A custom LTspice `.raw` binary parser was written for this experiment
(`scripts/ltspice_raw_parser.py`) since no existing parser was present in
this repository; its binary-layout assumptions (UTF-16LE header, 8-byte
double time + 4-byte float per other variable) were verified directly
against the header this project's own LTspice 26.0.2 build actually
writes, and cross-checked by confirming `(file_size - header_length) ==
no_points * record_bytes` exactly for both instrumented `.raw` files
(`~67.4 MB`/702,200 points and `~71.1 MB` respectively). Two further
analysis scripts (`scripts/find_extremum.py`,
`scripts/state_sequence.py`) locate a named trace's global MAX/MIN row
and reconstruct the settled (near-integer) state-dwell sequence over
time, respectively -- both used below.

## 2. Locating R04E10's own cited `t=19.275 us` event exactly

`scripts/find_extremum.py` located the global minimum of `I(XMOD:CS2)`
over the full `20 us` run directly (not estimated): **row 654331,
`t=1.9275359627109638e-05` s (`19.275359627...  us`), `I(CS2)=
-233,551.6875 A`, `I(CS3)=+233,541.40625 A`, `V(state_mon)=
3.217076301574707`.** This matches R04E10's own cited magnitude class
(`~233 kA`, `BOUNDARY.md` Section 3) and its cited `V(state_mon)=3.217`
value to 4 significant figures, confirming this is the same event R04E10
found from aggregate `.meas` output, now localized to an exact row.

Inspecting the 15 rows immediately before and after: rows 654316-654331
span **less than 10^-16 s** of simulated time while `V(state_mon)`
creeps from `3.217021942138672` to `3.217076301574707` and `I(L2)`,
`I(L3)` stay smooth and small (tens of amps) -- the same "many
consecutive rows at an effectively identical timestamp" fingerprint
R04E10 already used to diagnose this as a solver-convergence retry
artifact, now confirmed directly at the row level, not inferred from
aggregate output.

**Critically, following `V(state_mon)` forward from this exact row shows
it does NOT reverse here.** Over the next ~450 rows (about 100 ps of
simulated time) it rises smoothly and monotonically: `3.217 -> 3.499999...
[reset_gate: 0->5, reset_gate_chg: 5->0, exactly at the 3.5 boundary] ->
3.9999... -> 4.0` exactly at `t=1.9275360075392277e-05`, then continues
rising cleanly through `4 -> 5` over the following ~120 ns, landing
`V(state_mon)=5` (FREE3) by `t~19.2754 us`. The machine's 3rd rotation
completes cleanly 201 ns later, at `t=1.94758365279e-05`
(`T_ROT3`, matching R04E10's own committed value exactly). **This
specific, widely-cited timestamp is therefore an `ICS`-artifact-plus-
clean-forward-transition, not a reversal event.** This is reported as a
direct correction to how this one timestamp was characterized in
R04E10's `BOUNDARY.md` Section 5b/this experiment's own `BOUNDARY.md`
Section 3 -- the underlying `ICS` finding and the `3.217` value are both
confirmed correct; only the "reversal event" label attached to this
specific instant is not supported by direct inspection.

## 3. Hypothesis 1 (two reset gates disagree): tested directly, refuted

The two reset-gate B-sources (`BRESET_GATE` -> `reset_gate`,
`BRESET_GATE2` -> `reset_gate_chg`) are complementary boolean functions
of the SAME node, `V(state_mon)`: `reset_gate` is high exactly when
`state_mon` sits in a `CHARGE_k` half-integer bucket, `reset_gate_chg`
exactly when it sits in a `FREE_k` bucket. The hypothesis this
experiment's own `BOUNDARY.md` Section 2 explicitly flagged as
"plausible... not something to assume true without evidence" was that
these two gates might briefly disagree during a mid-transition,
non-integer `state_mon` value, corrupting one timer's reset state.

**Tested directly across every row of two independent reversal/artifact
windows:**

- The 151-row window spanning the `t=19.275 us` `ICS` episode (Section 2
  above): `reset_gate` and `reset_gate_chg` are `(0,5)` or `(5,0)` at
  every single row -- **0/151 conflicts** (never simultaneously high,
  never simultaneously low).
- An 80-row window inside the `T_CHARGE_MAX=5 ns` secondary cell's own
  reversal activity (Section 6 below): again **0/80 conflicts**.

**This directly refutes the two-gate-race hypothesis.** The gates track
`V(state_mon)` perfectly consistently, in both tested cells, throughout
the difficult episodes. Whatever is corrupting the machine's state, it is
not a disagreement between these two derived booleans.

## 4. Finding the actual reversal episodes, and their exact period

`scripts/state_sequence.py` reconstructs the settled (near-integer,
tolerance `0.01`) state-dwell sequence over the whole run and flags every
place the sequence goes backward (excluding the legitimate `FREE4(7) ->
CHARGE1(0)` wraparound). In the primary (`T_CHARGE_MAX=20 ns`) cell, of
**595 total settled-state dwell transitions** over the run, **113 are
reversals** (19%); in the secondary, permanently-stalled
(`T_CHARGE_MAX=5 ns`) cell, of **721 dwell transitions, 273 are
reversals** (38% -- roughly double the fraction, consistent with that
cell never escaping within the `20 us` window).

Isolating one clean, uninterrupted run of consecutive `CHARGE3(4) ->
FREE1(1)` reversals early in the primary cell (before the pattern's
character changes) gives an **exact, directly-measured period of
143.14 ns** (14 consecutive intervals, all identical to 4 significant
figures: `t=363.86, 507.00, 650.14, 793.28, 936.42, 1079.56, ... ns`,
each `+143.14 ns`) -- matching R04E10's own reported "~143 ns retry
period" (`BOUNDARY.md` Section 5b) to within its own stated precision, now
confirmed as an exact, not approximate, figure. A later, different
pattern in the same cell (`CHARGE4(6) -> FREE1(1)`, 25 consecutive
intervals from `t=4.684` to `10.052 us`) has an equally exact, distinct
period of **214.71 ns**. Both periods recur too precisely (to 4+
significant figures, dozens of times) to be solver noise -- they are a
real, reproducible characteristic of this construct's own retry dynamic.

## 5. Picosecond-resolution trace of one reversal: the state variable
   itself sweeps backward, continuously

Direct row-by-row inspection of one `CHARGE3(4) -> FREE1(1)` episode
(rows 43503-43654, `t=936.4129 ns` to `936.4290 ns`, ~16 ps total) shows:

- `V(state_mon)` decreases **continuously and monotonically** from
  `3.9999995` down through `3.4999995`, `2.4999998`, to `1.4999998` --
  not a discontinuous jump, a genuine smooth sweep.
- At each half-integer crossing (`3.5`, `2.5`, `1.5`), `reset_gate` and
  `reset_gate_chg` flip in perfect, immediate, correct correspondence
  with the crossing (e.g. at row+793, `t=936.4129 ns`,
  `V(state_mon)=3.499999523`: `reset_gate: 5.0->0.0`, `reset_gate_chg:
  0.0->5.0`, exactly the flip this construct's own B-source formulas
  dictate for a state value crossing from the `CHARGE3` bucket into the
  `FREE2` bucket). This is the SAME direct confirmation as Section 3:
  this project's own gate logic is behaving exactly as designed given
  whatever value `V(state_mon)` has at each instant.
- `I(L2)`/`I(L3)` during this window are small (`~0.1-0.5 A`) and of
  opposite sign -- consistent with residual flying-capacitor-branch
  current, not a large physical event; the anomaly is confined to the
  state variable, not a large physical current excursion at this
  specific moment (unlike the `t=19.275 us` `ICS` spike, Section 2).
- After landing at `state=1` (`FREE1`), the machine treats this as a
  fully committed state: `reset_gate_chg` stays high, `timer` (the
  freewheel timer) begins counting fresh from near-zero, and the machine
  dwells the commanded `T_FREEWHEEL_MAX` before its next natural
  transition -- confirming the landing is a genuine internal state
  commit, not merely a transient display glitch in the `state_mon`
  output node.

**Conclusion of the direct trace evidence:** the anomaly is not in this
project's own reset-gate/switch construct (shown consistent and correct
at every sampled instant in two independent episodes) but in the raw
internal `.machine` state variable itself, which is observed taking a
continuous, multi-integer-spanning, monotonically decreasing excursion
during a genuinely stiff, sub-picosecond-timestep solver episode -- the
same class of episode (many closely-spaced or identical-timestamp rows)
that separately produces the `ICS1-3` artifact (Section 2). This is
consistent with a limitation of how LTspice's `.machine`/`.rule` event
resolution behaves when the solver is forced into extremely fine
timesteps by a difficult analog transient elsewhere in the same coupled
circuit (here, very likely the near-simultaneous availability of both
the current-limit and timeout exit branches this experiment's parent,
R04E10, added) -- not a defect this project's own B-source/switch
constructs can be shown to cause or control.

## 6. Fix-hypothesis test: reset-switch hysteresis -- built, run, refuted

The most direct, well-motivated candidate mechanism consistent with
Sections 3-5's own evidence would be that the reset switches
(`SRESET`/`SRESET_CHG`, model `SWRESET`, `Vt=2.5 V`, **`Vh=0` -- zero
hysteresis**, sitting exactly on the SAME half-integer state-bucket
boundaries the `.machine` itself uses) chatter or re-trigger during the
difficult episode in a way that could, in principle, corrupt
`timer`/`timer_chg` and feed back into the very `.rule` conditions that
decide the next state. This was TESTED, not assumed:
`scripts/build_r04e11_fix_test_case.py` makes exactly ONE change to the
primary instrumented netlist -- `.model SWRESET SW(Ron=... Roff=1Meg
Vt=2.5 Vh=0)` -> `Vh=1` (turn-on/off thresholds at `3.0 V`/`2.0 V`
instead of a single `2.5 V` point) -- and nothing else
(`r04e11_fixtest_i30_tchg20ns_hysteresis.cir`). Because
`reset_gate`/`reset_gate_chg` swing cleanly between `0 V` and `5 V`
outside the diagnosed difficult regime, `Vh=1` cannot affect any
already-clean transition; it can only change behavior in exactly the
regime under test.

**Result: the fix-test run is bit-identical to the unmodified baseline.**
Both were run to completion in LTspice (`20 us`, `TMAX=50 ps`,
identical `.options`). Every checked quantity matches to full printed
precision: `STATE_FINAL=5`, `VOUT_FINAL=0.00236504548229`,
`VC1_FINAL=0.539655029774`, `VC2_FINAL=-0.430057376623`,
`VC3_FINAL=0.179109916091`, 4 rotations at the identical timestamps
(`T_ROT1..4`), and the `ICS2` global extremum located at the EXACT SAME
row (654331), EXACT SAME timestamp
(`1.9275359627109638e-05`), and EXACT SAME `V(state_mon)`
(`3.217076301574707`) as the unmodified run. **This directly refutes the
reset-switch-hysteresis hypothesis**: giving the reset comparators a
dead band did not change a single measured or raw-trace quantity,
confirming the reset switches were not chattering/re-triggering in a way
that mattered -- consistent with Section 3's own finding that they were
already behaving perfectly consistently. The root cause therefore lies
outside anything this experiment's own constructed switch/comparator
logic can reach.

No further fix candidates were attempted. Per `BOUNDARY.md` Section 2/7
and Ground Rule 7, a negative fix-test result is reported plainly, not
retried with a different parameter value in search of an accidental
improvement, and the 9-cell grid is not re-run (`BOUNDARY.md` Section
3/6 conditions a full grid re-run explicitly on a fix being found that
actually changes the outcome).

## 7. Secondary target cross-check (`T_CHARGE_MAX=5 ns`, the total-stall
   cell): same phenomena, more severe

The instrumented `I_LIMIT=30 A`/`T_CHARGE_MAX=5 ns` cell (one of
R04E10's three permanently-stalled cells, 0 rotations in `20 us`) was
run and reproduces R04E10's own committed result exactly (`STATE_FINAL=
FREE3`, `VOUT_FINAL=6.067e-4 V`, `VC1=0.09125`, `VC2=-0.03413`,
`VC3=-0.03409`). The settled-state scan finds **273 reversals across the
FULL `20 us` run** (vs. 113 confined mostly to the first `18.86 us` in
the escaping `T_CHARGE_MAX=20 ns` cell) -- directly confirming that this
cell's total failure to ever complete a rotation is the SAME reversal
dynamic, persisting for the entire run rather than eventually escaping.
The two-reset-gate consistency check was repeated on an 80-row window
inside this cell's own reversal activity: again **0/80 conflicts**,
confirming Section 3's finding generalizes across cells, not an artifact
of the one primary cell examined in detail.

## 8. What this establishes

- **The originally-hypothesized race between `BRESET_GATE`/
  `BRESET_GATE2`** (two reset-gate booleans briefly disagreeing during a
  mid-transition `state_mon` value) **is directly refuted** by 231
  sampled rows across two independent episodes in two different cells,
  zero conflicts.
- **The reset-switch's zero hysteresis is directly refuted as the fix**
  by a controlled isolation test producing a bit-identical trace.
- **The reversal is a genuine, continuous, monotonic, multi-integer-step
  decrease of the raw `.machine` state variable itself** (not a display
  artifact, not a downstream logic bug), occurring during the same class
  of stiff, sub-picosecond-timestep solver episode that separately
  produces the `ICS1-3` current-magnitude artifact -- both are
  manifestations of the same underlying solver difficulty, not two
  independent problems.
- **The specific `t=19.275 us` timestamp R04E10's own `BOUNDARY.md`
  cited as "one concrete reversal event" is, on direct inspection, a
  clean forward transition with a coincident `ICS` artifact, not a
  reversal** -- a direct correction to that characterization, with the
  underlying `ICS`/non-integer-`state_mon` finding itself fully
  reproduced and confirmed.
- **Exact, reproducible retry periods** (`143.14 ns`, `214.71 ns`) are
  now available in place of R04E10's own "~143 ns" approximation.
- Per `BOUNDARY.md` Section 6's own acceptance bar, this is a
  `CONTROLLER_GUARD_PASS`-style **partial success**: the reversal
  mechanism is narrowed to a specific construct element -- or rather, to
  the exclusion of specific construct elements (both hypothesized causes
  within this project's own B-source/switch logic are directly refuted)
  -- localizing the true cause to the underlying `.machine` simulation
  primitive's own behavior in this stiff regime, without achieving full
  isolation to one signal this project's own netlist can control and
  fix. This is reported honestly as the outcome the evidence supports,
  per Ground Rule 7 -- not forced further.

## 9. What this experiment cannot prove / does not establish

- It does **not** identify a working fix -- the one candidate tested
  (reset-switch hysteresis) is directly shown ineffective. No other
  candidate was tried; a genuinely different candidate (e.g. changing
  the `.machine` resolution parameter from `1p`, or restructuring how
  `T_CHARGE_MAX`/`T_FREEWHEEL_MAX`'s two OR-branches interact) was
  **not** attempted, since `BOUNDARY.md` Section 2 requires any fix to be
  "clean, minimal, single-conceptual" and no such candidate was
  identified by this diagnosis; inventing and testing further mechanism
  changes is explicitly out of this experiment's scope (that would be a
  new mechanism, not a diagnosis).
- It does **not** prove the state-variable excursion is unfixable in
  principle -- only that this experiment's one directly-motivated,
  minimal candidate does not fix it, and that this project's own gate
  logic is not the proximate cause.
- It does **not** change any of R04E10's own committed 9-cell grid
  results, `results.csv`/`results.json`, or grades -- those remain
  exactly as R04E10 reported them. This experiment adds diagnostic depth
  to two of those nine cells; it does not supersede or re-run the grid.
- It does **not** establish that the `ICS1-3` artifact and the reversal
  dynamic are the SAME phenomenon in every instance -- Section 2 shows
  one specific, previously-conflated instance where they coincide with a
  clean forward transition (no reversal), while Sections 4-5 show
  reversal episodes that do NOT show a comparably large `ICS` excursion
  at that exact moment (the `I(L2)`/`I(L3)` currents at the traced
  reversal in Section 5 are modest, tens of amps at most, not
  hundred-kilo-amp-scale). They appear to be two correlated but distinct
  symptoms of the same underlying stiff-solver-episode class, not one
  single event type.
- It does **not** validate `Cout=4.672 mF`, does not build or exercise
  the handoff into the strict steady-state controller, and does not
  establish anything about this construct's reliability outside this
  project's own specific usage pattern -- same scope limits as
  `BOUNDARY.md` Section 8.

## 10. Provenance and classification

Per this experiment's own `BOUNDARY.md` Section 5: **no new paper-sourced,
cross-paper, or external-device data is introduced.** Everything in this
experiment is one of:

| Item | Category |
|---|---|
| The `.save`-only diagnostic instrumentation (`r04e11_diag_*_instrumented.cir`) | Measurement-only, no physical value, no circuit change |
| `scripts/ltspice_raw_parser.py`, `find_extremum.py`, `state_sequence.py` | Diagnostic tooling, not simulation input |
| The `SWRESET` `Vh=0 -> Vh=1` fix-test change (`r04e11_fixtest_i30_tchg20ns_hysteresis.cir`) | `NUMERICAL_IDEALIZATION` (a construct/timing parameter, no physical counterpart) -- tested and found to have NO effect on the outcome; **not adopted**, left as a negative-result artifact only |
| Every parameter/topology value not listed above (`I_LIMIT=30 A`, `T_CHARGE_MAX in {20,5} ns`, `T_FREEWHEEL_MAX=50 ns`, `CFLY=3 uF`, `LPHASE=1.4666667 nH`, `COUT=4.672 mF`, GS61008T device data, `TSTOP=20 us`, `TMAX=50 ps`) | `SENSITIVITY_ONLY`, copied byte-for-byte from R04E10's own already-classified, already-committed cells -- see R04E10 `BOUNDARY.md` Section 6 for original provenance |

This experiment's overall grade is **`SENSITIVITY_ONLY`** (diagnostic),
with the fix-test itself graded a **negative/refuted `NUMERICAL_
IDEALIZATION` candidate** -- nothing here bears on any `P24_EXPLICIT` or
`P25_SUPPLEMENT` boundary, and nothing here is a paper-comparison result.

## 11. Files produced

- `scripts/build_r04e11_diagnostic_cases.py` -- generates the two
  instrumented diagnostic netlists from R04E10's own committed cases.
- `scripts/ltspice_raw_parser.py` -- reusable LTspice `.raw` binary
  parser (verified against this project's own LTspice 26.0.2 output).
- `scripts/find_extremum.py` -- locates a trace's global MAX/MIN row and
  prints a window of other variables around it.
- `scripts/state_sequence.py` -- reconstructs the settled state-dwell
  sequence over time and flags every backward (reversal) transition.
- `scripts/build_r04e11_fix_test_case.py` -- generates the one-change
  hysteresis fix-test netlist.
- `cases/r04e11_diag_i30_tchg20ns_instrumented.cir` -- primary diagnostic
  netlist (instrumented copy of R04E10's `I_LIMIT=30A/T_CHARGE_MAX=20ns`
  cell).
- `cases/r04e11_diag_i30_tchg5ns_instrumented.cir` -- secondary
  diagnostic netlist (instrumented copy of R04E10's
  `I_LIMIT=30A/T_CHARGE_MAX=5ns` total-stall cell).
- `cases/r04e11_fixtest_i30_tchg20ns_hysteresis.cir` -- fix-hypothesis
  test netlist (one-line `Vh=0->1` change from the primary diagnostic
  netlist).

`.raw`/`.log`/`.db` outputs from all three LTspice runs are gitignored
(`*.raw`, `*.log`, `*.db`, matching this repository's existing
convention -- R04E10's own `cases/` directory contains only `.cir`
files), consistent with the committed netlists being fully sufficient to
reproduce every number in this document by re-running them.

No `results.csv`/`results.json` is produced -- `BOUNDARY.md` Section 3
calls for these only "if you re-ran the 9-cell grid after a fix"; since
no fix changed the outcome, the grid was not re-run and R04E10's own
`results.csv`/`results.json` remain the authoritative record for all 9
cells.
