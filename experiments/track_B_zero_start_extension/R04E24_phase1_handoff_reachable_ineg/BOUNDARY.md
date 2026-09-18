# R04E24 - using a reachable I_NEG target so state 4 is actually entered (BOUNDARY)

## 0. Scope statement (unchanged from R04E21/R04E22/R04E23, restated)

Same standing limitation: **this does not test, claim, or imply P24
periodic steady-state reachability**, and does NOT attempt a four-phase
handoff. Direct, minimal follow-up to R04E23's own inconclusive result.

## 1. Parent and why this experiment exists

**R04E23** extended `TSTOP` to `100 us` and found `IL1` does NOT keep
ramping negative under R04E17's own bootstrapped initial condition
(`VC1_IC=35.86 V`, `IL1_IC=75.97 A`) with `I_LIMIT=125 A`: it reaches a
GLOBAL minimum of `-2.2150912284851074 A` at `t=2.817428674148355e-06 s`
(~`2.82 us`), then relaxes back toward zero for the rest of the run
(`-0.098 A` at `20 us`, `-0.0024 A` at `40 us`, `-0.0000236 A` at
`100 us`). Both `NEG_FRAC` targets tested there (`2%` -> `I_NEG=2.5 A`,
`7.77%` -> `I_NEG=9.7125 A`) sit ABOVE this natural peak, so state 3's
own exit condition (`I(L1)<=-I_NEG`) never fires, the machine never
reaches state 4, and R04E21's own original question (does correctly-
scaled `I_NEG` avoid R04E3's documented ZVS stall) has STILL never
actually been tested -- both R04E22 and R04E23 only ever exercised
state 3, never state 4 or beyond.

**This experiment makes exactly ONE change**: pick an `I_NEG` target
that is actually reachable given R04E23's own newly-observed natural
ceiling, so state 3 actually exits and R04E21's original question can
finally be tested for real.

## 2. What changed relative to R04E22/R04E23, exactly

- **`NEG_FRAC` changed to a single new value, `1.6%`, giving
  `I_NEG=125 A * .016 = 2.0 A`** -- chosen to sit safely BELOW R04E23's
  own observed natural peak (`2.215 A`), with a deliberate `~10%`
  margin (`2.0 A` vs `2.215 A` available), not an arbitrary new guess:
  it is the largest round value under the observed ceiling that still
  leaves margin against natural run-to-run/solver-tolerance noise. This
  is a NEW value for this project (previously only `2%` and `7.77%` had
  been tested), but it is directly derived from R04E23's own committed
  SPICE result, not an independent invention.
- **`TSTOP` kept at R04E23's own `100 us`** (not reverted to `20 us`) --
  since state 3 now exits quickly (near `2.82 us`, per R04E23's own
  observed timing), `100 us` remains ample margin to observe whatever
  happens next (state 4's own resonant ring and possible ZVS event, or
  a new stall), without yet another TSTOP-sizing iteration.
- Single cell only (not a sweep) -- this experiment tests ONE reachable
  target to see whether state 4 is entered and what happens there; a
  broader sweep of reachable targets is a natural follow-up, not
  performed here.
- Everything else -- `I_LIMIT=125 A`, phase 1's own bootstrapped initial
  conditions, `CFLY=3 uF`, phases 2-4's own hardcoded R04E3
  configuration -- copied UNCHANGED from R04E22/R04E23's own already-
  verified netlists.

## 3. What did not change

Everything except `NEG_FRAC`/`I_NEG` -- copied byte-for-byte from
R04E23's own `r04e23_neg2pct_t100us.cir` (the `TSTOP=100 us` netlist),
with only the `NEG_FRAC` parameter value edited.

## 4. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `NEG_FRAC=.016` (`I_NEG=2.0 A`) | New for this experiment: derived directly from R04E23's own committed SPICE result (natural peak `-2.215 A` at the bootstrapped operating point), chosen with ~10% margin below that ceiling | `SENSITIVITY_ONLY`, derived from this project's own prior committed result, not an external or paper-sourced value |
| Everything else | See R04E22/R04E23 `BOUNDARY.md` for original provenance | unchanged |

No new paper-sourced, cross-paper, or external-device data is
introduced.

## 5. What question this experiment answers

With an `I_NEG` target that is actually reachable given the
bootstrapped state's own natural current-excursion ceiling, does state
3 exit into state 4, and if so, does the high-side ZVS event (state
4->5, `V(vin,xmod:a1)<=0`) actually occur -- this is R04E21's own
original question, finally testable for real.

## 6. Success/failure conditions

- **State 3 exits, state 4 entered, ZVS event fires (state 5
  reached)**: confirms R04E21's own diagnosed hypothesis cleanly --
  correctly-scaled (and reachable) `I_NEG` avoids the documented stall.
- **State 3 exits, state 4 entered, but the SAME stall recurs** (state
  4, `V(vin,xmod:a1)<=0` never fires within `100 us`): the diagnosed
  hypothesis is refuted -- reaching state 4 at all is not sufficient;
  something else blocks the ZVS event even with nonzero stored negative-
  current energy.
- **State 3 still does not exit even at this lower target**: report
  this plainly -- would indicate R04E23's own observed `-2.215 A` peak
  is itself sensitive to exact timing/solver behavior and not a hard,
  reproducible ceiling; do not force a conclusion, investigate the
  discrepancy before proposing a next step.
- Phase 1's own current must stay within `+/-250 A` throughout (R04E23's
  own two cells already confirmed a `125.39 A` maximum under the same
  `I_LIMIT=125 A`; this cell is not expected to differ materially on the
  positive side).

## 7. What this experiment cannot prove

Same list as R04E21/R04E22/R04E23 Section 7/8, unchanged: does not test
P24 periodicity, does not test four-phase handoff, does not validate
R04E3 as "the" P24 controller, a positive result would not establish
what happens past state 5, does not modify any other experiment's own
committed results, no P24 reproduction claim of any kind. A single-cell
result at one reachable `I_NEG` value does not establish behavior across
the full range of reachable targets (`0` to `~2.2 A`) -- if this cell is
informative, a follow-up sweep within that range may be warranted, not
assumed necessary in advance.
