# A38 H2-to-H3 local two-residual solve boundary

Track: A (periodic steady-state reproduction). Branch: `CROSS_PAPER_EXTENSION`,
9% labelled P25 negative-current extension. Not a 2024-primary result (same
caveat as A37).

## 1. Parent experiment

A37 (`A37_p25_9pct_joint_seven_state_200ns_periodic_solve`), graded
`LOCAL_PASS`: a joint 7-variable least-squares solve over the full four-phase,
200 ns closure found no point better than its own seed. Diagnosis (recorded in
A37's `RESULTS.md`) ruled out a wiring/logic bug: H3's own predecessor events
fire correctly and `Vds(H3)` does cross zero, but 20-30 ns too early (67-79 ns)
relative to its 100 ns nominal slot — the same `MISSED_ZVS_SLOT` phenomenon
A35 documented for H1-to-H2 before A36's local two-residual solve fixed it,
recurring one phase later at H2-to-H3, uncorrected by A37's blind joint
search. A37's own RESULTS.md recommended, as the first next step, "a directed
local search targeting the ~25 ns H3 crossing-time gap specifically, rather
than a blind joint Jacobian" — confirmed with the user (2026-09-14) as the
immediate next action.

## 2. What changed relative to the parent

A37 solved (or attempted to solve) all seven state variables jointly in one
undirected least-squares search. A38 abandons that joint search and instead
replicates A35-to-A36's proven method — a small, directed, two-residual local
solve — shifted one phase forward: from "H1-to-H2" to "H2-to-H3". Only
`IL2_INIT` and `IL3_INIT` are adjusted; every other state variable is frozen
at the value it held in A37's best/seed candidate (which already includes
A36's converged `IL1_INIT`).

## 3. What did not change

- Topology, device `Coss` (GS61008T-derived, `385 pF`/`770 pF`), ideal
  reverse-conduction clamp (`Vf=0 V`, `Ron=1 mOhm`, active only while reverse
  current flows), inductor `1.4667 nH`, each phase's fixed `TON=16.6667 ns`,
  nominal `T/nP=50 ns` phase-slot origins, the `9%` labelled P25
  negative-current branch, the ideal `1 V` output clamp, and timestep — all
  identical to A37/A36/A35/A27, classifications unchanged from A37's
  BOUNDARY.md Section 3.
- `IL1_INIT = 5.2947 A`: frozen at A36's converged value (confirmed identical
  in A37's `best_candidate.json`). Classification: `NUMERICAL_IDEALIZATION`
  (a solved solver-seed coordinate, not a paper value), now treated as a
  locked upstream result rather than a free variable, per Section IV/X's rule
  that a validated local result (A36's H1-to-H2 solution) is not reopened by
  a downstream experiment without a named reason. A38 gives no reason to
  reopen it, since H1's peak and H2's ZVS residuals were both still converged
  at A37's seed (per A37's `RESULTS.md` per-residual table).
- `IL4_INIT = 84.1447433786 A`: frozen at A37's seed value (originally
  inherited from A33/A34's event-ring observation, not itself validated).
  Classification: `NUMERICAL_IDEALIZATION`, unvalidated placeholder. A38 does
  not touch phase 4 and makes no claim about it.
- `VC1_INIT=36 V`, `VC2_INIT=24 V`, `VC3_INIT=12 V` (approximately, at A37's
  seed precision): frozen at the Section VIII initial-guess table values.
  Classification: `NUMERICAL_IDEALIZATION`. A38 does not reopen capacitor
  closure; if the H2-to-H3 residuals cannot both converge with only
  `IL2_INIT`/`IL3_INIT` free, reopening a capacitor voltage is a candidate for
  a later, separately named experiment, not an automatic fallback here.

## 4. Provenance of the changed values

`IL2_INIT` and `IL3_INIT` are numerical solve outputs (`NUMERICAL_IDEALIZATION`
per Section VIII), not paper values. Their starting point for this solve is
A37's seed (`IL2_INIT=21.205095337 A`, `IL3_INIT=41.5782701063 A`, the latter
inherited unvalidated from A33/A34). The solver method itself — a local
secant/bracketing search directly mirroring
`solve_a36_two_residual_local.py`'s pattern, applied to the H2-to-H3 pair
instead of H1-to-H2 — is the documented "changed module" for this experiment,
consistent with the one-variable/one-module principle in Section V (this is
a small, explicitly-scoped two-variable local solve, not a joint-vector
exception like A37's).

## 5. Question this experiment is meant to answer

Holding every other state variable at A37's seed, does a small,
targeted two-residual local solve over `(IL2_INIT, IL3_INIT)` — the same
method that resolved H1-to-H2 in A36 — resolve H2-to-H3's `MISSED_ZVS_SLOT`
gap (H3's `Vds=0` crossing currently arrives ~20-30 ns before its 100 ns
slot) without breaking H1's already-converged peak-current and H2's
already-converged ZVS residuals?

## 6. Success condition

Both of the following converge to the same numerical-edge tolerance A36
achieved (~1e-4 scale in the respective A/V unit):

- `R1 = iL2(TON2 end) - 125 A` (phase-2's own peak current at its own fixed
  `TON` end, mirroring A36's `R1` one phase forward).
- `R2 = Vds(H3)` at the nominal `100 ns` slot, minus `0 V` (phase-3's ZVS
  admission residual, mirroring A36's `R2` one phase forward).

Additionally, `H1`'s peak-current residual and `H2`'s original ZVS-timing
residual (A36's two residuals) must still be checked and must remain
converged after `IL2_INIT` moves — A36's own boundary already warned that
adjusting `IL2_INIT` alone can move H2's already-solved ZVS time (this is the
literal mechanism A37 was built to investigate at full scale, and it applies
here too, one phase earlier). If moving `IL2_INIT` to satisfy `R1`/`R2`
breaks either of A36's original residuals, that is a reportable finding
(`NOT_PERIODIC` on the affected residual), not something to hide by
re-adjusting `IL1_INIT` without renaming the experiment.

## 7. Failure condition

- If no `(IL2_INIT, IL3_INIT)` pair satisfies both `R1` and `R2`
  simultaneously (analogous to A35's finding that the fixed-time/event-driven
  system can structurally miss a slot), grade the experiment
  `PHYSICAL_BOUNDARY_FAIL` and report exactly which residual could not be
  driven to zero and what the best achievable joint value was — do not loosen
  the `100 ns` slot definition or extend `TON2` to manufacture a match.
- If satisfying `R1`/`R2` breaks either of A36's original two residuals,
  grade the experiment `LOCAL_PASS` at best (name exactly which residuals
  hold and which broke) and record that this reopens the question of whether
  H1-to-H2 and H2-to-H3 can be solved independently in sequence at all, or
  require the joint/coupled treatment A37 already attempted — do not silently
  re-tune `IL1_INIT` to compensate without recording that as a new, separate
  change.
- Prohibited outcomes, per Section XI: extending any `TON` to reach 125 A;
  hard-switching H3 before its own `Vds=0`; holding the reverse clamp active
  without reverse current present; changing `Coss`, capacitor, inductor, or
  the 9% label to fit a result.

## 8. What this experiment cannot prove

- Not a 2024-primary (P24 2%) result; runs on the 9% `CROSS_PAPER_EXTENSION`
  branch only.
- Not a solution to the full four-phase / 200 ns closure — even full success
  here still leaves H3-to-H4 and H4-to-H1 unsolved and the 200 ns periodicity
  residuals untouched, exactly as A36's success on H1-to-H2 alone did not
  imply A37's success.
- Not evidence that sequential, one-transition-at-a-time local solves compose
  into a full periodic solution in general; A37 already showed the naive
  version of that claim (joint search from independently-solved-looking
  seeds) does not hold. A38 succeeding would show only that this specific
  adjacent pair can be solved without disturbing the previous pair — each
  further phase pair must still be checked, not assumed.
- Not evidence about zero-start (Track B), closed-loop regulation, efficiency,
  loss, thermal, EMI, or package behavior.
