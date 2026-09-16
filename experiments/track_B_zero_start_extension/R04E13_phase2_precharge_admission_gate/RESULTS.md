# R04E13 result - phase-2 precharge admission gate, stacked on phase-1's own

## Outcome, stated first

**Both required baseline-identity checks pass to full printed precision.**
`N1_PRECHARGE=1, N2_PRECHARGE=1` is confirmed IDENTICAL to R04E10's own
committed `I_LIMIT=60 A`/`T_CHARGE_MAX=50 ns` cell on every measured
quantity (Section 2), and `N1_PRECHARGE=3, N2_PRECHARGE=1` is confirmed
IDENTICAL to R04E12's own committed `N_PRECHARGE=3` cell on every measured
quantity (Section 3).

**A naive first implementation attempt of the phase-2 gate FAILED its own
required pilot verification and was corrected before any grid cell was
trusted** (Section 4): hanging the phase-2 mirror chain directly off the
real, round-robin-shared `FREE2` state's single rule caused the phase-2
precharge chain to re-trigger on EVERY subsequent rotation, not just once
-- a genuine construct bug caught by BOUNDARY.md Section 5's own required
raw-trace pilot check before it was ever allowed to contaminate the grid.
The corrected construct (a dedicated, one-time-only "ADMIT" duplicate of
`CHARGE1`/`FREE1`/`CHARGE2`/`FREE2`, positioned strictly upstream of the
closed round-robin loop, exactly mirroring why R04E12's own phase-1 gate
never had this problem) was independently verified two ways: (a) a
run-independent static analysis of the generated `.rule` graph for all 5
cells (single rule per state, correct targets, and a full deterministic
walk-simulation proving convergence to the intended closed loop with every
precharge/ADMIT state visited at most once -- Section 4), and (b) direct
raw-trace pilot verification against real LTspice runs (Section 5).

**Pilot verification at `N2_PRECHARGE=3` passes ALL SIX checks cleanly.**
**Pilot verification at `N2_PRECHARGE=5` and `N2_PRECHARGE=10` FAILS the
strict admission-order pattern-match**, but this is directly and
precisely attributable to a recurrence of the R04E10/R04E11-diagnosed
retry/chatter solver artifact landing, for the first time in this
project's lineage, transiently INSIDE the precharge-admission window
itself (previously it only ever corrupted ordinary round-robin dwells).
Strong, cross-validated evidence supports this attribution rather than a
new construct defect (Section 5): the SAME stiff episode occurs at
essentially the SAME absolute simulation time (`t=6.1843-6.1844e-7 s`,
agreeing to 6 significant figures) in ALL FOUR of `N1_PRECHARGE=3`'s
cells regardless of `N2_PRECHARGE`, and manifests as an ordinary,
already-characterized round-robin reversal in the `N2_PRECHARGE=1`
baseline and (because its own admission chain is short enough to have
already finished by then) in `N2_PRECHARGE=3`, but as an admission-order
glitch in `N2_PRECHARGE=5`/`10` purely because their longer admission
chains are still running at that exact instant. Rotations complete
cleanly in every cell regardless (10-12 rotations, no stalls), and `IL1-4`
stay safely bounded everywhere (worst case `60.18 A`, `24%` of the
`+/-250 A` limit) -- no `PHYSICAL_BOUNDARY_FAIL`.

**Stacking a phase-2 gate on top of phase 1's own does NOT improve
`Vout`, and mostly WORSENS or only marginally helps `VC2`/`VC3`, across
this grid.** Relative to the `N2_PRECHARGE=1` baseline (`N1_PRECHARGE=3`
fixed): `Vout_final` is WORSE at every tested `N2_PRECHARGE` (`-10.6%` at
`3`, `-11.9%` at `5` and `10`). `VC2_final` is markedly WORSE at
`N2_PRECHARGE=3` (`-33.2%`) but marginally BETTER at `5` and `10`
(`+3.8%`, `+4.1%`). `VC3_final` is WORSE at every tested value (`-35.7%`
at `3`, `-19.6%`/`-18.9%` at `5`/`10`). The root cause is directly
identifiable and not ambiguous: adding ANY phase-2 gate costs exactly 2
completed rotations within the fixed `TSTOP=20 us` window (`12->10`,
Section 7) -- the one-time admission chain's own wall-clock cost eats
into the window that would otherwise fund additional round-robin
rotations, and losing those rotations costs more state-variable progress
than the extra phase-2 charge front-loading gains. **This directly
answers BOUNDARY.md Section 7's question: the bottleneck does NOT
"just relay" further down to `VC3`/phase 3 in an improved way -- gating
phase 2 here is a net-negative-to-marginal trade against phase 1's own
already-validated gate, not a further improvement**, a materially
different (and more clearly negative) result than R04E12's own mixed
phase-1-only finding.

## 1. Parent

**R04E12** (`experiments/track_B_zero_start_extension/
R04E12_phase1_precharge_admission_gate/`), which implemented R04E9's
option (c) for phase 1 ONLY: a one-time admission gate that repeats
`CHARGE1`/`FREE1` `N_PRECHARGE` times before the machine is ever admitted
into `CHARGE2` and the normal round-robin rotation. R04E12 found `Vout`
improves monotonically with `N_PRECHARGE` (`+40%` at `N_PRECHARGE=20`),
but `VC2` improves non-monotonically (best at `N_PRECHARGE in {3,20}`,
worse than baseline at `5`, flat at `10`), with a new `VC3`-goes-negative
trade-off at the single best-`VC2` cell (`N_PRECHARGE=20`). R04E12 fixed
`N_PRECHARGE=3` as its own clean, trade-off-free best value.

R04E9's own root-cause finding (`RESULTS.md` Section 11) is that EVERY
phase beyond the first only ever receives charge relayed from the
capacitor before it. R04E12 tested whether front-loading `C1` alone
helps; this experiment tests the natural next generalization: does ALSO
front-loading `C2` (via the identical gate mechanism, applied to phase 2,
stacked after phase 1's own already-tested gate at its clean
`N1_PRECHARGE=3` value) help further?

## 2. `N1_PRECHARGE=1, N2_PRECHARGE=1` baseline-match sanity check
   (BOUNDARY.md Section 5, identity 1 -- done first)

`cases/r04e13_n1_1_n2_1.cir` was generated, run in real LTspice 26.0.2 via
`tools/ltspice_runner.sh` (exit code 0, `.log` `14,651` bytes, `.raw`
`49,455,150` bytes, matching R04E10's own committed cell's output sizes to
within rounding), and its `.log` `.meas` output compared directly against
R04E10's own already-committed `results.csv` row for `i_limit_a=60.0,
t_charge_max_ns=50.0`. **Every single value matches to full printed
precision:**

| Quantity | R04E10 committed | R04E13 `N1=1,N2=1` | Match? |
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

Guaranteed by construction (`N1_PRECHARGE=1, N2_PRECHARGE=1` emits zero
extra precharge/ADMIT states either side, Section 4), and confirmed
directly by this real re-run, not merely assumed.

## 3. `N1_PRECHARGE=3, N2_PRECHARGE=1` baseline-match sanity check
   (BOUNDARY.md Section 5, identity 2)

`cases/r04e13_n1_3_n2_1.cir` was generated, run in real LTspice (exit code
0, `.log` `14,642` bytes, `.raw` `49,486,030` bytes), and compared
directly against R04E12's own already-committed `results.csv` row for
`r04e12_npre_3`. **Every single value matches to full printed precision:**

| Quantity | R04E12 `N_PRECHARGE=3` committed | R04E13 `N1=3,N2=1` | Match? |
|---|---:|---:|---|
| `STATE_FINAL` | `6.0` (`CHARGE2`) | `6.0` (`CHARGE2`) | YES |
| `VOUT_FINAL` | `0.0144837088883` | `0.0144837088883` | YES |
| `VC1_FINAL` | `1.873742342` | `1.873742342` | YES |
| `VC2_FINAL` | `0.715811192989` | `0.715811192989` | YES |
| `VC3_FINAL` | `0.106644280255` | `0.106644280255` | YES |
| `IL1_MAX` | `60.1728401184` | `60.1728401184` | YES |
| `IL1_MIN` | `-40.1942024231` | `-40.1942024231` | YES |
| `IL2_MAX` | `29.7509059906` | `29.7509059906` | YES |
| `IL2_MIN` | `-52.7431335449` | `-52.7431335449` | YES |
| `IL3_MAX` | `9.54246234894` | `9.54246234894` | YES |
| `IL3_MIN` | `-17.7880992889` | `-17.7880992889` | YES |
| `IL4_MAX` | `2.34767317772` | `2.34767317772` | YES |
| `IL4_MIN` | `-6.6421546936` | `-6.6421546936` | YES |
| `ICS1_MAX` | `7775.97705078` | `7775.97705078` | YES |
| `ICS1_MIN` | `-1610.6373291` | `-1610.6373291` | YES |
| `ICS2_MAX` | `3904.09692383` | `3904.09692383` | YES |
| `ICS2_MIN` | `-143499.234375` | `-143499.234375` | YES |
| `ICS3_MAX` | `143501.59375` | `143501.59375` | YES |
| `ICS3_MIN` | `-8224.96972656` | `-8224.96972656` | YES |
| Rotations completed | `12` | `12` | YES |

The generated `.machine`/timer-boolean/rule text for this cell was also
confirmed, by direct `diff` (modulo header comments, subcircuit name, and
one cosmetic blank-line placement), IDENTICAL to R04E12's own committed
`r04e12_npre_3.cir`, confirming the match is guaranteed by construction
(`N2_PRECHARGE=1` emits zero phase-2 extra/ADMIT states, Section 4), not a
numerical coincidence.

## 4. The implementation construct actually used, INCLUDING a design
   correction found and fixed during this experiment's own build

**A naive first attempt, and why it failed.** The most direct
generalization of R04E12's own phase-1 mirror-chain pattern to phase 2
would hang the `N2_PRECHARGE-1` extra mirror pairs directly off the real,
shared `FREE2` state's single outgoing rule (`.rule FREE2 PCHG2_1 ...`
instead of `.rule FREE2 CHARGE3 ...`). This was built and run first (an
`(N1=3, N2=3)` cell). **`verify_precharge_gate2.py`'s own required pilot
check (BOUNDARY.md Section 5) caught the defect immediately, before any
result was trusted**: the phase-2 mirror chain re-triggered on EVERY
subsequent round-robin rotation (`count_reversals.py` showed reversal
events like `CHARGE3 -> FREE1` recurring throughout the ENTIRE 20us run,
not confined to a one-time admission window; the dwell-count check found
`148` phase-2-precharge-role dwells against an expected `4`).

**Root cause (automaton-theoretic, not a typo).** In a `.machine` where
every state has EXACTLY ONE outgoing `.rule` (this project's own
established discipline, R04E12 RESULTS.md Section 1), the sequence of
states visited from any starting state is COMPLETELY DETERMINISTIC --
formally, a "functional graph" (out-degree 1 everywhere) whose walk from
any start state eventually enters a fixed cycle and never leaves it. Once
a walk is ON a cycle, EVERY state reachable from a cyclic state is ALSO
on that same cycle forever, because the walk cannot behave differently on
its "first" visit to a state versus any later visit -- a state's single,
static rule has no memory of how it was reached. `CHARGE2`/`FREE2` are
necessarily part of the closed round-robin cycle (reached every rotation
via `CHARGE1`/`FREE1`/`FREE4`), so anything hanging off `FREE2`'s single
rule is ALSO on that cycle permanently. This is exactly why R04E12's own
phase-1 gate never had this problem: its mirror chain sits strictly
BEFORE `CHARGE1` ever joins the cycle, reachable only via the machine's
own one-time initial condition (never via any `.rule`), so nothing inside
the closed loop ever points back into it. A gate hung off a state that is
itself already inside the loop (as phase 2's naturally is) cannot reuse
that exact trick unmodified.

**The fix**, used in every committed cell with `N2_PRECHARGE>1`: a
dedicated, one-time-only "ADMIT" duplicate of `CHARGE1`/`FREE1`/
`CHARGE2`/`FREE2` (named `CHARGE1_ADMIT`/`FREE1_ADMIT`/`CHARGE2_ADMIT`/
`FREE2_ADMIT` -- electrically IDENTICAL mirrors, same current-limit-OR-
timeout / zero-crossing-OR-timeout rules) is inserted strictly upstream
of the closed loop, exactly the same structural position R04E12's own
phase-1 mirror chain already occupies. The full one-time walk is:

```
[phase-1 mirror chain, if N1_PRECHARGE>1: PCHG1_1/PFREE1_1..PCHG1_{N1-1}/PFREE1_{N1-1}]
-> CHARGE1_ADMIT -> FREE1_ADMIT -> CHARGE2_ADMIT -> FREE2_ADMIT
-> [phase-2 mirror chain: PCHG2_1/PFREE2_1 .. PCHG2_{N2-1}/PFREE2_{N2-1}]
-> CHARGE3   (merges into the closed loop here, permanently)
```

and the closed, permanent round-robin loop (entered exactly once from the
tail above, repeating forever after) is the ordinary 8-state cycle using
PLAIN names: `CHARGE3 -> FREE3 -> CHARGE4 -> FREE4 -> CHARGE1 -> FREE1 ->
CHARGE2 -> FREE2 -> CHARGE3` (cycle closes). `CHARGE1_ADMIT`/
`FREE1_ADMIT`/`CHARGE2_ADMIT`/`FREE2_ADMIT` are visited EXACTLY ONCE in
the entire run -- a pure `.machine`-state-graph necessity to give the
phase-2 branch point a private, acyclic history to branch on, not a
second physical circuit (same gate drive, same exit conditions as the
loop's own `CHARGE1`/`FREE1`/`CHARGE2`/`FREE2`). When `N2_PRECHARGE==1`
(no phase-2 gate at all), NONE of this ADMIT duplication is emitted --
the construct collapses EXACTLY to R04E12's own single-shared-loop
pattern, which is why Sections 2/3's identity checks pass byte-for-byte.

This is a genuinely stronger structural requirement than phase 1's own
gate needed, discovered by building the naive version FIRST and catching
its failure via the project's own required pilot-verification discipline
-- the same "isolated/naive generalization does not guarantee full-machine
correctness" lesson R04E10 Section 1 (`T_CHARGE_MAX=5ns` cells) and R04E12
Section 1 (single-rule-per-state discipline) already established,
reconfirmed here for a second-gate-in-a-chain scenario neither of those
experiments needed to consider.

**Independent, run-independent structural verification** (`scripts/
verify_rule_graph_static.py`, new for this experiment): for all 5 grid
cells, confirms directly from the generated `(order, rules)` data
structure (no LTspice, no `.raw` file): state codes are contiguous with no
gaps/duplicates; every declared state has EXACTLY ONE outgoing rule;
every rule target is a declared state; charge-role codes are all even and
free-role codes all odd, partitioning every code exactly; and a full
deterministic walk-simulation (following only rule targets, valid because
out-degree is exactly 1 everywhere) from state 0 for 200 steps confirms
every precharge/ADMIT state is visited AT MOST ONCE and the walk converges
to the intended closed 8-state loop. **All 5 cells: PASS.** This is what
lets Section 5 below attribute the `N2_PRECHARGE=5`/`10` raw-trace pilot
anomaly to a solver artifact rather than a `.rule`-graph defect: the graph
itself is proven correct independent of any specific LTspice run.

Subcircuit renamed `SCB4P_P24_R04E13` only to avoid a same-name collision
with R04E10/R04E12's own files, electrically identical.

## 5. Pilot verification of the phase-2 gate construct (BOUNDARY.md
   Section 5, done at `N2_PRECHARGE=3` and `=10`, plus `=5` for extra
   context, before trusting the 4-cell grid)

`scripts/verify_precharge_gate2.py` (generalizing R04E12's own
`verify_precharge_gate.py`) directly parses each cell's raw `.raw` binary
transient trace and reconstructs the settled dwell sequence of
`V(state_mon)`, then checks: (1) the phase-1 mirror chain is visited in
order, exactly once, before `CHARGE1`/`CHARGE1_ADMIT`, and never again
after; (2) the phase-2 mirror chain (and, when present, the ADMIT states)
is visited in strictly increasing order, immediately after
`CHARGE2_ADMIT`/`FREE2_ADMIT` and before the real (loop) `CHARGE3`, and
never re-entered after the machine's first arrival at `CHARGE3`; (3) exact
dwell counts match `2*(N1-1)` and `2*(N2-1)` respectively.

**`N1_PRECHARGE=3, N2_PRECHARGE=3`** (`cases/r04e13_n1_3_n2_3.raw`): ALL
SIX CHECKS PASS. Phase-1 admission order: expected
`['PCHG1_1','PFREE1_1','PCHG1_2','PFREE1_2','CHARGE1_ADMIT']`, actual
IDENTICAL. Phase-1 mirror chain never re-triggers. Phase-1 dwell count:
expected `4`, got `4`. Phase-2 admission order: expected segment after
`CHARGE2_ADMIT`/`FREE2_ADMIT` = `['PCHG2_1','PFREE2_1','PCHG2_2',
'PFREE2_2']`, actual IDENTICAL. Phase-2/ADMIT states never re-trigger
after first `CHARGE3`. Phase-2 dwell count: expected `4`, got `4`.
**Overall: PASS.**

**`N1_PRECHARGE=3, N2_PRECHARGE=10`** (`cases/r04e13_n1_3_n2_10.raw`):
Phase-1 checks 1-3 ALL PASS (identical prefix, no re-trigger, dwell count
`4`/`4`). **Phase-2 check 1 (admission order) FAILS**: the actual dwell
sequence after `CHARGE2_ADMIT`/`FREE2_ADMIT` is `['PCHG2_1','PFREE2_1',
'PCHG2_2','PFREE2_2','PCHG2_3','PFREE2_3','PCHG2_4','PCHG2_8','FREE1',
'CHARGE2','FREE1','CHARGE2','FREE2']` against an expected 18-element
mirror sequence -- after a NORMAL `~51 ns` dwell in `PCHG2_4` (matching
`T_CHARGE_MAX=50 ns`), the raw trace jumps to code `22` (`PCHG2_8`) then,
just `68 ps` later, to code `31` (the LOOP's `FREE1`), skipping states
`PFREE2_4` through `PCHG2_7`/`PFREE2_7` entirely. **Phase-2 check 2
(never re-triggers) PASSES** (nothing from the mirror/ADMIT set appears
again after this). **Phase-2 check 3 (dwell count) FAILS**: expected `18`,
got `8`.

**`N1_PRECHARGE=3, N2_PRECHARGE=5`** (`cases/r04e13_n1_3_n2_5.raw`), run
for extra context beyond BOUNDARY.md's own minimum requirement: the SAME
pattern -- phase-1 checks all PASS; phase-2 check 1 FAILS after a normal
dwell in `PCHG2_4`, jumping directly to the LOOP's `FREE1`/`CHARGE2`
(skipping `PFREE2_4`); phase-2 check 3 FAILS (expected `8`, got `7`).

**Diagnosis: this is the ALREADY-DIAGNOSED R04E10/R04E11 retry/chatter
solver artifact, landing for the first time in this project's lineage
inside a precharge-admission window itself, NOT a new construct defect --
supported by strong, precisely-timed, cross-cell evidence, not
speculation:**

| Cell | Reversal/anomaly instant nearest this episode | Manifestation |
|---|---:|---|
| `N1=3,N2=1` (baseline) | `t=6.184384155884075e-07 s` | ordinary round-robin reversal: `CHARGE3 -> FREE2` |
| `N1=3,N2=3` | `t=6.184391206857805e-07 s` | ordinary round-robin reversal: `CHARGE2 -> CHARGE4` |
| `N1=3,N2=5` | `t=6.184388364598225e-07 s` | admission-order glitch: `PCHG2_4 -> FREE1(loop)` |
| `N1=3,N2=10` | `t=6.184328867138431e-07 s` | admission-order glitch: `PCHG2_4 -> PCHG2_8 -> FREE1(loop)` |

All four timestamps agree to 6 significant figures (`6.1843-6.1844e-7 s`),
despite the four cells having different machine topologies (different
`N2_PRECHARGE`) -- this is the SAME underlying stiff, sub-picosecond-
timestep solver episode R04E11 directly diagnosed (a genuine, continuous
sweep of the raw `.machine` internal state variable through several
state-code boundaries within picoseconds), occurring at essentially a
FIXED absolute point in the shared circuit transient (independent of which
machine state happens to be active there). In the baseline and
`N2_PRECHARGE=3` (whose short admission chain has already finished and
joined the round-robin loop well before `t=6.18e-7 s`), the SAME episode
lands on an ordinary loop dwell and is already captured by the
`count_reversals.py`/`~19-27%` reversal-rate figures (Section 8) --
already-characterized, unremarkable. In `N2_PRECHARGE=5` and `=10` (whose
LONGER admission chains, needing `4`/`9` extra mirror pairs, are STILL
running at that exact instant), the identical episode instead lands
inside the admission-order check itself, which is why (and ONLY why) the
strict pattern-match fails there and not at `N2_PRECHARGE=3`. This is
independently corroborated by Section 4's static rule-graph proof (the
`.rule` graph itself is provably correct for all 5 cells, so the anomaly
cannot originate in the graph) and by the fact that every affected cell
still completes its expected `10` rotations cleanly with `IL1-4` safely
bounded (Section 7) -- the artifact does not compromise the cell's overall
`CONTROLLER_GUARD_PASS` grade, only this specific raw-trace pattern-match.

**New methodological lesson for this project** (generalizing R04E10
Section 1's own "isolated pilot verification is necessary but not
sufficient" finding): a one-time admission gate stretched long enough in
WALL-CLOCK duration to overlap one of this construct family's fixed-timing
stiff-solver episodes can show that episode intrude directly into its own
admission-order verification, not merely into later round-robin dwells --
worth checking explicitly in any future experiment building a longer or
differently-timed admission chain on this same `CHARGE_k`/`FREE_k`
construct family.

Per BOUNDARY.md Section 1/9: `IL1-4` remain the trustworthy peak-current
indicator in every cell; `ICS1-3` magnitudes are flagged (not reported as
physical currents), exactly as R04E10/R04E11/R04E12 established.

## 6. Parameters actually used

Fixed for every cell (BOUNDARY.md Section 4, R04E12's own clean best
`N_PRECHARGE=3` value / R04E10's own best-performing cell): `Vin=48 V`,
`nP=4`, `nM=4`, full four-phase P24 connectivity (unchanged from
R04E9/R04E10/R04E12), `LPHASE=1.4666667 nH`, `CFLY=3 uF`, `COUT=4.672 mF`,
GS61008T device data (1 HS / 2 parallel LS), true-zero-energy initial
conditions (`ic=0` throughout, `UIC`), `I_LIMIT=60 A`, `T_CHARGE_MAX=
50 ns`, `T_FREEWHEEL_MAX=50 ns`, `TSTOP=20 us`, `TMAX=50 ps`,
`N1_PRECHARGE=3` fixed. Swept: `N2_PRECHARGE` in `{1, 3, 5, 10}`, 4 cells
(plus the separate `N1_PRECHARGE=1, N2_PRECHARGE=1` identity-check cell,
5 netlists total), all run to completion in real LTspice 26.0.2 (batch
mode, exit code 0; `.log` files `13.9-14.7 KB`, `.raw` files `42.6-50.2 MB`
-- all 5 cells, confirming completed `TSTOP=20 us` transient runs, none
truncated).

## 7. The 4-cell grid

| `I_LIMIT` (A) | `N1_PRECHARGE` | `N2_PRECHARGE` | Final state | Rotations | `Vout` final (V) | `VC1` final (V) | `VC2` final (V) | `VC3` final (V) | `IL1_max` (A) | Handoff? |
|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---|
| 60 | 3 | 1  | CHARGE2 (loop, code 6)   | 12 | 0.0144837 | 1.873742 | 0.715811 | 0.106644 | 60.173 | NO |
| 60 | 3 | 3  | CHARGE4 (loop, code 14)  | 10 | 0.0129453 | 1.759638 | 0.477898 | 0.068555 | 60.173 | NO |
| 60 | 3 | 5  | FREE1 (loop, code 21)    | 10 | 0.0127567 | 1.457067 | 0.742921 | 0.085745 | 60.173 | NO |
| 60 | 3 | 10 | FREE1 (loop, code 31)    | 10 | 0.0127548 | 1.461010 | 0.745437 | 0.086482 | 60.173 | NO |

Targets for reference: `Vout=1 V`, `VC1=36 V`, `VC2=24 V`, `VC3=12 V`.
Full numeric detail (min currents, `ICS1-3` values, all trajectory
checkpoints, per-rotation trend statistics) is in `results.csv`/
`results.json`, generated by `scripts/analyze_r04e13_grid.py`. `IL1-4`
stay comfortably inside the `+/-250 A` safety bound in every cell (worst
case `IL1_max=60.173 A`, `24%` of the bound). `IL2_max` shows a small,
real increase at `N2_PRECHARGE>=3` (`34.843 A` vs `29.751 A` at the
baseline, `+17.1%`, still only `13.9%` of the bound) -- the added phase-2
admission passes draw a slightly higher peak on `L2`, consistent with
R04E12's own analogous small `IL2_max` increase at its largest tested
`N_PRECHARGE`. **No `PHYSICAL_BOUNDARY_FAIL` in any cell.**

## 8. Does stacking a phase-2 gate further improve `VC2`/`VC3`/`Vout`, or
   does the bottleneck just relay to `VC3`/phase 3? (BOUNDARY.md
   Section 7's question, answered directly)

**No -- it does not further improve, and the bottleneck does not
"cleanly relay" anywhere; the net effect across this grid is negative to
marginal, and the reason is directly identifiable, not ambiguous.**

**`Vout_final` is WORSE than the `N2_PRECHARGE=1` baseline
(`0.0144837 V`) at every tested value**: `-10.6%` at `N2_PRECHARGE=3`
(`0.0129453 V`), `-11.9%` at `N2_PRECHARGE=5` (`0.0127567 V`) and
`N2_PRECHARGE=10` (`0.0127548 V`). This is the OPPOSITE of R04E12's own
clean, monotonically-positive `Vout` result for gating phase 1 -- gating
phase 2 on top does not repeat that pattern.

**`VC2_final` relative to baseline (`0.715811 V`):**

| `N2_PRECHARGE` | `VC2_final` (V) | vs. baseline | Direction |
|---:|---:|---:|---|
| 1 (baseline) | 0.715811 | -- | -- |
| 3  | 0.477898 | **-0.238 (-33.2%)** | markedly worse |
| 5  | 0.742921 | +0.027 (+3.8%) | marginally better |
| 10 | 0.745437 | +0.030 (+4.1%) | marginally better |

Only `N2_PRECHARGE in {5,10}` show ANY `VC2` improvement, and it is small
(`~4%`) -- far smaller than R04E12's own phase-1-gate `VC2` gains
(`+15.7%` at `N_PRECHARGE=3`, `+37.9%` at `N_PRECHARGE=20`). `VC3_final`
is WORSE than baseline (`0.106644 V`) at every tested value: `-35.7%` at
`N2_PRECHARGE=3`, `-19.6%`/`-18.9%` at `5`/`10` -- so the marginal `VC2`
gain at `N2_PRECHARGE in {5,10}` comes packaged with a substantially
WORSE `VC3`, not an improvement that "relays" cleanly forward. `VC1_final`
is also WORSE than baseline at every tested value (`-6.1%` at `3`,
`-22.2%`/`-22.0%` at `5`/`10`).

**The root cause is directly identifiable: adding ANY phase-2 gate costs
exactly 2 completed rotations within the fixed `TSTOP=20 us` window**
(`12 -> 10`, Section 7's table), regardless of whether `N2_PRECHARGE` is
`3`, `5`, or `10` (all three cost the same 2 rotations, no further cost as
`N2_PRECHARGE` grows). The one-time admission chain's own wall-clock cost
(a minimum of `~4*100 ns=400 ns` at `N2_PRECHARGE=3`, up to
`~9*100 ns=900 ns` at `N2_PRECHARGE=10` in the idealized zero-artifact
case, similar order to R04E12's own worst-case `~1.9 us` at
`N_PRECHARGE=20`) eats into the window that would otherwise fund
additional round-robin rotations; losing those 2 rotations' worth of net
charge transfer costs more state-variable progress than the extra
phase-2-only front-loading gains at every state variable except `VC2` at
the two largest tested values, where the gain is real but small
(`~4%`) and paired with a `VC3` cost roughly `5x` larger in relative
terms.

**Answering BOUNDARY.md Section 7's question directly: the bottleneck
does NOT relay cleanly to `VC3`/phase 3 in an improved sense -- `VC3` is
the variable that WORSENS most, at every tested `N2_PRECHARGE`.** The
marginal effect of gating phase 2 here is smaller than, and largely
opposite in sign to, gating phase 1 was in R04E12, and it introduces its
own dominant new trade-off (the rotation-count cost) that R04E12's
phase-1-only gate did not exhibit at any of its own tested values (R04E12
Section 6 found rotation count only ever rose mildly with `N_PRECHARGE`,
`12->14`, never fell).

## 9. Recurrence of the R04E10/R04E11-diagnosed retry/chatter dynamic and
   `ICS1-3` artifact

BOUNDARY.md Section 1 explicitly anticipated this "may recur here too."
It recurs in every one of the 5 cells, at a MODESTLY HIGHER severity than
R04E12's own `19.2-21.8%` range:

| Cell | Settled dwell transitions | Reversals | Reversal rate |
|---|---:|---:|---:|
| `N1=1,N2=1` | 409 | 89 | 21.8% |
| `N1=3,N2=1` | 411 | 89 | 21.7% |
| `N1=3,N2=3` | 428 | 111 | 26.0% |
| `N1=3,N2=5` | 430 | 114 | 26.6% |
| `N1=3,N2=10` | 442 | 121 | 27.4% |

The two identity-check cells (`N2_PRECHARGE=1`) match R04E10/R04E12's own
`~19-22%` figures almost exactly, as expected (mechanism-identical
construct). The three `N2_PRECHARGE>1` cells show a real, modest increase
(`26-27%`) -- consistent with a longer admission chain simply providing
more wall-clock opportunity for the same class of stiff episode to occur,
not a new or qualitatively different phenomenon (Section 5's precise
cross-cell timestamp match already establishes this is the SAME episode
class, not a new one). The coincident `ICS1-3` `.meas` artifact
(`>1000 A` flag, same threshold as R04E10/R04E11/R04E12) is present in
every cell (`ICS1_MAX/MIN`, `ICS2_MAX/MIN` in all 5; `ICS3_MAX/MIN` in the
two `N2=1` cells, `ICS3_MIN` only -- not `ICS3_MAX` -- in the three
`N2>1` cells, an incidental exception of the same kind R04E12's own
`N_PRECHARGE=10` cell showed). **Per BOUNDARY.md Section 1/9: `IL1-4` are
the trustworthy peak-current indicator in every cell; `ICS1-3` magnitudes
are flagged, not reported as physical currents.** No cell's retry/chatter
episode prevented rotation completion (10-12 rotations in every cell) --
BOUNDARY.md Section 9's `PHYSICAL_BOUNDARY_FAIL`/stall failure conditions
do NOT trigger; only Section 5's own raw-trace pilot-pattern-match fails
at `N2_PRECHARGE in {5,10}`, attributed above to this same recurring
phenomenon, not silently worked around.

## 10. What this experiment establishes

- The compile-time-unrolled, ADMIT-duplicated precharge admission-gate
  construct (Section 4) is the CORRECT generalization of R04E12's own
  phase-1 pattern to a second, downstream gate -- proven both by
  independent static rule-graph analysis (all 5 cells) and by direct
  raw-trace pilot verification (cleanly at `N2_PRECHARGE=3`). A naive,
  more direct generalization was tried first and FAILED this same
  verification discipline before being trusted, a genuine methodological
  finding worth citing for any future multi-stage-gate construct on this
  `.machine` family.
- Both required baseline identities (`N1=1,N2=1` vs. R04E10;
  `N1=3,N2=1` vs. R04E12's own `N_PRECHARGE=3`) are confirmed to full
  printed precision.
- Stacking a phase-2 gate on top of phase 1's own (at `N1_PRECHARGE=3`
  fixed) does NOT further improve `Vout`, `VC1`, or `VC3` at any tested
  `N2_PRECHARGE` -- all three are WORSE than the `N2_PRECHARGE=1`
  baseline at every tested value. `VC2` shows a small (`~4%`) improvement
  at `N2_PRECHARGE in {5,10}` only, paired with a larger (`~19%`) `VC3`
  cost at those same values.
- The dominant, directly-identified cause of this net-negative result is
  a fixed rotation-count cost (`12->10`) incurred by adding ANY phase-2
  gate within the fixed `TSTOP=20 us` window -- a genuinely different,
  and more clearly negative, dynamic than R04E12's own phase-1-only gate
  exhibited (which never cost rotations at any tested value).
- The R04E10/R04E11-diagnosed retry/chatter dynamic recurs in every cell,
  at a modestly higher rate (`26-27%`) than R04E12's own `~19-22%` for
  cells with `N2_PRECHARGE>1`, and for the first time in this project's
  lineage was directly observed intruding into a precharge-admission-order
  raw-trace check itself (not just ordinary round-robin dwells) --
  precisely timed cross-cell evidence attributes this to the SAME
  already-diagnosed episode class landing, by wall-clock coincidence, at a
  different point in a longer admission chain, not a new phenomenon.
- No cell approaches the handoff condition; every cell remains
  `CONTROLLER_GUARD_PASS`. `IL1-4` stay safely bounded in every cell
  (worst case `24%` of the `+/-250 A` limit).

## 11. What this experiment cannot prove

- It does not close the handoff gap at any cell (best `Vout=0.0145 V` at
  the `N2_PRECHARGE=1` baseline is still `98.5%` short of `1 V`) --
  R04E10 Section 10's structural finding (this whole construct family
  converges far more slowly per-cycle than R04E7/E8's switch-only
  mechanism) remains unaddressed.
- It does not validate `Cout=4.672 mF`, still an unconfirmed inherited
  value.
- It does not build or exercise the handoff into the existing strict
  steady-state controller -- out of scope, same as R04E9-R04E12.
- A result here is specific to `N1_PRECHARGE=3` fixed; it does not
  explore the full `N1 x N2` interaction space (BOUNDARY.md Section 10),
  and must not be read as a general statement about stacking precharge
  gates independent of the specific `N1` value chosen -- a different
  `N1_PRECHARGE` (e.g. R04E12's own numerically-best-for-`VC2` `N=20`)
  might interact differently with a stacked phase-2 gate, untested here.
- It does not gate phases 3 or 4 -- whether the observed net-negative
  result generalizes (or reverses) if the SAME gate were applied further
  down the chain remains untested.
- It does not further diagnose the `ICS1-3`/retry-chatter artifact's
  LTspice-internals root cause (R04E11 already left this undiagnosed at
  that level); this experiment adds a new, precisely-timed observation
  (the episode's admission-window intrusion, Section 5) but not a new
  root-cause finding.
- It does not evaluate R04E9 Section 11's options (a) (direct topology
  change) or (b) (passive precharge circuit) -- those remain separate,
  unstarted candidate directions.

## 12. Provenance and classification (BOUNDARY.md Section 6)

| Value | Source | Category |
|---|---|---|
| Phase-2 precharge admission-gate construct (ADMIT-duplicated, compile-time-unrolled state chain, Section 4) | This experiment's own generalization of R04E12's own validated phase-1 construct, corrected during this experiment's own build after a naive first attempt failed BOUNDARY.md Section 5's own required pilot check (Section 4) | `NUMERICAL_IDEALIZATION`/engineering construct -- no physical counterpart, a controller/sequencing choice |
| `N1_PRECHARGE=3` (fixed) | R04E12's own clean, trade-off-free best value (its `BOUNDARY.md` Section 4) | inherited, `SENSITIVITY_ONLY` (R04E12 provenance) |
| `N2_PRECHARGE` swept values `{1, 3, 5, 10}` | New for this experiment; `1` is the R04E12-`N=3`-equivalent baseline | `SENSITIVITY_ONLY` |
| `I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`, `T_FREEWHEEL_MAX=50 ns` | R04E10's own best-performing cell, fixed here rather than re-swept (inherited via R04E12) | inherited, `SENSITIVITY_ONLY` |
| `scripts/ltspice_raw_parser.py` | Reused verbatim (unmodified) from R04E11/R04E12's own committed, already-validated diagnostic tooling | Diagnostic tooling, not simulation input |
| `scripts/verify_precharge_gate2.py`, `scripts/count_reversals.py`, `scripts/analyze_r04e13_grid.py`, `scripts/verify_rule_graph_static.py` | New for this experiment, built on top of the reused `ltspice_raw_parser.py` and directly generalizing R04E12's own equivalent scripts | Diagnostic tooling, not simulation input |
| Every value carried over from R04E9/R04E10/R04E12 (`Vin`, `nP`, `nM`, topology, `LPHASE`, `CFLY`, `COUT`, GS61008T data, handoff tolerance bands, `CHARGE_k`/`FREE_k` exit rules) | See R04E12 `BOUNDARY.md` Section 6 | unchanged |

**No new paper-sourced, cross-paper, or external-device data is
introduced.** Nothing here bears on any `P24_EXPLICIT` or
`P25_SUPPLEMENT` boundary.

**Overall grade**: `CONTROLLER_GUARD_PASS` (5/5 cells: rotations complete,
currents stay bounded, handoff never reached in any cell), with a
**net-negative-to-marginal finding** on the specific question BOUNDARY.md
Section 7 poses -- `Vout`/`VC1`/`VC3` are WORSE than the `N2_PRECHARGE=1`
baseline at every tested `N2_PRECHARGE`, `VC2` shows only a small
(`~4%`) improvement at `N2_PRECHARGE in {5,10}` paired with a larger
`VC3` cost at those same values, and BOUNDARY.md Section 9's own
"no measurable improvement... a legitimate, informative negative result"
failure condition applies cleanly to `Vout`/`VC1`/`VC3` (though not to
`VC2`, which does show a small measurable gain at two of the three
tested points) -- reported plainly as the honest, mostly-negative result
this grid shows, per Ground Rule 7, not smoothed into either a clean
"stacking helps" or "stacking never helps" verdict. `SENSITIVITY_ONLY`
overall.

## 13. Files produced

- `scripts/build_r04e13_cases.py` -- generates the 5 case netlists from
  R04E10's own committed template, implementing both the reused phase-1
  gate (unchanged from R04E12) and the new, ADMIT-duplicated phase-2 gate
  (see its own module docstring for the full construct design rationale,
  including the documented naive-attempt failure and its fix).
- `scripts/verify_precharge_gate2.py` -- pilot verification tool
  (Section 5): confirms both stacked gates' admission order, one-time
  gating, and dwell counts directly from a cell's `.raw` file.
- `scripts/verify_rule_graph_static.py` -- independent, run-independent
  structural verification of the generated `.rule` graph for all 5 cells
  (Section 4): single-rule-per-state discipline, contiguous codes, parity,
  and deterministic walk-simulation convergence to the intended loop.
- `scripts/count_reversals.py` -- generalizes R04E12's own reversal count
  to this experiment's ADMIT-aware state numbering (Section 9).
- `scripts/analyze_r04e13_grid.py` -- parses all 5 cells' `.log` files
  into `results.csv`/`results.json` (adapted from R04E12's own
  `analyze_r04e12_grid.py`).
- `scripts/ltspice_raw_parser.py` -- reused verbatim from R04E11/R04E12.
- `cases/r04e13_n1_{1,3}_n2_{1,3,5,10}.cir` -- the 5 committed netlists
  (`n1_1_n2_1` and `n1_3_n2_1` are the two identity-check cells;
  `n1_3_n2_{1,3,5,10}` is the main 4-cell grid).
- `results.csv`/`results.json` -- full grid results, same format as
  R04E12's own.

`.raw`/`.log`/`.db` outputs from all 5 LTspice runs are gitignored
(`*.raw`, `*.log`, `*.db`, this repository's existing convention),
consistent with the committed netlists being fully sufficient to
reproduce every number in this document by re-running them.
