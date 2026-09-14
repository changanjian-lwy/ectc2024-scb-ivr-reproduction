# A37 joint seven-state 200 ns periodic-state solve boundary

Track: A (periodic steady-state reproduction). Branch: `CROSS_PAPER_EXTENSION`,
9% labelled P25 negative-current extension. This experiment is not a
2024-primary result; see the branch policy below.

## 1. Parent experiment

A36 (`A36_local_peak_and_50ns_zvs_solve`): local two-residual solve of the
H1-to-H2 transition on the 9% branch. A36 in turn inherits A35's hybrid
fixed-`TON`/event-ZVS/slot-guard controller, A27's ideal reverse-conduction
clamp, and A24/A33's P25-rotated four-phase 9% event ring.

## 2. What changed relative to the parent

A36 solved two residuals (`IL1_INIT`, `IL2_INIT`) for one local transition,
H1-to-H2. A37 extends the same physical-event state machine to all four
phase transitions (H2-to-H3, H3-to-H4, H4-to-H1) and adds the full-period
closure condition `x(T)=x(0)`. This requires seven jointly solved free
variables instead of two, using an explicitly declared joint solve vector
(Section V one-variable exception, confirmed with Mihai 2026-09-14) rather
than a sequential single-variable method, because A36 already showed that
adjusting `IL2_INIT` alone to fix the H2 peak moves the already-solved H2 ZVS
time.

## 3. What did not change

- Topology: series-connected high-side ladder, flying capacitors, grounded
  low sides, one output inductor per phase (2024 Fig. 3; 2025 Fig. 1).
  Classification: `P24_EXPLICIT` (ladder, capacitors, output inductor),
  `P25_SUPPLEMENT` (grounded low-side connection).
- Device `Coss`: GS61008T-derived commutation capacitance, `385 pF` high-side,
  `770 pF` low-side; snubbers remain zero. Classification:
  `EXTERNAL_DEVICE_DATA` (GS61008T datasheet-derived Coss),
  `UNKNOWN_BLOCKING` (real snubber value, held at zero).
- Ideal reverse-conduction clamp from A27: `Vf=0 V`, `Ron=1 mOhm`, valid only
  while reverse current is present. Classification: `NUMERICAL_IDEALIZATION`.
- Inductor: `1.4667 nH` from the printed 2024 Eq. (4). Classification:
  `P24_EXPLICIT` (the equation and the recalculated value); the Table I
  `2.68 nH` entry remains a separate, non-adopted `P24_EXPLICIT` conflict
  record and is not a candidate value here.
- Each phase's high-side fixed on-time `TON=16.6667 ns`. Classification:
  `P24_EXPLICIT` (Eq. 1/3). Never extended to manufacture 125 A.
- Nominal phase-slot origins `T/nP=50 ns` (`0/50/100/150 ns`). Classification:
  `P24_EXPLICIT` (phase interleaving) combined with `CROSS_PAPER_EXTENSION`
  (rotating the P25 module-shift convention to `nP=4`, per
  `SEQUENCE_SOURCE_MATRIX.md`). `50 ns` is a phase slot, not a commutation
  duration.
- Negative-current label for this pass: `9%`. Classification:
  `CROSS_PAPER_EXTENSION` of the `P25_SUPPLEMENT` 5-10% range, currently fixed
  at the `SENSITIVITY_ONLY` value already adopted by A24/A33/A35/A36. It must
  never be reported as the `P24_EXPLICIT` 1-2% boundary.
- Output boundary: the existing ideal `1 V` output-isolation clamp.
  Classification: `NUMERICAL_IDEALIZATION`.
- Timestep: inherited from A35/A36. Classification: `NUMERICAL_IDEALIZATION`.
- Event-driven control latching: low-side opening, negative-current cutoff and
  high-side ZVS admission remain physical-event controlled and latched per
  Section VII, never time-forced. A phase reaching its `50 ns` slot with
  `Vds != 0` is blocked from hard turn-on and must record `MISSED_ZVS_SLOT`.

## 4. Provenance of the changed values

The seven jointly solved free variables are numerical solve outputs, not
paper values. Classification: `NUMERICAL_IDEALIZATION` (they are solver-seed
state coordinates per Section VIII, not demonstrated zero-start or
hardware-measured quantities):

| Variable | Meaning |
|---|---|
| `IL1_INIT` | Phase-1 inductor current at global `t=0` (phase-1 `H1` turn-on origin) |
| `IL2_INIT` | Phase-2 inductor current at the same instant |
| `IL3_INIT` | Phase-3 inductor current at the same instant |
| `IL4_INIT` | Phase-4 inductor current at the same instant |
| `VC1_INIT` | Flying-capacitor `C1` voltage at the same instant |
| `VC2_INIT` | Flying-capacitor `C2` voltage at the same instant |
| `VC3_INIT` | Flying-capacitor `C3` voltage at the same instant |

The joint least-squares (or equivalent joint-Newton) solver method itself is
the single documented "changed module" for provenance purposes, per the
Section V exception Mihai confirmed for this experiment class only. It does
not apply to any other experiment in this project.

## 5. Question this experiment is meant to answer

Does the P24 four-phase event-ring state machine (H1-H4), running on the
labelled 9% P25 negative-current extension with all other A27/A35/A36
boundaries fixed, admit a seven-state vector
`x=[VC1,VC2,VC3,IL1,IL2,IL3,IL4]` (output excluded, held by the ideal 1 V
clamp) that jointly satisfies, or partially satisfies, the peak-current,
ZVS-timing and full-period-closure residuals defined below? Which of these
residuals are structurally satisfiable together at this degree of freedom,
and which are not?

## 6. Success condition

Per Mihai's 2026-09-14 decision, no residual is pre-weighted or prioritized.
One combined joint least-squares (or equivalent joint-Newton) solve is run
over the full residual set below; success is graded per-residual after
observing convergence, not assumed in advance:

- 4 peak-current residuals: `iLk(TON end) - 125 A`, `k=1..4`.
- 4 ZVS-timing residuals: `Vds(H_{(k mod 4)+1})` at the nominal slot
  `k*50 ns`, minus `0 V`.
- 7 periodicity residuals over `T=200 ns`: `ILk(T)-ILk(0)` for `k=1..4`,
  `VCj(T)-VCj(0)` for `j=1..3`.

A residual is `PASS` if it converges to numerical-edge tolerance (consistent
with A36's `~1e-4` scale). The overall experiment is `PASS` only if all 15
residuals converge; this is not expected given the 7-DOF system.

## 7. Failure condition

- Any residual that does not converge is recorded individually, not averaged
  away. Grade each per-residual outcome as `PASS`, `PHYSICAL_BOUNDARY_FAIL`
  (a physical event, e.g. `Vds=0`, was not reached), or `NOT_PERIODIC` (an
  `x(T)-x(0)` residual did not close).
- If the joint solve stalls or diverges before producing a candidate, grade
  the experiment `BLOCKED_BY_MISSING_DATA` only if the blocker is a genuinely
  missing paper/device parameter, otherwise `REJECTED` if the solve method
  itself has a principled error (e.g. an algebraic chatter loop as seen in
  earlier R03B/R03C history).
- If some residuals converge and others do not, grade the experiment
  `LOCAL_PASS` and name exactly which residuals passed, per Section IV
  RESULTS.md item 6-7. No residual's target or tolerance may be redefined
  after the fact to convert a failure into a pass.
- Prohibited outcomes, per Section XI: extending any `TON` to reach 125 A;
  hard-switching a high side before its `Vds=0`; holding the reverse clamp
  active without reverse current present; changing `Coss`, capacitor,
  inductor or the 9% label to fit a result.

## 8. What this experiment cannot prove

- Not a 2024-primary (`P24_EXPLICIT` 1-2%) reproduction result while running
  on the 9% `CROSS_PAPER_EXTENSION` branch. A separate, later experiment
  (candidate name `A38_p24_2pct_joint_seven_state_200ns_periodic_solve`) must
  repeat this identical method on the 2% branch and report its own result
  independently; A20 already shows the 2% branch fails the local H1-to-H2 ZVS
  test under the sequential method, so failure on this branch is a plausible,
  reportable outcome for A38, not a reason to retune A37.
- Not a complete four-module, four-module-interleaved, or hardware
  reproduction.
- Not evidence about zero-start (Track B), closed-loop output regulation,
  efficiency, loss, thermal, EMI, or package behavior.
- A `PASS` or `LOCAL_PASS` grade here never authorizes claiming "the 2024
  paper's four-phase period is reproduced"; it authorizes only the
  per-residual claims actually observed.
