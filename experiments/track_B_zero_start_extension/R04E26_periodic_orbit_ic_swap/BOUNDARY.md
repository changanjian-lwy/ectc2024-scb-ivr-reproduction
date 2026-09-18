# R04E26 - swapping R04E21's own initial condition for the math model's periodic-orbit state (BOUNDARY)

## 0. Scope statement (unchanged from R04E21-R04E25, restated)

Same standing limitation: **this does not test, claim, or imply P24
periodic steady-state reachability**, and does NOT attempt a four-phase
handoff. Minimal, single-variable-change follow-up to R04E21, chosen by
explicit user direction over the larger alternative (bootstrapping the
full four-phase real-device power stage from the periodic orbit's
complete state) as the cheaper, smaller-scope option to try first.

## 1. Parent and why this experiment exists

**Cross-track finding (documented in `CONSOLIDATED_FINDINGS_2026-09-16.md`,
"Cross-check against the parallel math-model effort's newly-found
periodic orbit")**: the parallel math-model effort's own newly-solved
ideal-switch periodic orbit (`results/ZERO_START_AFFINE_PERIOD_FIXED_
POINT.md`) reports natural per-phase current minima of only `0.111` to
`-0.214 A` -- roughly 50x smaller than the `~10.6 A` R04E25 found is
needed to close R04E3's own state-4 ZVS gap, and much closer to R04E3's
OWN ORIGINAL `I_NEG=0.2 A` (`NEG_FRAC=.02` at `I_LIMIT=10 A`) than to the
rescaled `125 A`-based values R04E22-R04E25 tested. This raises the
possibility that R04E3's original small-current parameters were never
"wrong scale" -- it may instead have been R04E17's own zero-start-ramp-
derived bootstrap state (`IL1=75.97 A`) that was never representative of
where phase 1's current actually sits near the true periodic orbit.

**This experiment tests the cheapest available version of that question**:
re-run R04E21 EXACTLY as committed (same `I_LIMIT=10 A`, `NEG_FRAC=.02`,
`CFLY=3 uF`, `TSTOP=20 us`, same 5-state `.machine`, phases 2-4 still
hardcoded at R04E3's own zero-energy configuration), changing ONLY the
two bootstrapped initial-condition values (`VC1_IC`, `IL1_IC`) from
R04E17's zero-start-ramp result to the periodic orbit's own reported
values.

## 2. What changed relative to R04E21, exactly

- **`VC1_IC` changed from `35.85894624845418 V` (R04E17's own zero-start
  bootstrap) to `35.8448 V`** (the periodic orbit's own reported average
  flying-capacitor-1 voltage, `results/ZERO_START_AFFINE_PERIOD_FIXED_
  POINT.md`, "Average flying-capacitor voltages" row, quoted to its own
  published precision).
- **`IL1_IC` changed from `75.96527862548828 A` (R04E17's own zero-start
  bootstrap) to `0.111 A`** (the periodic orbit's own reported
  phase-1 current MINIMUM, same source document, "Phase-current minima"
  row, quoted to its own published precision). This is used as the best
  available proxy for phase 1's own natural pre-commutation current,
  since the source document reports only period-averaged/extremal
  statistics, not the full instantaneous 20-variable state vector at a
  specific sampled instant -- this approximation is a stated, explicit
  limitation of this experiment (Section 7), not a hidden assumption.
- Nothing else changes: `I_LIMIT=10 A`, `NEG_FRAC=.02` (`I_NEG=0.2 A`),
  `TSTOP=20 us`, `CFLY=3 uF`, the 5-state `.machine` block's own rule
  structure, phases 2-4's own hardcoded R04E3 configuration -- all
  copied byte-for-byte from R04E21's own already-committed netlist.

## 3. A pre-registered structural expectation (stated before running, per
   this project's own Ground Rule discipline)

R04E3's own state `ENERGY` (state 0) exits on the unconditional rule
`I(XMOD:L1)>=I_LIMIT`, regardless of the starting current -- so whatever
`IL1_IC` is set to, the machine will simply charge phase 1's current up
to `I_LIMIT=10 A` before state 1 begins. **This means the specific value
of `IL1_IC` (`0.111 A` here vs `75.97 A` in R04E21) is very likely to be
almost entirely "erased" by the time the interesting states (2/3/4) are
reached**, and the ONLY initial condition with a plausible chance of
mattering is `VC1_IC` -- which differs from R04E21's own value by only
about `0.04%` (`35.8448 V` vs `35.85894... V`). **The most likely outcome
of this experiment is therefore that it reproduces R04E21's own
documented permanent stall at state 4, with results numerically close to
identical to R04E21's own.** This is stated explicitly in advance so
that an unchanged result is not mistaken for a failed experiment -- it
would instead CONFIRM this structural insensitivity finding, which is
itself useful (it tells us that a small-scope IC swap of this kind
cannot resolve the cross-track discrepancy, motivating the larger,
full-four-phase alternative the user did not choose this round).

## 4. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| `VC1_IC=35.8448 V` | `results/ZERO_START_AFFINE_PERIOD_FIXED_POINT.md`, "One-period electrical metrics" table, "Average flying-capacitor voltages" row, first value, quoted verbatim | `CROSS_PAPER_EXTENSION`-adjacent, from the parallel math-model effort's own already-published, self-consistency-checked result (map residual `2.6e-11`) -- not independently re-derived by this session |
| `IL1_IC=0.111 A` | Same source document, "Phase-current minima" row, first value, quoted verbatim | Same category; additionally `SENSITIVITY_ONLY` in the specific sense that this is an approximation (period minimum used as a proxy for the pre-commutation instantaneous value), explicitly flagged, not an exact checkpoint match |
| Everything else | See R04E21 `BOUNDARY.md` for original provenance -- unchanged | unchanged |

No new paper-sourced or external-device data is introduced. This is the
first experiment in this project to use a value sourced from the
parallel math-model effort's own periodic-orbit result as a SPICE
initial condition.

## 5. What question this experiment answers

Does swapping only the initial condition (leaving R04E3's own original,
small-current-scale parameters `I_LIMIT=10 A`/`I_NEG=0.2 A` untouched)
for values closer to the true periodic orbit change the outcome at all?
If the pre-registered structural expectation (Section 3) is correct, this
experiment's main value is confirming that expectation explicitly with
real SPICE data, not resolving the cross-track discrepancy itself.

## 6. Success/failure conditions

- **Outcome matches R04E21 closely (permanent stall at state 4, `T_HIGH_
  SIDE_ZVS` never fires, all measured values within a fraction of a
  percent of R04E21's own committed numbers)**: confirms the pre-
  registered structural-insensitivity expectation. Report plainly as
  expected, not as a null/failed result -- and explicitly recommend the
  larger, full-four-phase, real-instantaneous-state experiment (the
  option not chosen this round) as the next step if the cross-track
  discrepancy is still worth pursuing.
- **Outcome differs materially from R04E21** (different final state, or
  ZVS reached): would be a genuine surprise given the erasure argument in
  Section 3 -- report immediately and prominently, and investigate why
  the erasure argument was wrong before drawing further conclusions.
- Phase 1's own current must stay within `+/-250 A` throughout (R04E21's
  own cell already confirmed a small excursion under this same
  `I_LIMIT=10 A` regime; not expected to differ materially).

## 7. What this experiment cannot prove

- It does NOT use the periodic orbit's own exact instantaneous state at
  the commutation instant -- only its period-averaged/extremal summary
  statistics, since the parallel math-model effort's own published
  `results/*.md` files do not report a full 20-variable checkpoint at a
  specific sampled instant. If this approximation matters, only the
  larger alternative experiment (full four-phase, real checkpoint data)
  can resolve it.
- It does not test all four phases, still hardcoding phases 2-4 at
  R04E3's own zero-energy configuration -- same standing limitation as
  R04E21-R04E25.
- It does not modify, touch, or depend on `src/scb_ivr/` or `results/`
  beyond reading and quoting the one already-published document cited
  above.
- Same list as R04E21-R04E25 otherwise: does not test P24 periodicity,
  does not test four-phase handoff, does not validate R04E3 as "the" P24
  controller, no P24 reproduction claim of any kind.
