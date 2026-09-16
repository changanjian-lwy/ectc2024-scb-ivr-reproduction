# R04E16 - Roberts' soft-start mechanism on fixed-timing four-phase PWM (BOUNDARY)

## 1. Parent and why this experiment exists

**Roberts' PhD dissertation, Chapter 3 Section 3.5** (`paper_locked/00_boundaries/
ROBERTS_PRODIC_2024_LITERATURE_REVIEW.md`'s "Follow-up" section) describes
ramping `Vin` itself slowly through an eFuse, bandwidth-limited well below
the flying-capacitor resonance, while the converter's own normal
multiphase switching pattern runs unchanged -- a mechanism this project
has not yet built or tested. `ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`
derived P24-specific candidate ramp times (`~31-117 us` depending on the
still-unconfirmed `Cfly`, using Roberts' own `30x`-margin convention) but
built no SPICE model. This experiment is the first to actually build and
run that mechanism, per explicit user direction 2026-09-16: **"所以相当于
也是把这个人的方法外延到我们的文章之中，这个边界一定要标记清楚，你可以
开始设计实际的SPICE边界了"** (this is extending Roberts' own method into
this project's own model; the boundary must be clearly marked; begin
designing the actual SPICE boundary).

## 2. Critical scope distinction -- what "normal switching pattern" means
   here, and why this is NOT a repeat of R04E5's already-falsified
   combination

Roberts' own text says the converter's "normal gate-drive/PWM pattern"
runs during the ramp. This project has THREE structurally different
things that could all be called "the switching pattern," and conflating
them would be a real error:

1. **R04E9-R04E15's admission-order state machine** (`CHARGE_k`/`FREE_k`,
   invented specifically for zero-start bootstrapping) -- NOT what Roberts
   describes; his mechanism assumes the converter's ORDINARY periodic
   modulation, not a special bootstrap sequencer.
2. **The strict, physically-event-gated ZVS controller** (R04E3's own
   construct, the one R04E5 grafted a ramp/timeout onto and found
   permanently stalls at zero energy regardless of timing, because it
   waits for a physical current/voltage event that cannot occur without
   pre-existing current) -- `README.md`'s own explicit standing warning
   states: **"Do not re-attempt 'keep the strict full P24 admission chain,
   just add a ramp/timeout on top of it' as a zero-start fix -- this has
   now been tried and it cannot work by construction, not by bad luck."**
   This experiment MUST NOT be this combination.
3. **Fixed-timing, non-event-gated, open-loop four-phase PWM** -- gate
   signals that are pure functions of absolute time (fixed `T/4`-shifted
   phase intervals, fixed `Ton`), with NO dependency on any voltage or
   current state anywhere. This is what Roberts' own description actually
   matches (a normal, steady-state-timed modulation pattern, not an
   event-driven bootstrap sequencer), and it is ALSO the exact pattern
   already used and diagnosed in this project's own **R03A**
   (`paper_locked/02_ectc2024_main/spice/
   R03A_passive_precharge_to_fixed_pwm_takeover.cir`, gate B-sources
   `BH1..BH4`/`BL1..BL4`, fixed `D=1/12`, conventional `1->2->3->4`
   sequence, non-overlapping high sides, complementary low sides, no ZCD/
   dead time/event-gating of any kind).

**This experiment uses option 3, reusing R03A's own exact gate-generation
formulas.** This is a genuinely different, not-yet-falsified combination
from R04E5's own falsified one, for a specific, stated causal reason
(Section 3).

## 3. Why R03A's own negative finding does not pre-invalidate this
   experiment

R03A itself already tested fixed-timing PWM and found catastrophic
current runaway (phase peaks `563-884 A`, `Vout` overshoot to `1.54 V`)
-- but R03A's own causal diagnosis (`STEP_07_R03_PRECHARGE_PWM_TAKEOVER.md`)
is specific: **`Vin` was already ramped to its FULL `48 V` value
(`TRAMP=100 us`), and the fixed-`5 MHz` PWM was switched on suddenly at
`TSTART=150 us`, well after `Vin` had settled, onto a system whose `Vout`
was still near zero.** The causal chain R03A itself states: "At startup
`Vout` is low, so the OFF-interval inductor slope `-Vout/L` is too small
for current to return to zero before the next fixed `5 MHz` opportunity" --
i.e. the failure is specifically about applying FULL-STRENGTH (`Vin=48 V`)
switching pulses onto a cold (`Vout~=0`) system.

**This experiment's whole mechanism is designed to avoid exactly that
scenario**: `Vin` itself is near zero at the same time the switching
pattern is active, so the ON-interval charging slope `(Vin-Vout)/L` starts
near zero (not `48 V`-strength) and grows only as `Vin` itself grows,
giving `Vout`/the ladder time to develop in step with `Vin` rather than
being hit with full-strength pulses while still cold. Whether this
actually avoids R03A's own diagnosed accumulation failure is an empirical
question this experiment is built to answer, not something assumed here.

## 4. What changed relative to R03A, exactly

- **`TSTART=0`** (PWM active from the very start, not delayed to `150 us`
  after `Vin` has already settled) -- the single most important change,
  directly implementing "the normal pattern runs during the ramp."
- **The `Vin` ramp itself becomes the swept variable under test**
  (`TRAMP` derived from `ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`,
  Section 6), not a fixed `100 us` R02B-derived value.
- **`LPHASE=1.4666667 nH`** (Eq.-4 branch, this project's own standing
  value used throughout R04E3-R04E15) REPLACES R03A's own `2.68 nH`
  (the Table-I discrepancy value `CURRENT_ASSUMPTION_CROSSCHECK.md`'s
  "Inductor" row already flags as unresolved) -- for consistency with the
  rest of this project's active-netlist lineage, not a silent
  substitution.
- **`CFLY`** swept across the first-principles `0.6-8.7 uF` range
  (`CFLY_FIRST_PRINCIPLES_ESTIMATE.md`) REPLACES R03A's own
  cross-topology-suspect `53.8 uF`.
- **The R02B passive-divider precharge network is REMOVED ENTIRELY**
  (`CIN1-4`, `RLEAK1-4`, `DPC1-3`, `CDIV`) -- true zero-energy start with
  NO separate precharge circuit of any kind. This tests Roberts'
  mechanism in its purest form: does the `Vin` ramp ALONE, with no
  auxiliary precharge network, bootstrap both the ladder and `Vout`?
- **Per the framework/module principle restated by the user 2026-09-16**
  ("我们现在以及以后做的不能受到数值的影响...先打框架再来带入" -- the
  circuit's structure must not be hard-coded to any single unconfirmed
  numeric value): `CFLY`, `TRAMP`, and the margin factor are all built as
  `.param` inputs to an otherwise-unchanged netlist structure, swept as a
  grid (Section 6), not picked once and hard-coded.

## 5. What did not change

- The four-phase P24 power-stage connectivity (`SH1-4`/`CF1-3`/`SL1-4`/
  `L1-4`, `out` node) -- copied unchanged from R03A.
- The gate-generation B-source formulas themselves (`BH1..BH4`/
  `BL1..BL4`, fixed `T/4`-shifted, non-overlapping high sides,
  complementary low sides, `D=NP*VOUT/VIN=1/12`, `TON=D*T`) -- copied
  unchanged from R03A except `TSTART=0` (Section 4).
- `COUT=4.672 mF` (still-flagged cross-topology candidate, NOT corrected
  here -- same deliberate scope limit R04E8-R04E15 all declared) and
  `RLOAD=Vout_target^2/Pout` (P24's own formula, `Pout=250 W`) -- UNLIKE
  R04E9-R04E15's own bootstrap-only, open-output convention, this
  experiment KEEPS a real resistive load, because Roberts' own mechanism
  is meant to address `Vout` bootstrap under load, not just the flying-
  capacitor ladder in isolation (matching his own Fig. 3.12 example,
  which also includes `Cout`/`Rload`). This is a deliberate scope
  difference from R04E9-R04E15, stated explicitly, not an oversight.
- Ideal switch model (`SWI`, `Ron=1u`/`Roff=1T`), `RLDAMP=1u` inductor
  damping -- copied unchanged from R03A. No GS61008T Coss data is added in
  this first test (a second conceptual change beyond this experiment's
  single-change scope; a candidate follow-up, not done here).
- True-zero-energy initial conditions (`UIC`, no `IC=` statements on any
  capacitor or inductor) -- unchanged from R03A/every Track-B experiment.
- `TMAX=50 ps` (matching R04E9-R04E15's own numerical-resolution
  convention for this class of circuit).

## 6. Swept grid

**Grid 1 -- matched `(Cfly,Tramp)` pairs at Roberts' own `30x` margin**
(from `ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md` Section 2, the
project's own primary candidate range): `(Cfly=0.6 uF, Tramp=30.68 us)`,
`(Cfly=3 uF, Tramp=68.61 us)`, `(Cfly=8.7 uF, Tramp=116.84 us)` -- 3 cells.

**Grid 2 -- margin-factor sensitivity at `Cfly=3 uF`** (testing
`ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`'s own flagged caveat that
`30x` is Roberts' own unjustified choice, not a derived optimum):
`10x` margin (`Tramp=22.87 us`), `100x` margin (`Tramp=228.71 us`) -- 2
cells (`30x` already covered by Grid 1's `Cfly=3 uF` cell).

**Control cell -- near-instantaneous ramp** (`Cfly=3 uF`,
`Tramp=1 us`, matching R02B/R04E14's own fastest-tested `Tramp` value):
tests whether THIS netlist (fixed-timing PWM from `t=0`, no precharge
network) reproduces R03A-style current runaway when the "slow ramp" idea
is effectively absent -- the counterfactual establishing that any
difference in the other 5 cells is attributable to the ramp itself, not
to some other silent change (removing the passive divider, correcting
`Lphase`/`Cfly`, etc.).

Total: 6 cells. `TSTOP = TRAMP + 300 us` per cell (giving `1500` switching
periods of settling time after the ramp completes, at `T=200 ns`).

## 7. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `TSTART=0` (PWM active from the start) | This experiment's single core mechanism, implementing Roberts' dissertation Section 3.5's own described method | `CROSS_PAPER_EXTENSION` (author's own general method, applied to P24's specific untested operating point) |
| `TRAMP` values (Grids 1/2) | `ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`, itself derived from Roberts' Eq. 3.44 + his own `30x`-margin convention applied to P24's `LOCKED` `D`/`L` values | `CROSS_PAPER_EXTENSION` |
| `CFLY` range `0.6-8.7 uF` | `CFLY_FIRST_PRINCIPLES_ESTIMATE.md` | `SENSITIVITY_ONLY`, inherited |
| `LPHASE=1.4666667 nH` | Eq.-4 branch, this project's own standing value (R04E3-R04E15) | `P24_EXPLICIT` (Eq.-4 branch) |
| `COUT=4.672 mF` | Still-unconfirmed EPE2019 cross-topology candidate, unchanged | cross-topology candidate, flagged unconfirmed |
| `D=1/12`, `TON`, fixed `T/4` gate-generation formulas, `RLOAD` formula | R03A's own construct, itself `P24_EXPLICIT`-derived (`D=NP*Vout/Vin`) plus the OJPEL-2024-cited non-overlap constraint (`STEP_07`'s own "Modulation boundary" section) | inherited from R03A, `P24_EXPLICIT`/`CROSS_PAPER_EXTENSION` mix, unchanged |
| Removal of R02B's passive divider network | This experiment's own scope choice (test Roberts' ramp mechanism in isolation, without an auxiliary precharge circuit) | scope decision, not a paper value |
| `30x`/`10x`/`100x` margin factors | Roberts' own `30x` choice (unjustified by him beyond "significantly below"), `10x`/`100x` added here as this experiment's own sensitivity bracket | `SENSITIVITY_ONLY` |

**No new paper-sourced, cross-paper, or external-device data is
introduced beyond what is already itemized above.** The entire mechanism
under test is explicitly `CROSS_PAPER_EXTENSION`: Roberts' own general
`N`-inductor SCB theory, applied to an operating point (P24's specific
`Vin`/`L`/`Cfly` combination) that neither he, P24, nor P25 worked out
numerically or combined with this specific fixed-timing gate pattern.

## 8. What question this experiment is meant to answer

Does ramping `Vin` slowly (per Roberts' own bandwidth-margin design rule,
applied to P24's own operating point) while running P24's ordinary fixed-
timing, non-event-gated four-phase PWM from `t=0` -- with NO separate
precharge circuit -- bootstrap both the flying-capacitor ladder AND
`Vout` (under a real resistive load) without the catastrophic current
runaway R03A found when the same fixed-timing pattern was applied
suddenly at full `Vin` to a cold `Vout`? Is the answer sensitive to
exactly which `Cfly` (hence which derived `Tramp`) is used, and to the
unjustified `30x` margin choice?

## 9. Success condition

`CONTROLLER_GUARD_PASS`-style success (this project's own established
bar for a bootstrap-only-until-now problem): phase currents stay within
the `+/-250 A` safety bound R04E5/R04E9-R04E15 all adopted, `Vout` and
`VC1-3` do not diverge, and ideally approach `1 V`/`36/24/12 V` without a
large overshoot (unlike R03A's own `1.54 V` `Vout` overshoot).
`LOCAL_PASS`-style success: additionally reaches within the same handoff
tolerance bands R04E9-R04E15 used (`Vout` within `5%`, `VCk` within `2%`)
by `TSTOP`.

## 10. Failure conditions

- `PHYSICAL_BOUNDARY_FAIL`: any phase current exceeds `+/-250 A`, or
  approaches R03A's own `563-884 A` scale -- reported as direct evidence
  the ramp mechanism does NOT avoid R03A's diagnosed failure mode.
- `NOT_PERIODIC`/divergence: `Vout`/`VC1-3` fail to settle or oscillate
  without bound after the ramp completes.
- The control cell (near-instant ramp) failing to reproduce
  runaway-like behavior would itself be a notable, separately-reportable
  finding (it would mean removing R02B's passive network or correcting
  `Lphase`/`Cfly` changed the outcome independent of the ramp idea,
  undermining this experiment's own counterfactual design) -- reported
  plainly if it happens, not silently accepted as "the ramp must be
  responsible."
- Solver non-convergence -- reported as its own outcome, not retried with
  loosened tolerances.

## 11. What this experiment cannot prove

- It does not validate GS61008T device-level switching behavior (Coss,
  dead time, ZVS) -- ideal switches only, same limitation R03A itself
  declared.
- It does not establish that `30x` (or any tested margin) is "correct" --
  all remain `SENSITIVITY_ONLY`.
- It does not establish which single `Cfly` value is correct -- still
  pending Mihai's confirmation.
- It does not validate the ground-referenced-vs-floating flying-capacitor
  question R04E14/R04E15 already flagged for the PASSIVE module -- this
  experiment uses the REAL floating adjacent-capacitor connection (R03A's
  own `SH/CF/SL` topology, same as R04E9-R04E15's active netlists), so
  that specific R02-family caveat does not apply here; a different one
  does: whether a fixed-timing (non-ZVS) switching pattern is an
  acceptable steady-state target at all is a separate, already-flagged
  Track-A question this experiment does not address.
- A positive result here would show this SPECIFIC mechanism (fixed-timing
  PWM + Vin ramp, no auxiliary precharge circuit) can avoid R03A's
  diagnosed failure mode at this specific parameter combination -- it
  would not, by itself, constitute a P24 reproduction claim, nor would it
  supersede R04E9-R04E15's or R04E14/R04E15's own findings, which remain
  valid for their own respective mechanisms.
- It does not build or test the handoff into R04E3's own strict
  event-gated steady-state controller -- if this mechanism succeeds at
  bootstrapping close to target, a SEPARATE future experiment would still
  need to build that handoff explicitly, per the standing
  `ROBERTS_PRODIC_2024_LITERATURE_REVIEW.md` requirement that any such
  handoff be self-labelled as an engineering hypothesis, not a
  literature-derived rule.
