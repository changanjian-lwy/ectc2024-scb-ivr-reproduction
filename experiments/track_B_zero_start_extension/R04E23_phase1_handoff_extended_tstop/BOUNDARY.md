# R04E23 - extending TSTOP so R04E22's own question can actually be tested (BOUNDARY)

## 0. Scope statement (unchanged from R04E21/R04E22, restated)

Same standing limitation: **this does not test, claim, or imply P24
periodic steady-state reachability**, and does NOT attempt a four-phase
handoff. Direct, minimal follow-up to R04E22's own inconclusive result.

## 1. Parent and why this experiment exists

**R04E22** raised `I_LIMIT` from R04E3's own `10 A` to P24's own real
`125 A` and swept `NEG_FRAC` across two already-established values --
but found neither cell's own `I_NEG` target was reached by `TSTOP=20 us`
(inherited byte-identical from R04E3/R04E21, sized for the OLD
`I_LIMIT=10 A` regime): both cells parked at state `LOW_BUILD_NEGATIVE`
(state 3) with `IL1` only reaching `-2.215 A` by `20 us`, short of both
the `2%` target (`-2.5 A`) and the `7.77%` target (`-9.7125 A`). Because
neither cell's own state-3-exit rule ever fired, the two cells were
PHYSICALLY IDENTICAL up to `TSTOP` (`NEG_FRAC` never entered the
simulated dynamics) -- R04E22's own actual question (does a correctly-
scaled `I_NEG` avoid R04E3's own documented ZVS stall) was never
actually tested, only prepared for.

**This experiment makes exactly ONE change**: extend `TSTOP` so the
state-3 negative-current build has enough time to actually reach both
swept `I_NEG` targets, allowing R04E22's own question to be tested for
real.

## 2. What changed relative to R04E22, exactly

- **`TSTOP` extended from `20 us` to `100 us`** (a `5x` margin over a
  naive linear extrapolation of R04E22's own observed rate, which
  suggested both targets would be reached only slightly past `20 us` if
  the rate stayed constant -- `100 us` is deliberately generous rather
  than a tightly-fitted minimum, since the actual `IL1(t)` trajectory's
  own nonlinearity past `20 us` is unknown and not assumed). This is a
  pure numerical-resolution/observation-window choice, not a physics
  change -- the underlying circuit, initial conditions, and `.machine`
  logic are otherwise byte-identical to R04E22's own two netlists.
- Everything else -- `I_LIMIT=125 A`, `NEG_FRAC` in `{.02, .0777}`,
  phase 1's own bootstrapped initial conditions, `CFLY=3 uF`, phases
  2-4's own hardcoded R04E3 configuration -- copied UNCHANGED from
  R04E22's own already-verified netlists.

## 3. What did not change

Everything except `TSTOP` -- copied byte-for-byte from R04E22's own two
netlists (`r04e22_neg2pct.cir`, `r04e22_neg7p77pct.cir`).

## 4. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `TSTOP=100 us` | New for this experiment: a `5x`-margin extension over R04E22's own observed rate, chosen to give ample headroom for unknown nonlinear dynamics past `20 us`, not a tightly-derived minimum | numerical-resolution/observation-window choice, not physical, not swept |
| Everything else | See R04E22 `BOUNDARY.md` for original provenance | unchanged |

No new paper-sourced, cross-paper, or external-device data is
introduced.

## 5. What question this experiment answers

With adequate observation time, does the correctly-scaled `I_NEG`
(`2.5 A` or `9.7125 A`, both far larger than R04E21's own insufficient
`0.2 A`) actually get reached, and if so, does reaching it let the
high-side ZVS event (state 4->5) occur -- this is R04E21/R04E22's own
original question, finally testable.

## 6. Success/failure conditions

- **`I_NEG` reached, state 4 entered, ZVS event fires (state 5
  reached)**: confirms R04E21's own diagnosed hypothesis cleanly.
- **`I_NEG` reached, state 4 entered, but the SAME stall recurs** (state
  4, `V(vin,a1)<=0` never fires): the diagnosed hypothesis is refuted --
  more negative-current energy alone is still not sufficient; something
  else blocks this event.
- **`I_NEG` still not reached even at `100 us`**: report this plainly
  and do not extrapolate further without another explicit, separately-
  justified `TSTOP` extension -- do not silently keep multiplying the
  window in search of a result (Ground Rule 7).
- The two `NEG_FRAC` cells may diverge in outcome (one reaches state 5,
  the other doesn't, or reaches its own target at a different time) --
  report the actual split plainly.
- Phase 1's own current must stay within `+/-250 A` throughout both
  cells.

## 7. What this experiment cannot prove

Same list as R04E21/R04E22 Section 8, unchanged: does not test P24
periodicity, does not test four-phase handoff, does not validate R04E3
as "the" P24 controller, a positive result would not establish what
happens past state 5, does not modify any other experiment's own
committed results, no P24 reproduction claim of any kind.
