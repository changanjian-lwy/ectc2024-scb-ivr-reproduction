# R04E12 - phase-1 precharge admission gate (BOUNDARY)

## 1. Parent

**R04E10** (`experiments/track_B_zero_start_extension/
R04E10_timeout_gated_multi_rotation_bootstrap/`), the currently
best-validated, multi-rotation-capable construct (6/9 cells complete
4-17 rotations, `Vout` rises monotonically). Its own `RESULTS.md` Section
10 found this mechanism converges MUCH more slowly per-cycle than
R04E7/E8's switch-only ladder mechanism because each phase's own
current-limit/timeout ceiling caps how much charge transfers per visit.
Its best cell (`I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`) still leaves `VC2`
(the axis phase 2 feeds, whose high side connects between `C1` and `C2`,
never directly to `Vin`) as the weakest-progressing quantity, and 3 of its
6 multi-rotation cells show `VC2` moving in the WRONG direction entirely.

This traces to R04E9's own root-cause finding (`RESULTS.md` Section 11,
still valid, not superseded): phase 2 only ever receives charge relayed
FROM `C1`, and `C1` itself starts each rotation with only whatever phase 1
managed to deposit in ONE current-limited pass (R04E9: `~0.93 ns` first
pulse). R04E9 Section 11 proposed three candidate fixes; this experiment
implements option (c) verbatim, per explicit user direction (2026-09-16):
**"allowing phase 1 to repeat (re-enter `CHARGE1`) several times, building
up `C1`'s charge over multiple pulses, before the machine is allowed to
advance to phase 2 -- a genuinely different admission structure from the
strict round-robin rotation tested here."**

Also relevant: **R04E11** (`R04E11_charge_free_reversal_root_cause/`)
directly diagnosed R04E10's own retry/chatter dynamic and its coincident
`ICS1-3` current-reporting artifact as a limitation of LTspice's
`.machine`/`.rule` event resolution during stiff, sub-picosecond-timestep
solver episodes -- NOT a defect in this project's own reset-gate/switch
logic (two candidate internal-logic causes were directly tested and
refuted). Because this experiment reuses R04E10's `CHARGE_k`/`FREE_k`
current-limit-OR-timeout construct unchanged, **the same class of
retry/chatter episode and `ICS1-3` artifact may recur here too** -- this is
an already-understood, already-diagnosed phenomenon per R04E11, not a new
mystery, and must be flagged (not silently trusted) using the same
`>1000 A` `ICS1-3` filter R04E10 used, with `IL1-4` treated as the
trustworthy peak-current indicator, exactly as R04E10/R04E11 established.

## 2. What changed relative to the parent, exactly

**Single conceptual change**: a new precharge admission stage is inserted
before the machine's normal round-robin rotation begins. A counter tracks
how many times `FREE1` has completed. While the counter is below a fixed
threshold `N_PRECHARGE`, `FREE1`'s exit routes back to `CHARGE1` (repeat
phase 1 alone) instead of advancing to `CHARGE2`. Once the counter reaches
`N_PRECHARGE`, the machine joins R04E10's own already-validated normal
round-robin sequence (`CHARGE1->FREE1->CHARGE2->FREE2->CHARGE3->FREE3->
CHARGE4->FREE4->CHARGE1->...`) unchanged, and never re-enters the
precharge stage again (the gate is a one-time admission condition, not a
per-rotation repeat). `N_PRECHARGE=1` is definitionally identical to
R04E10's own unmodified behavior (phase 1 never repeats, immediate
admission to `CHARGE2`) and is included in the swept grid as the exact
apples-to-apples baseline.

No other mechanism, node, topology, or parameter change. `CHARGE_k`'s
current-limit-OR-timeout exit rule, `FREE_k`'s event-OR-timeout exit rule,
and the full four-phase `SCB4P_P24_*` power-stage connectivity are copied
unchanged from R04E10 (subcircuit renamed only to avoid a same-name
netlist collision, electrically identical).

## 3. What did not change

- Full four-phase P24 power-stage connectivity -- copied unchanged from
  R04E10/R04E9.
- `CHARGE_k`'s current-limit exit condition and its own `T_CHARGE_MAX`
  timeout fallback -- copied unchanged from R04E10 (the R04E10-validated
  construct, not R04E9's un-timed-out original).
- `FREE_k`'s exit condition and elapsed-freewheel-time timer -- copied
  unchanged from R04E9/R04E10.
- `LPHASE=1.4666667 nH`, `CFLY=3 uF` (R04E8's corrected value), `COUT=
  4.672 mF` (still-flagged candidate, not corrected here), GS61008T
  device data, true-zero-energy initial conditions (`ic=0`, `UIC`),
  `TMAX=50 ps`.
- The handoff-condition monitor definition (`Vout` within 5% of `1 V` AND
  `VC1-3` within 2% of `36/24/12 V`) -- identical to R04E9/R04E10's.
- The inactive-phase all-off switch convention (R04E9 Section 2 / R04E10
  Section 4) -- unchanged; this remains a bootstrap-only transient study,
  not periodic steady-state, so the P24-vs-P25 inactive-low-side question
  still does not arise here.

## 4. Fixed parameters and the swept axis

Fixed at R04E10's own best-performing cell's values (`RESULTS.md` Section
8: `I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns` reached the closest fraction of
every target of any R04E10 cell), for direct before/after comparability
against a single known R04E10 reference point rather than re-sweeping
everything at once:

- `I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`, `T_FREEWHEEL_MAX=50 ns`.
- `TSTOP=20 us`, `TMAX=50 ps` (unchanged from R04E10; the added precharge
  passes add at most `~20*100 ns=2 us` before normal rotation begins,
  leaving ample remaining window).

Swept: `N_PRECHARGE` in `{1, 3, 5, 10, 20}`, 5 cells. `N_PRECHARGE=1` is
the exact R04E10-equivalent baseline (Section 2). The other four values
are a first, order-of-magnitude exploration of whether a modest precharge
stage measurably helps -- not a claim that any one of them is optimal or
paper-derived; this axis is `SENSITIVITY_ONLY` like every other swept
control-timing value in this project's Track-B lineage.

## 5. Pilot verification required before committing to the full grid

Per this project's own established discipline (R04E7/R04E8/R04E9/R04E10
each piloted their new mechanism in isolation first): before running the
5-cell grid, verify in an isolated diagnostic that the new counter/routing
construct actually does what Section 2 describes -- `FREE1` returns to
`CHARGE1` exactly `N_PRECHARGE-1` times before the `N_PRECHARGE`-th
`FREE1` completion routes to `CHARGE2`, confirmed by direct inspection of
`V(state_mon)`'s dwell sequence for at least the `N_PRECHARGE=3` and `=10`
cells, not merely assumed from the construct's intended logic. Report this
pilot check explicitly in `RESULTS.md`, the same standard R04E10 Section 5
set for its own new timer branch.

## 6. Provenance of every changed/new value

| Value | Source | Category |
|---|---|---|
| Precharge admission-gate construct (counter + routing change) | This experiment's single new mechanism, implementing R04E9 `RESULTS.md` Section 11 option (c) verbatim, per explicit user direction 2026-09-16 | `NUMERICAL_IDEALIZATION`/engineering construct -- no physical counterpart, a controller/sequencing choice |
| `N_PRECHARGE` swept values `{1, 3, 5, 10, 20}` | New for this experiment; `1` is the R04E10-equivalent baseline, `{3,5,10,20}` are an order-of-magnitude first exploration | `SENSITIVITY_ONLY` |
| `I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`, `T_FREEWHEEL_MAX=50 ns` | R04E10's own best-performing cell, fixed here rather than re-swept | inherited, `SENSITIVITY_ONLY` (R04E10 provenance) |
| Every value carried over from R04E9/R04E10 (`Vin`, `nP`, `nM`, topology, `LPHASE`, `CFLY`, `COUT`, GS61008T data, handoff tolerance bands, `CHARGE_k`/`FREE_k` exit rules) | See R04E10 `BOUNDARY.md` Section 6 | unchanged |

**No new paper-sourced, cross-paper, or external-device data is
introduced.** Nothing here bears on any `P24_EXPLICIT` or
`P25_SUPPLEMENT` boundary.

## 7. What question this experiment is meant to answer

Does front-loading charge onto `C1` alone (via a repeated-admission
precharge stage) BEFORE phase 2 ever draws on it, measurably improve
`VC2`'s trajectory (stop it regressing, or reach a larger fraction of its
`24 V` target) compared to R04E10's own `N_PRECHARGE=1` best cell -- and
does it improve the other three state variables (`Vout`, `VC1`, `VC3`) as
well, or trade them off? Is there a point of diminishing (or negative)
returns as `N_PRECHARGE` increases (e.g. because the precharge stage
itself eats into the `20 us` window without leaving enough time for
enough normal rotations after it)?

## 8. Success condition

`LOCAL_PASS`: a cell reaches the handoff condition within `TSTOP`
(unlikely given R04E10's own scale of shortfall, but reported honestly if
it happens). `CONTROLLER_GUARD_PASS` with genuine improvement: rotations
complete, currents stay within `+/-250 A`, and at least one of
`{5,10,20}` shows a measurably better trajectory (larger fraction of
target reached, or `VC2` moving in the correct direction where R04E10's
`N_PRECHARGE=1`-equivalent cell did not) than the `N_PRECHARGE=1` cell in
this same grid. `CONTROLLER_GUARD_PASS` with no improvement or a
trade-off: reported plainly as a negative/mixed result, per Ground Rule 7
-- this experiment must not force a favorable reading of an ambiguous
result.

## 9. Failure conditions

- `PHYSICAL_BOUNDARY_FAIL`: any phase current exceeds `+/-250 A`.
- No measurable improvement in any swept `N_PRECHARGE` value over the
  `N_PRECHARGE=1` baseline -- a legitimate, informative negative result,
  not a reason to keep sweeping further values in search of one that
  works.
- The precharge stage itself fails to terminate cleanly (Section 5's pilot
  check fails) -- reported as its own construct-level finding, same
  standard as R04E10/R04E11's own honestly-reported construct fragilities.
- Solver non-convergence, or a recurrence of R04E11's diagnosed
  retry/chatter dynamic severe enough to prevent any rotation from
  completing in a cell -- reported plainly using the same `IL1-4`-as-
  trustworthy-indicator / `ICS1-3`-flagged-as-suspect convention R04E10/
  R04E11 established, not silently worked around.

## 10. What this experiment cannot prove

- It does not, by itself, close the full handoff gap even if it measurably
  helps `VC2` -- R04E10 Section 10's finding (this whole inductor-mediated
  family converges far more slowly per-cycle than R04E7/E8's switch-only
  mechanism) is a separate, structural limitation this experiment does not
  address.
- It does not validate `Cout=4.672 mF`, still an unconfirmed inherited
  value.
- It does not build or exercise the handoff into the existing strict
  steady-state controller -- out of scope, same as R04E9/R04E10/R04E11.
- A result here is specific to this exact fixed-parameter combination
  (`I_LIMIT=60 A`, `T_CHARGE_MAX=50 ns`, `T_FREEWHEEL_MAX=50 ns`,
  `CFLY=3 uF`, `COUT=4.672 mF`); it must not be read as a general
  statement about precharge-admission-gating independent of these values.
- It does not evaluate R04E9 Section 11's options (a) (direct topology
  change) or (b) (passive precharge circuit) -- those remain separate,
  unstarted candidate directions.
