# A49 - cross-checking the parallel math model's affine periodic-orbit seed against the real-device, real-dead-time A37 construct (BOUNDARY)

Track: A (periodic steady-state reproduction). Branch: `CROSS_PAPER_EXTENSION`
(9% negative-current branch, inherited from A35/A36/A37 unchanged), plus a
new `CROSS_PAPER_EXTENSION`-adjacent seed source (Section 4).

## 0. Scope statement

This does not claim a P24/P25 periodic-state reproduction. It is a
cross-check between two independently-built models already present in
this repository, on two different tracks maintained by different
efforts: (1) `src/scb_ivr/`'s own ideal-switch, ideal-diode affine-map
periodic-orbit solution (`results/ZERO_START_AFFINE_PERIOD_FIXED_
POINT.md`), and (2) this project's own real-device, event-driven,
four-phase SPICE construct (`A37`, unchanged in controller topology).
It answers one narrow question: does the ideal-switch model's own
predicted steady-state seed, when given to the real-device model as an
initial condition, hold together (small one-period closure error, all
four phases achieving genuine ZVS admission) -- or does it immediately
diverge, revealing that the "missing factor" (real switching-node
capacitance and event-driven, not fixed, dead time) makes a first-order
difference?

## 1. Parent experiment and why this exists

**Parent: `A37`** (`A37_p25_9pct_joint_seven_state_200ns_periodic_solve/
A37_p25_9pct_joint_seven_state_200ns_periodic_solve.cir`), this project's
own best prior real-device four-phase periodic-seed attempt: real
GS61008T device capacitance/RDS_on (`GS61008T_typical_params.lib`,
`GS61008T_commutation_capacitance.lib`), a genuinely event-driven
(not fixed-timer) `.machine` construct gating each phase's own high-side
turn-on on BOTH its nominal `T/4` slot AND its own real `Vds<=0` event,
`IPEAK=125 A`, `NEG_FRAC=.09` (the `9%` branch). A37's own best
optimizer-found seed (174 points explored across two full attempts) had
only 3 of 15 residuals converged, and phases `H3`/`H4` never achieved
their own ZVS admission at any explored point -- the optimizer-driven
search never found a working seed.

**This session's separate cross-check work (documented in
`experiments/track_B_zero_start_extension/CONSOLIDATED_FINDINGS_
2026-09-16.md`, "Cross-check against the parallel math-model effort's
newly-found periodic orbit")** found that the parallel `src/scb_ivr/`
effort independently solved a genuinely self-consistent periodic orbit
under an IDEAL-switch boundary (one-period closure error `2.3e-8`, map
residual `2.6e-11`) -- but that model structurally cannot need or show a
ZVS gap, since ideal switches transition instantaneously. A smaller
single-phase test (Track B's `R04E26`) already showed that swapping only
one phase's own initial condition into R04E3's own single-phase-isolated
construct reproduces the same stall as before (no new information beyond
confirming a structural insensitivity). Per explicit user direction, this
experiment now performs the larger version instead: feed the ideal-switch
model's OWN periodic-orbit state into A37's own already-built real-device,
real-dead-time, FULL FOUR-PHASE construct, instead of guessing/optimizing
a seed as A24-A37 did.

## 2. What changed relative to A37, exactly

- **`CFLY` corrected from A37's own inherited `4*10u+2*4.7u+2*2.2u=53.8 uF`
  (the old cross-topology-suspect value, never updated in Track A) to
  `3 uF`** -- REQUIRED, not optional: the periodic-orbit state being
  imported was solved by the math model under its own frozen boundary
  `CFLY=3 uF` (`ZERO_START_AFFINE_PERIOD_FIXED_POINT.md` Section
  "Question"). Importing a voltage state solved for one capacitance value
  into a circuit with an `18x` larger capacitance would be physically
  inconsistent (same correction Track B's own `R04E8`/`R04E21` already
  made for the same reason). `3 uF` is Track B's own already-corrected,
  already-used-throughout (`R04E8`, `R04E16-R04E26`) middle value.
- **The seven state-vector initial conditions (`VC1_INIT`, `VC2_INIT`,
  `VC3_INIT`, `IL1_INIT`, `IL2_INIT`, `IL3_INIT`, `IL4_INIT`) replaced**,
  from A37's own inherited optimizer-search values (A36/A33/guess-table
  provenance), with values read from the math model's own periodic-orbit
  result -- see Section 4 for the exact source and the explicit
  approximation this requires.
- Nothing else changes: `IPEAK=125 A`, `NEG_FRAC=.09`, `LPHASE=
  1.466666666666667 nH`, `COUT=4.672 mF` (`{8*220u+32*47u+64*22u}`,
  confirmed by direct computation to already equal the math model's own
  frozen `Cout=4.672 mF`), `VIN=48 V` constant (no ramp -- this
  experiment starts from an already-charged state, it is not a zero-start
  test), `FSW=5 MHz`, the full 20-state `.machine` block's own rule
  structure, `T0=0`, real device library includes, all `.meas`
  instrumentation -- copied byte-for-byte from A37's own already-verified
  netlist.

## 3. What did not change

Everything except `CFLY` and the seven initial-condition values -- copied
byte-for-byte from A37's own netlist, including its own controller
topology, its own `9%` `NEG_FRAC` branch (not re-litigated here), its own
`.meas` instrumentation set (reused unchanged so this run's results are
directly comparable to A37's own already-published numbers, residual by
residual).

## 4. Provenance of every changed/new value -- explicit classification

| Value | Source | Category |
|---|---:|---|
| `CFLY=3 uF` | Track B's own `R04E8` correction, already used throughout `R04E16-R04E26`; also matches the math model's own frozen boundary in `ZERO_START_AFFINE_PERIOD_FIXED_POINT.md` | `NUMERICAL_IDEALIZATION`-adjacent engineering correction (not a P24/P25 value; A37's own prior `53.8 uF` was itself never a P24/P25 value either, see A37's own BOUNDARY.md Section 3) |
| `VC1_INIT=35.8448`, `VC2_INIT=23.8863`, `VC3_INIT=11.9278` (V) | `results/ZERO_START_AFFINE_PERIOD_FIXED_POINT.md`, "One-period electrical metrics" table, "Average flying-capacitor voltages" row, quoted verbatim to the source's own published precision | `CROSS_PAPER_EXTENSION`-adjacent: sourced from the parallel math-model effort's own already-published, self-consistency-checked periodic-orbit solution (map residual `2.6e-11`, one-period closure error `2.3e-8`) -- NOT a P24/P25 paper value, NOT independently re-derived by this session. Using the period AVERAGE for all three capacitor voltages is a reasonable, low-risk approximation since large flying capacitors change little within one switching period; this is a minor approximation, not a major one. |
| `IL1_INIT=0.111` (A) | Same source document, "Phase-current minima" row, first value (phase 1) | `CROSS_PAPER_EXTENSION`-adjacent, same source as above. **This is the one initial condition chosen for a specific physical reason, not just convenience**: A37's own `.machine` construct starts (`T0=0`, state `P1_M1`) exactly at the instant phase 1's own high side turns on, which is precisely the instant right after phase 1 completes its own negative-current-build/ZVS-admission sequence -- i.e., phase 1's OWN current minimum. Using the periodic orbit's own reported phase-1 minimum for `IL1_INIT` is therefore a physically motivated match to what this specific sampling instant represents, not an arbitrary choice among the three reported statistics (avg/max/min). |
| `IL2_INIT=62.724`, `IL3_INIT=62.724`, `IL4_INIT=63.033` (A) | Same source document, "Average phase currents" row, second/third/fourth values | `CROSS_PAPER_EXTENSION`-adjacent, same source. **Explicitly flagged as the weakest approximation in this experiment**: at `T0`, phases 2/3/4 are each partway through their OWN individual cycle (offset by `T/4`, `T/2`, `3T/4` respectively from phase 1's own reference instant), not at their own commutation instant -- the source document reports only period-averaged/extremal statistics per phase, not the full instantaneous multi-phase state at one shared timestamp (this remains the same open gap `MINIMUM_INFORMATION_REQUEST.md` Item 9 already documents). Using each phase's OWN period average as a "typical mid-cycle" proxy is a defensible, clearly-labeled choice, not a validated four-phase snapshot -- if this experiment's own result is sensitive to this specific choice, that sensitivity itself would be worth reporting, not concealed. |
| Everything else (`IPEAK=125`, `NEG_FRAC=.09`, `LPHASE`, `COUT`, device library values, `.machine` structure) | See A37 `BOUNDARY.md` for original provenance -- unchanged | unchanged |

No new paper-sourced or external-device data is introduced beyond what
A37 already used. This is the first experiment in this project to import
a full multi-variable state from the parallel math-model effort into a
real-device Track-A SPICE construct.

## 5. What question this experiment answers

Does the ideal-switch math model's own independently-solved periodic
orbit, when given (with the explicitly-flagged single-instant
approximation above) to the real-device, real-event-driven-dead-time A37
construct as a starting state, produce a smaller one-period closure error
and/or more successful ZVS admissions (fewer `MISSED_ZVS_SLOT` cases)
than A37's own best 174-point optimizer search ever found? Or does it
diverge immediately, similarly to or worse than A37's own best candidate?

## 6. Success/failure conditions

- **Smaller closure error AND/OR more phases achieving genuine ZVS
  admission than A37's own best candidate (3/15 residuals, H3/H4 never
  admitted)**: a genuinely significant result -- would suggest the
  ideal-switch periodic orbit's own state is closer to a real
  steady-state solution than anything the optimizer search found on its
  own, and would justify a follow-up (e.g. requesting the math-model
  effort's own true per-phase instantaneous snapshot to remove this
  experiment's own approximation, per Section 4's flagged gap).
- **Comparable or worse closure error, similar or more admission
  failures**: reinforces the conclusion already reached in Track B's own
  `R04E24`/`R04E25`/`R04E26` chain -- that the ideal-switch model's own
  predicted state does not straightforwardly transfer to a real ZVS
  admission requirement, most likely because the ideal model structurally
  has no ZVS energy requirement to satisfy in the first place. Report
  which specific phases fail (via the same `MISSED_ZVS_SLOT`-style
  diagnostic A37's own `.meas` set already provides) and by how much,
  plainly.
- **Solver failure (non-monotonic time, singular matrix, or a corrupted
  `.raw` trace)**: report as a genuine negative result per this project's
  own Ground Rule 7, not retried silently with different tolerances
  without saying so.
- All four phase currents must stay within `+/-250 A` throughout (A37's
  own prior runs already establish this construct's own typical current
  range; not expected to differ materially given `IL_INIT` values here
  are all smaller than A37's own inherited seed's `IL4_INIT=84.14 A`).

## 7. What this experiment cannot prove

- It does not resolve `MINIMUM_INFORMATION_REQUEST.md` Item 9's own
  standing gap (a true simultaneous four-phase instantaneous snapshot) --
  it uses an explicitly-flagged approximation instead (Section 4).
- It does not modify, touch, or depend on `src/scb_ivr/` or `results/`
  beyond reading and quoting the one already-published document cited
  above -- consistent with this project's own established boundary
  discipline of not touching the other track's own work area.
- It does not modify A37's own committed files -- A37's own netlist is
  copied, not edited in place.
- A positive result (smaller closure error / more ZVS admissions) would
  NOT itself constitute a P24/P25 periodic-state reproduction claim --
  it would motivate further, more careful follow-up (removing the
  Section 4 approximation), not be reported as a completed reproduction.
- It does not change or re-litigate A37's own `NEG_FRAC=.09` branch
  choice, nor attempt the P24-primary `1-2%` branch -- that remains a
  separate, unstarted thread per A37's own BOUNDARY.md Section 8.
- Consistent with this project's own standing practice, the math model's
  own underlying Python solver code was not independently re-verified by
  this session -- only the specific numbers explicitly quoted here were
  checked for faithful transcription against the source `results/*.md`
  file.
