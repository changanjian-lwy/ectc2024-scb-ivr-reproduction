# A48 dead-time feasibility sweep boundary

Track: A, local P24 `t2->t3` mechanism experiment (same family as A41/A42/
A45). This is not a periodic-orbit, four-phase or startup experiment.

## Parent

Electrical parent:
`paper_locked/02_ectc2024_main/spice/R04D3A_P24_interval3_same_phase_ZVS.cir`,
via the same A42 zero-snubber local-state chain
(`R04D0`->`R04D1A`/`R04D1B2`->`R04D2A`->`R04D3A`).

## Fixed quantities (identical to A42; not changed here)

- P24 topology, local state sequence and R04D2A-chained initial state
  (`VC1_T2`, `VX1_T2`, `VA1_T2`).
- `Vin=48 V`, `Vo=1 V`, `nP=4`, `nM=1`, `Ipk=125 A`.
- Locked Eq.-(4) `L=1.4667 nH`.
- P25/external GS61008T charge-equivalent commutation capacitance
  `CH=385 pF`, `CL=770 pF` (no snubber, no nonlinear `Coss(V)`).
- High/low switch resistance `7/3.5 mOhm` (`GS61008T_RDS_TYP_25C`, `NHS`/`NLS`
  scaling).
- The QL1 release rule and event: `I(L1)<-INEG` with `INEG=NEG_FRAC*125A`,
  exactly as in A42.
- 50 ns observation window, `reltol=1e-7`/`abstol=1e-10` (unchanged from A42).
  `chgtol` is relaxed from A42's `1e-16` to LTspice's own default `1e-14`
  (100x looser, still tight) -- see "Numerical note" below; this is a solver
  setting, not a physical/electrical parameter, and is not the changed
  variable.
- The EPC2067/A45 device-swapped branch is explicitly out of scope for this
  experiment; A48 only uses the GS61008T assumption. (A second,
  clearly-separately-labelled EPC2067 branch was not attempted -- see
  "What this experiment does not cover" below.)

## Only changed variable

QH1's turn-on rule. The parent/A42 use an **ideal event detector**: QH1
turns on the instant `V(vin,a1)<0` (`.rule P24_COMMUTATE_TO_HIGH
P24_QH1_ZVS_ON V(vin,a1)<0`). A48 replaces this with a **fixed-delay
turn-on**: QH1 turns on at a fixed time `T_DEAD` after the QL1 release event
(`I(L1)<-INEG`), regardless of `V(vin,a1)`'s value at that instant. This is
implemented as `B_GH1_FIXED_DELAY gh1 0 V=delay(V(release_flag),T_DEAD)`,
where `release_flag` is the state-machine output that steps at the release
event; the third machine state (`P24_QH1_ZVS_ON`) and its `V(vin,a1)<0` rule
are removed. `delay()` is the same LTspice behavioral-delay primitive already
used in this project's A28/A29 and A37 controllers (fixed `TON`/`T_SENSE`
delays), reused here for a fixed dead time instead.

`T_DEAD` itself is `SENSITIVITY_ONLY` (per
`EXPERIMENT_PROTOCOL_AND_ARCHIVE_RULES.md` category rules): it is swept over
a physically reasonable real-GaN-driver span, not a measured value. The real
dead time/driver propagation delay remains `UNKNOWN_BLOCKING`, requested from
Mihai in Report Section 8 and still unanswered.

## Supporting addition (not the changed variable)

An ideal GaN off-state reverse-conduction diode (`DH1_REVERSE a1 vin
DGAN_IDEAL`, the same `DGAN_IDEAL` model A27 already introduces: `Vf=0`,
`Ron=1 mOhm`, P25-labelled) is placed across QH1. Without it, once `T_DEAD`
is long enough for the natural `Vds=0` crossing to occur before the forced
turn-on, nothing in the model would stop `V(vin,a1)` from being driven
through and past zero into an undefined negative region while QH1 is still
off. The diode only becomes forward-biased once `V(vin,a1)<0`, i.e. only
after the natural crossing has already happened; it does not participate in,
and does not affect, the primary pre-crossing residual-`Vds` measurement.

## Numerical note: chgtol relaxation

A42/R04D3A's `chgtol=1e-16` was tuned for a soft (near-zero-differential)
ZVS closure. A48 deliberately produces genuinely hard-switching cases
(forcing an ~1.75 mOhm switch closed across several volts), and with
`chgtol=1e-16` these hang indefinitely (verified: killed after >20 minutes
of CPU time with no result) -- the charge-transfer-per-step this tolerance
demands during a multi-thousand-amp instantaneous spike never converges in
practice. `chgtol` was relaxed to LTspice's own default, `1e-14`. This was
verified NOT to change the physics being measured: A42's original 1%
netlist, rerun standalone with only `chgtol` changed from `1e-16` to
`1e-14` (no other edit), reproduces A42's published minimum post-release
`Vds` of 9.2566 V to 4 significant figures (9.2567 V / 9.2570 V across two
isolation tests). The same isolated test with A48's reverse-conduction
diode added but the controller left as A42's original ideal detector also
reproduces 9.2567 V. The relaxation is therefore attributable entirely to
resolving the new hard-switching branch, not to any loss of accuracy in the
shared pre-event LC dynamics.

## Fixed release rows (reused unchanged from A42)

Three `NEG_FRAC` rows, each simulated at every swept `T_DEAD`:

- `1%` (`P24_EXPLICIT`) -- A42 found no natural ZVS in-window (min `Vds`
  9.257 V).
- `2%` (`P24_EXPLICIT`) -- A42 found no natural ZVS in-window (min `Vds`
  7.996 V).
- `7.77%` (A42's own already-bracketed local natural-ZVS threshold) --
  natural ZVS occurs 2.155 ns after release per A42's fine refinement.

No new `NEG_FRAC` values are introduced; the release-current axis is fully
inherited from A42, not re-derived here.

## Question this experiment answers

For each (`NEG_FRAC`, `T_DEAD`) pair: does the fixed-delay forced turn-on
happen before or after the natural `Vds=0` crossing (when one exists), and
what is `V(vin,a1)` (the residual switching voltage) at the instant of
forced turn-on? This produces a feasibility map -- a bracket of `T_DEAD`
values, for the one row where natural ZVS exists at all, above/below which
the forced turn-on catches zero volts vs. a nonzero residual -- that can
later be compared against Mihai's real dead-time number once given.

## Success / extraction criteria

- For every case: extract the release time/current (`P24_T_QL1_OFF`), the
  natural-ZVS time/current if one occurs in-window (`P24_T3_HIGH_VDS_ZERO`),
  the forced-on time (`P24_T_FORCED_ON`, defined as `V(gh1)` crossing its
  2.5 V threshold), and `V(vin,a1)`/`I(L1)` at that forced-on instant
  (`P24_VDS_AT_FORCED_ON`, `P24_IL1_AT_FORCED_ON`).
- A row counts as reaching effective ZVS at forced turn-on only if
  `P24_VDS_AT_FORCED_ON` is at or within numerical noise of 0 V.
- The coarse grid (0.5, 1, 2, 3, 5, 7, 10, 15, 20 ns) is intended to bracket
  any pass/fail transition for the 7.77% row only, since A42 already showed
  1%/2% never reach a natural crossing in-window (so no transition can exist
  for them at any `T_DEAD` -- dead time cannot manufacture negative-current
  margin that was never there). Refinement grids narrow only around a
  transition actually observed in the coarse grid for the 7.77% row.

## Prohibited claims

- This cannot establish the real dead time or driver propagation delay --
  `T_DEAD` remains `SENSITIVITY_ONLY`; the real value is still
  `UNKNOWN_BLOCKING` pending Mihai.
- Cannot claim four-phase closure, periodic state, or startup: this is a
  single local `t2->t3` interval on phase 1 only.
- Cannot claim that 1% or 2% negative current becomes ZVS-viable at any
  `T_DEAD`. A longer dead time only changes *when* QH1 is forced on; it
  cannot create commutation energy that the release current never supplied.
  If A42 found no natural zero-crossing for a row within the observation
  window, no `T_DEAD` value can produce one either -- the fixed-delay
  mechanism can only report the residual voltage at whatever positive `Vds`
  the resonant tank already occupies at that time.
- A `T_DEAD` value that lands after the 7.77% row's natural crossing is
  **not automatically equivalent to A42's natural-ZVS result**: the
  underlying LC tank keeps resonating once QH1 is off and the crossing has
  passed, so `V(vin,a1)` does not necessarily stay pinned at 0 -- it can
  ring back positive. Whether "any dead time above the natural commutation
  duration matches A42" must be checked explicitly per case, not assumed;
  see RESULTS.md for what was actually found.
- This does not validate or invalidate the GS61008T device-capacitance
  assumption itself; that question belongs to A41/A42/A45/A46, not here.

## What this experiment does not cover

A second, separately-labelled EPC2067 (A45 device assumption) branch was in
scope as an optional extension but was not run: the primary GS61008T sweep
above already surfaced a result (the post-crossing ring-back, see
RESULTS.md) that needed full coarse+refinement characterization to report
honestly, and that took priority within the available time. If pursued
later, it must be a clearly separate branch, not conflated with the rows
above.
