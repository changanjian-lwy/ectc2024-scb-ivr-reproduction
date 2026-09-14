# A37 joint seven-state 200 ns periodic solve results

Branch: `CROSS_PAPER_EXTENSION`, labelled P25 9% negative-current branch. Not a
2024-primary (`P24_EXPLICIT` 1-2%) result; see BOUNDARY.md Section 8.

## 1. Whether the simulation completed normally

Yes, at the individual-run level: every one of the 174 LTspice batch
invocations behind this result completed normally (exit code 0, no solver
non-convergence). The `.meas` "FAIL'ed" lines seen in every run's `.log` for
`t_h3_off`, `il3_h3_off`, `peak_error_h3`, `t_h4_off`, `il4_h4_off`,
`peak_error_h4` are the controller correctly reporting that H3 (and
consequently H4) never received a fixed-`TON` turn-off event because they
never turned on in the first place -- this is the intended
`MISSED_ZVS_SLOT`-blocking behavior from A35/A36, not a solver error.

At the optimizer level, two attempts were made and neither converged to the
7-DOF/15-residual joint solution BOUNDARY.md's Section 6 defines:

1. `scipy.optimize.least_squares(method="lm")`, `diff_step=1e-4`,
   `max_nfev=80`. This attempt did not respect `max_nfev` as a hard cap (it
   was still issuing new evaluations past 120), and was terminated only
   because the host session running it was torn down externally after 120
   completed LTspice evaluations -- not a simulation failure, and not this
   script's own termination logic. All 120 completed evaluations were
   recovered from their `.raw` files on disk (`A37_solver_work/iter_001.cir`
   through `iter_119.cir`, one file having been mid-write at the moment of
   interruption and correctly excluded by recovery) without re-running
   LTspice, and are included in `solver_history.json`.
2. `scipy.optimize.least_squares(method="trf")`, `diff_step=1e-3`,
   `max_nfev=60`, restarted from the same seed (the numerical optimizer state
   itself cannot be resumed across a killed process; only completed LTspice
   evaluations can be, and were). This run terminated normally by its own
   `xtol` criterion after 19 further evaluations, `optimizer_success=True`,
   but at a point with a *worse* aggregate residual norm (226.92) than the
   best point already on record (209.40), and with zero individually
   converged residuals -- see Section 5. `scipy`'s own "success" flag
   describes only that its local step size shrank below `xtol`; it does not
   mean this experiment's acceptance condition was met.

Combined: 174 LTspice evaluations across both attempts, all recorded in
`solver_history.json`.

## 2. Parameters actually used

Locked (unchanged from A35/A36, see BOUNDARY.md Section 3): topology,
`Coss` (385 pF high-side / 770 pF low-side), ideal reverse-conduction clamp
(`Vf=0`, `Ron=1 mOhm`), `LPHASE=1.466666666666667 nH`, `TON=16.6667 ns`,
`PHASE=50 ns`, `NEG_FRAC=.09`, output held at ideal 1 V, timestep/solver
options.

Seven free variables, seeded per BOUNDARY.md Section 4 / the task's explicit
seeding instructions:

| Variable | Seed value | Provenance |
|---|---:|---|
| `IL1_INIT` | 5.2947 A | A36 `best_candidate.json` |
| `IL2_INIT` | 21.20509533697147 A | A36 `best_candidate.json` |
| `IL3_INIT` | 41.5782701063 A | A33 (carried through A34/A35/A36 unchanged) |
| `IL4_INIT` | 84.1447433786 A | A33 (carried through A34/A35/A36 unchanged) |
| `VC1_INIT` | 36.000066454 V | Protocol Section VIII's documented "36/24/12 V" guess table (a file named `RESEARCH_NOTES.md` was not found anywhere in the project; this project-wide protocol document is the authoritative source for that same guess) |
| `VC2_INIT` | 23.9999142326 V | same as above |
| `VC3_INIT` | 12.0006048777 V | same as above |

`IL3_INIT`/`IL4_INIT` were cross-checked (not re-derived) against an
independent exponential-decay interpolation between the two solved anchor
points `IL1_INIT`(local phase-time 0) and `IL2_INIT`(local phase-time
150 ns) using the local-timeline model in
`PHASE_LOCAL_TIMELINE_REBUILD.md`; the interpolation gives approximately
41.3 A and 80.2 A respectively, close enough to A33's inherited 41.58 A /
84.14 A to use the latter directly rather than introduce new unvalidated
numbers, per the task's "e.g. rotated/interpolated" guidance.

**Best candidate found** (see Section 5 for why this is the seed itself, not
either optimizer's reported solution):

| Variable | Value |
|---|---:|
| `IL1_INIT` | 5.2947 A |
| `IL2_INIT` | 21.205095337 A |
| `IL3_INIT` | 41.5782701063 A |
| `IL4_INIT` | 84.1447433786 A |
| `VC1_INIT` | 36.000066454 V |
| `VC2_INIT` | 23.9999142326 V |
| `VC3_INIT` | 12.0006048777 V |

## 3. When each key event occurred (best candidate)

| Event | Time | Value |
|---|---:|---:|
| H1 off (fixed `TON`) | 16.6681 ns | `iL1`=124.999989 A |
| H2 ZVS admission | 50.0007 ns | `Vds(H2)`=-0.000531 V |
| H2 off (fixed `TON`) | 66.6682 ns | `iL2`=117.766 A |
| H3 nominal slot (100 ns) | 100 ns | `Vds(H3)`=11.246 V -- **not admitted, `MISSED_ZVS_SLOT`** |
| H3 turn-off | never (H3 never turned on) | -- |
| H4 nominal slot (150 ns) | 150 ns | `Vds(H4)`=13.916 V -- **not admitted, cascade from H3** |
| H4 turn-off | never | -- |
| H1 next-cycle nominal slot (200 ns = `T`) | 200 ns | `Vds(H1)`=11.978 V -- **not admitted, cascade** |

Because the four-phase controller is a single rotating state machine (one
shared `.machine` block, per A33/A35/A36), H3 never being admitted means H4
and the next H1 admission never happen either within this 205 ns window --
the rotation stalls at state `P2_M5`, correctly blocked rather than
hard-switched (`CONTROLLER_GUARD_PASS` behavior at the controller level, even
though the joint state solve overall fails).

## 4. Key voltages and currents (best candidate)

| Quantity | `t=0+` | `t=T+` | Difference |
|---|---:|---:|---:|
| `IL1` | 5.2947 A (seed) | -5.708 A | -11.003 A |
| `IL2` | 21.2051 A (seed) | 22.454 A | +1.249 A |
| `IL3` | 41.5783 A (seed) | 0.963 A | -40.615 A |
| `IL4` | 84.1447 A (seed) | -49.914 A | -134.059 A |
| `VC1` | 36.0001 V (seed) | 36.0023 V | +0.00225 V |
| `VC2` | 23.9999 V (seed) | 24.0181 V | +0.01820 V |
| `VC3` | 12.0006 V (seed) | 12.0006 V | -0.0000139 V |

`IL3` and `IL4` collapse toward small/negative values by `t=T` precisely
because phases 3 and 4 never conduct at all after their nominal slots are
missed -- their inductor current simply free-wheels/decays instead of being
replenished by a `TON` pulse, which is the dominant driver of the large
`DIL3`/`DIL4` periodicity residuals below.

## 5. Full per-residual classification (best candidate = the seed)

Target is 0 for every residual. Tolerance is `2e-4` in the residual's own
unit (A or V), matching the order of magnitude A36 itself achieved and
called converged (A36's own analogous residuals were `-1.13e-5 A` and
`-1.75e-4 V`) -- not loosened beyond that.

| # | Residual | Value | Unit | \|value\|<=2e-4? |
|---|---|---:|---|:---:|
| 1 | `peak_error_h1_a` (`iL1(TON)-125A`) | -0.0000076 | A | **CONVERGED** |
| 2 | `peak_error_h2_a` | -7.2343 | A | not converged |
| 3 | `peak_error_h3_a` | -125.0 | A | not converged (structural: H3 never conducts) |
| 4 | `peak_error_h4_a` | -125.0 | A | not converged (structural: cascade from H3) |
| 5 | `zvs_error_h2_v` (`Vds(H2)@50ns`) | -0.000175 | V | **CONVERGED** |
| 6 | `zvs_error_h3_v` (`Vds(H3)@100ns`) | 11.246 | V | not converged |
| 7 | `zvs_error_h4_v` (`Vds(H4)@150ns`) | 13.916 | V | not converged |
| 8 | `zvs_error_h1_v` (`Vds(H1)@200ns`) | 11.978 | V | not converged |
| 9 | `periodic_error_il1_a` | -11.003 | A | not converged |
| 10 | `periodic_error_il2_a` | 1.249 | A | not converged |
| 11 | `periodic_error_il3_a` | -40.615 | A | not converged |
| 12 | `periodic_error_il4_a` | -134.059 | A | not converged |
| 13 | `periodic_error_vc1_v` | 0.002247 | V | not converged |
| 14 | `periodic_error_vc2_v` | 0.018205 | V | not converged |
| 15 | `periodic_error_vc3_v` | -0.0000139 | V | **CONVERGED** |

**3 of 15 converge. 12 of 15 do not.** This is the best result found: across
174 evaluated points spanning two full optimizer attempts, no point achieved
more converged residuals than this one, and no point achieving the same
count (3) had a smaller residual norm. The globally smallest-Euclidean-norm
point actually visited (`solver_history.json` iteration 119, norm 209.40 vs.
this seed's 226.96) has **zero** converged residuals: it improved the large
`periodic_error_il3_a`/`periodic_error_il4_a` terms somewhat but only by
moving `peak_error_h1_a`, `zvs_error_h2_v`, and `periodic_error_vc3_v` away
from their converged seed values, which is a regression under this
experiment's per-residual, no-pre-weighting grading (BOUNDARY.md Section 6).
`best_candidate.json` is therefore the seed itself, not either optimizer
run's own reported "solution."

## 6. Where the first failure boundary occurred

The first and structurally dominant failure boundary is `zvs_error_h3_v`
(residual 6). This was directly diagnosed from the raw waveforms, not
inferred from the residual value alone, because a residual pinned at
exactly `-125.0 A` for `peak_error_h3_a`/`peak_error_h4_a` in every one of
174 evaluated points is exactly the signature a wiring/logic bug would also
produce, and had to be ruled out rather than assumed away:

- **The four-phase `.rule`/`.output` control tables in this netlist are
  byte-for-byte identical to A35's already-validated symmetric hybrid
  controller** (diffed directly, after normalizing the intended `Lk`-to-
  `LINDk` rename; zero differences). **The phase-3/phase-4 power-stage
  wiring is byte-for-byte identical to A33's already-validated topology**
  (diffed directly; only the intended `L3`/`L4`->`LIND3`/`LIND4` rename and
  the `VC3_INIT` parameterization of `C3`'s initial condition differ). There
  is no introduced wiring or event-ring bug.
- **H3's predecessor events do fire correctly.** Tracing the seed
  candidate's `sequence_state` trace directly: `IL3` decays from its
  41.578 A seed, crosses zero, and reaches `-INEG=-11.25 A` (state
  `P2_M4`->`P2_M5`) at `t=76.85 ns`, exactly as the P25-derived event ring
  requires.
- **`Vds(H3)` does physically reach zero** -- it is not "never seen." In the
  seed candidate it crosses to `-0.00129 V` at `t=79.166 ns`, a genuine
  bidirectional zero-crossing (confirmed by inspecting individual raw
  samples straddling the crossing). The same early crossing, in the
  `67-79 ns` range, occurs in every other inspected point across the full
  explored space, including the `lm` run's iteration 9 outlier
  (`IL4_INIT=-506 A`) and the `trf` run's final point. In every single case
  it is **20-30 ns before** the nominal 100 ns slot, and `Vds(H3)` does not
  return to `<=0` again for the remaining ~105-125 ns of the observation
  window in any evaluated point.
- This is the same `MISSED_ZVS_SLOT` phenomenon A35's RESULTS.md already
  documented for the H1-to-H2 transition (an early ~26 ns window against a
  50 ns slot) before A36's two-variable solve moved `IL1_INIT`/`IL2_INIT`
  enough to shift H2's natural crossing exactly onto its 50 ns slot. Here it
  recurs one phase later (H2-to-H3 against the 100 ns slot), and this
  experiment's joint solve was not able to reproduce A36's fix for it: the
  crossing time only moved within the same 67-79 ns band across a very wide
  parameter search (including the physically implausible outlier), which
  suggests the crossing time is not strongly sensitive to these seven
  variables in the neighborhood explored, unlike the H1-to-H2 case A36
  solved. Because the controller is one shared rotating state machine, this
  single missed slot blocks every downstream event (H4's slot and the next
  cycle's H1 slot) from ever being reached inside the 205 ns window, which is
  why residuals 3, 4, 7, 8, and most of 9-12 are downstream consequences of
  this one boundary rather than independent failures.

Separately, and only at the numerical-method level (not a physics finding):
a blind finite-difference joint Jacobian over all 15 residuals, several of
which are pinned at a flat, discontinuous `-125 A` plateau whenever
`MISSED_ZVS_SLOT` is in effect, gives the optimizer no usable local gradient
to escape that plateau -- both `lm` and `trf` stayed inside it for the
entirety of both runs, consistent with the crossing-time insensitivity
above.

## 7. Result grade

`LOCAL_PASS`. Exactly two residuals converge to numerical-edge tolerance:
`peak_error_h1_a` (residual 1) and `zvs_error_h2_v` (residual 5) -- i.e. the
H1-to-H2 local transition that A35/A36 already solved remains solved when
embedded in the full seven-variable problem. `periodic_error_vc3_v`
(residual 15) also converges, apparently coincidentally (C3's volt-second
balance over 200 ns happens to already be near zero at the seed, independent
of anything this experiment solved for). The other 12 residuals, including
all four peak-current residuals for H2/H3/H4 and all four ZVS-timing
residuals for H1/H3/H4, do not converge. Per BOUNDARY.md Section 7, this is
named exactly rather than averaged: this experiment does **not** show
four-phase 200 ns period closure, does not show H3 or H4 achieving ZVS, and
does not show full seven-state periodicity. It shows only that the
previously-established H1-to-H2 local solution survives being embedded in
the larger joint vector, plus one likely-coincidental capacitor-balance
residual.

## 8. Which module should be adjusted next

Two independent, clearly separated next actions (per Section VI/XI, neither
authorizes retuning `TON`, `Coss`, capacitor/inductor values, or the 9%
label):

1. **Physics/DOF**: H3's natural ZVS crossing is real and only ~20-30 ns
   early (67-79 ns against a 100 ns slot), the same size of mismatch A36
   closed for H1-to-H2 (an ~24 ns gap) with 2 free variables -- so a nearby
   joint solution plausibly exists. The next authorized action is either a
   directed local search that explicitly targets moving this one crossing
   time by ~25 ns (rather than a blind joint Jacobian, per point 2 below),
   or, if that is tried and fails, asking whether an additional named degree
   of freedom (e.g., explicitly solving for the nominally-fixed `a2`/`a3`
   node anchors currently held at literal 24 V / 12 V, which BOUNDARY.md
   Section 3 and this experiment left locked) is needed. This experiment
   cannot yet distinguish "no solution exists at 7 DOF" from "a solution
   exists nearby but a blind finite-difference joint search could not find
   it" -- the crossing-time insensitivity noted in Section 6 suggests the
   latter is at least plausible.
2. **Numerical method**: any future joint solve on this residual set should
   not rely on a single blind finite-difference Jacobian across
   discontinuous `MISSED_ZVS_SLOT` residuals. A staged approach (e.g. only
   admitting periodicity/ZVS residuals for phases that are not currently
   missing admission, or a derivative-free/global method for the discrete
   admission structure) is a reasonable next step; this is a solver-design
   question, not a boundary change.

## 9. Which parameters must never be changed because of this failure

Per Section XI, unchanged by this result: `TON=16.6667 ns` must never be
extended to force H3/H4 admission or reach 125 A; `Coss`, capacitor values,
and `LPHASE` must not be changed to fit a result; the 9% negative-current
label must not be raised to manufacture ZVS, and must never be reported as
the 2024 2% result; the reverse clamp must not be held active without
reverse current present (it was not, in any of the 174 runs); and the
`MISSED_ZVS_SLOT` block on H3/H4 must not be silently forced/hard-switched
to make the period appear to close. This experiment does not license
changing any of these; the two named next actions in Section 8 are the only
authorized paths forward.
