# R04E13 - phase-2 precharge admission gate, stacked on phase-1's (BOUNDARY)

## 1. Parent

**R04E12** (`experiments/track_B_zero_start_extension/
R04E12_phase1_precharge_admission_gate/`), which implemented R04E9's
option (c) for phase 1 ONLY: a one-time admission gate that repeats
`CHARGE1`/`FREE1` `N_PRECHARGE` times, building up `C1`'s charge, before
the machine is ever admitted into `CHARGE2` and the normal round-robin
rotation. Result: `Vout` improved monotonically with `N_PRECHARGE` (`+40%`
at `N_PRECHARGE=20`), but `VC2` improved non-monotonically (`+16%` at
`N_PRECHARGE=3`, `-18%` at `N_PRECHARGE=5`, `+38%` at `N_PRECHARGE=20`,
with a new `VC3`-goes-negative trade-off at that same best-`VC2` cell).

R04E9's own root-cause finding (`RESULTS.md` Section 11) is that EVERY
phase beyond the first only ever receives charge relayed from the
capacitor before it -- phase 2's high side connects between `C1` and `C2`,
never to `Vin` directly; the same is true structurally of phase 3 (between
`C2`/`C3`) and phase 4 (`C3` to ground). R04E12 tested whether
front-loading `C1` alone helps; this experiment tests the natural next
generalization: **does ALSO front-loading `C2` (via the identical gate
mechanism, applied to phase 2, stacked after phase 1's own already-tested
gate) help further, independent of or in combination with phase 1's own
gate?**

## 2. What changed relative to the parent, exactly

**Single conceptual change, applied twice using R04E12's own already-
validated construct pattern**: after phase 1's precharge stage completes
(`N1_PRECHARGE` repeats of `CHARGE1`/`FREE1`, IDENTICAL mechanism and
implementation style to R04E12), a SECOND, analogous precharge stage is
inserted for phase 2: `FREE2`'s exit routes back to `CHARGE2`
(`N2_PRECHARGE-1` extra times, repeating phase 2 alone, building up `C2`'s
charge) instead of advancing to `CHARGE3`, using the exact same compile-
time-unrolled state-pair-chain pattern R04E12 built and pilot-verified for
phase 1 (`PCHG2_k`/`PFREE2_k`, mirroring `CHARGE2`/`FREE2` exactly, same
current-limit-OR-timeout / zero-crossing-OR-timeout rules, same shared
`timer`/`timer_chg` nodes generalized to cover the new states). Once
`N2_PRECHARGE` is reached, the machine joins the normal round-robin
sequence at `CHARGE3` permanently; the phase-2 precharge chain never
re-triggers, exactly mirroring phase 1's own one-time-gate behavior.

`N1_PRECHARGE=1, N2_PRECHARGE=1` must be definitionally identical to
R04E10's own original (ungated) behavior. `N1_PRECHARGE=X, N2_PRECHARGE=1`
must be definitionally identical to R04E12's own `N_PRECHARGE=X` cell.
Both identities must be confirmed directly (byte-identical `.machine`
text where applicable, matching `.meas` output), the same sanity-check
discipline R04E12 applied to R04E10.

No other mechanism, node, topology, or parameter change. Phases 3 and 4
are NOT gated in this experiment -- extending the gate further is a
separate, later generalization if this one shows benefit.

## 3. What did not change

- Full four-phase P24 power-stage connectivity, `CHARGE_k`/`FREE_k`
  current-limit-OR-timeout / zero-crossing-OR-timeout exit rules -- copied
  unchanged from R04E9/R04E10/R04E12.
- `LPHASE=1.4666667 nH`, `CFLY=3 uF`, `COUT=4.672 mF`, GS61008T device
  data, true-zero-energy initial conditions (`ic=0`, `UIC`), `TMAX=50 ps`.
- `I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`, `T_FREEWHEEL_MAX=50 ns` -- R04E10's
  own best-performing cell, fixed here exactly as R04E12 fixed them.
- The handoff-condition monitor definition and the inactive-phase all-off
  switch convention -- unchanged; this remains a bootstrap-only transient
  study, not periodic steady-state.
- Phase 1's own gate mechanism and its pilot-verified correctness
  (R04E12 Section 3) -- reused unchanged, not re-verified from scratch,
  only re-confirmed at the specific `N1_PRECHARGE` value(s) used here.

## 4. Fixed parameters and the swept axis

`N1_PRECHARGE` fixed at **`3`** (not R04E12's numerically-best-for-`VC2`
`20`, deliberately): R04E12 Section 7 found `N_PRECHARGE=3` gives a clean,
trade-off-free `VC2` improvement (`+15.7%`, no negative `VC3`), whereas
`N_PRECHARGE=20` achieves a larger `VC2` gain (`+37.9%`) but at the cost of
the only negative `VC3_final` in that whole grid. Anchoring on the
clean, no-trade-off value isolates phase 2's own marginal effect without
inheriting phase 1's own worst side effect into this grid's baseline.

Swept: `N2_PRECHARGE` in `{1, 3, 5, 10}`, 4 cells, `N1_PRECHARGE=3` fixed
for all. `N2_PRECHARGE=1` is the exact R04E12-`N_PRECHARGE=3`-equivalent
baseline (Section 2). `I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`,
`T_FREEWHEEL_MAX=50 ns`, `TSTOP=20 us`, `TMAX=50 ps` fixed, unchanged from
R04E12.

This is a smaller, more targeted grid than R04E12's own 5-cell sweep
(4 cells, not a full `N1 x N2` cross product) -- deliberately, to keep
this a single-conceptual-change experiment (marginal effect of gating
phase 2, holding phase 1's own gate at one already-characterized value)
rather than a new 2-D parameter search; a full cross-sweep is a candidate
follow-up only if this one shows a clear, well-behaved effect worth
mapping further.

## 5. Pilot verification required before committing to the full grid

Same standard as R04E12 Section 5/R04E10 Section 5: before trusting the
4-cell grid, confirm by direct raw-trace inspection (reusing R04E12's own
`scripts/verify_precharge_gate.py`, generalized to check phase 2's own
precharge chain the same way it already checks phase 1's) that, for at
least `N2_PRECHARGE=3` and `N2_PRECHARGE=10`: (1) the machine visits every
phase-2 precharge pair exactly once, in strictly increasing order,
AFTER phase 1's own precharge chain completes and the real `CHARGE2` is
first reached, and BEFORE the real `CHARGE3`; (2) the phase-2 precharge
chain never re-triggers after the machine's first arrival at `CHARGE3`;
(3) the exact count of phase-2-precharge-role dwells equals
`2*(N2_PRECHARGE-1)`. Also confirm the `N1_PRECHARGE=3, N2_PRECHARGE=1`
baseline cell's `.meas` output matches R04E12's own committed
`N_PRECHARGE=3` row to full printed precision, mirroring R04E12 Section 2.

## 6. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| Phase-2 precharge admission-gate construct (second compile-time-unrolled chain, stacked after phase 1's own) | Direct generalization of R04E12's own validated phase-1 construct to phase 2, motivated by R04E9's structural finding that every phase beyond the first faces the same relay-only charging limitation | `NUMERICAL_IDEALIZATION`/engineering construct -- no physical counterpart, a controller/sequencing choice |
| `N1_PRECHARGE=3` (fixed) | R04E12's own clean, trade-off-free best value (Section 4) | inherited, `SENSITIVITY_ONLY` (R04E12 provenance) |
| `N2_PRECHARGE` swept values `{1, 3, 5, 10}` | New for this experiment; `1` is the R04E12-`N=3`-equivalent baseline | `SENSITIVITY_ONLY` |
| `I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`, `T_FREEWHEEL_MAX=50 ns` | R04E10's own best-performing cell, fixed here | inherited, `SENSITIVITY_ONLY` |
| Every value carried over from R04E9/R04E10/R04E12 | See R04E12 `BOUNDARY.md` Section 6 | unchanged |

**No new paper-sourced, cross-paper, or external-device data is
introduced.** Nothing here bears on any `P24_EXPLICIT` or
`P25_SUPPLEMENT` boundary.

## 7. What question this experiment is meant to answer

Does ALSO front-loading `C2` (on top of phase 1's own already-gated
precharge) further improve `VC2`/`VC3`/`Vout`, or does it just shift the
same relay-only bottleneck one stage further down the chain (onto `VC3`,
fed by phase 3, which is NOT gated in this experiment)? Is the marginal
benefit of gating phase 2 comparable in size to gating phase 1 was
(R04E12), smaller (diminishing returns as the gate is pushed further from
the true-zero-energy start), or does it introduce its own new trade-off
the way `N_PRECHARGE=20` did for `VC3` in R04E12?

## 8. Success condition

`LOCAL_PASS`: a cell reaches the handoff condition (very unlikely given
R04E12's own scale of shortfall, but reported honestly if it happens).
`CONTROLLER_GUARD_PASS` with genuine improvement: rotations complete,
currents stay within `+/-250 A`, and at least one of `{3,5,10}` shows a
measurably better `VC2` AND/OR `Vout` trajectory than the
`N2_PRECHARGE=1` baseline in this same grid, without a proportionally
worse trade-off elsewhere. Reported plainly as mixed/non-monotonic if that
is what the data shows, per Ground Rule 7 -- exactly as R04E12 itself was
reported.

## 9. Failure conditions

- `PHYSICAL_BOUNDARY_FAIL`: any phase current exceeds `+/-250 A`.
- No measurable improvement over the `N2_PRECHARGE=1` baseline in any
  swept value -- a legitimate, informative negative result.
- The phase-2 precharge stage fails to terminate cleanly, or the pilot
  check (Section 5) fails -- reported as its own construct-level finding.
- A recurrence of the R04E11-diagnosed retry/chatter dynamic severe enough
  to prevent rotation completion in a cell -- reported using the same
  `IL1-4`-trustworthy / `ICS1-3`-flagged convention R04E10/R04E11/R04E12
  established, not silently worked around.

## 10. What this experiment cannot prove

- It does not, by itself, close the handoff gap even if it measurably
  helps -- R04E10 Section 10's structural finding (this whole family
  converges far more slowly per-cycle than R04E7/E8's switch-only
  mechanism) remains unaddressed.
- It does not validate `Cout=4.672 mF`, still an unconfirmed inherited
  value.
- It does not build or exercise the handoff into the existing strict
  steady-state controller -- out of scope, same as R04E9-R04E12.
- A result here is specific to `N1_PRECHARGE=3` fixed; it does not explore
  the full `N1 x N2` interaction space, and must not be read as a general
  statement about stacking precharge gates independent of the specific
  `N1` value chosen.
- It does not gate phases 3 or 4 -- if gating phase 2 helps, whether the
  same benefit extends further down the chain (and whether it eventually
  runs out of usable window within `TSTOP=20 us`) remains untested here.
- It does not evaluate R04E9 Section 11's options (a) (direct topology
  change) or (b) (passive precharge circuit) -- those remain separate,
  unstarted candidate directions.
