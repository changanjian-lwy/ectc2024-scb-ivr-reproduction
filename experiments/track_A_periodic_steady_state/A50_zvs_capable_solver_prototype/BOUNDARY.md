# A50 - a ZVS-capable copy of the parallel math model's fast periodic solver (BOUNDARY)

Track: A (periodic steady-state reproduction). This is a Python-solver
prototyping experiment, not a SPICE experiment -- its "netlist" is a copy
of another track's own source code, extended with new physics.

## 0. Scope statement and the explicit copy-not-modify constraint

**Per explicit user instruction 2026-09-18** ("你要搞个复制文档过去 就是不要
污染原来的代码" -- make a copy elsewhere, do not pollute the original code):
this experiment works ENTIRELY on a byte-for-byte COPY of the relevant
`src/scb_ivr/` files, placed under this experiment's own `solver_copy/`
subdirectory. **`src/scb_ivr/` itself is never opened for writing by this
experiment, under any outcome.** If this prototype fails validation
(Section 6), the only consequence is an honest negative `RESULTS.md` in
this directory -- the original codebase is completely unaffected, exactly
as if this experiment had never been attempted. This is in addition to,
not instead of, this project's own standing git-worktree-isolation
discipline (every experiment already runs on its own branch, merged only
after independent verification) -- the user's instruction here is a
stronger, file-level version of that same principle, specific to not
even having in-place edits appear in a branch that touches the other
track's own maintained files.

This does not claim a P24/P25 reproduction. It is an engineering
prototype: does adding real switch capacitance and genuine dead time to
the parallel math model's own fast (seconds, not SPICE's 20-100+ minute)
periodic solver let it answer ZVS feasibility questions for arbitrary
device parameters, the way `commutation_feasibility.py`'s closed-form
formulas already do for the SINGLE-PHASE local case -- but for the full,
coupled four-phase joint periodic state, which no closed-form formula can
capture (per the analysis already given to the user this session).

## 1. Why this exists

Per this session's own discussion with the user: Track A's four-phase
periodic-orbit search (A24-A49) has been SPICE-only, each candidate
costing tens of minutes and requiring hand-guessed device parameters.
`src/scb_ivr/periodic_affine_solver.py` already solves a RELATED problem
(one-period affine fixed point) in seconds -- but its underlying
`assemble_descriptor` (`zero_start_descriptor.py`) models switches as
pure two-state resistors (`Ron`/`Roff`) with **no parallel capacitance at
any switching node and no independent dead-time state** (`Mode.high_side_on`
is a single boolean per phase; the low side is always exactly the
complement -- confirmed by direct code reading, not inferred). This
means the existing fast solver structurally CANNOT represent a ZVS
resonant transition at all -- it is why the discrepancy discussed
earlier this session (`CONSOLIDATED_FINDINGS_2026-09-16.md`, "Cross-check
against the parallel math-model effort's newly-found periodic orbit")
exists: the ideal model has no ZVS energy requirement built in, by
construction, not by oversight.

**This prototype tests whether that gap can be closed cheaply**, by
adding switch capacitance and a genuine three-state (`HIGH`/`LOW`/
`DEADTIME`) per-phase mode to a COPY of the existing linear MNA
descriptor framework, reusing its own `E dz/dt + A z = r(t)` structure
(capacitance terms already live in `E`, conductance terms in `A` -- this
is a natural extension of an existing linear framework, not a new
numerical paradigm).

## 2. Exactly what is copied, and from where

Copied, unmodified on first commit, into `solver_copy/` (a local Python
package, import-path-isolated from `src/scb_ivr/`):

- `zero_start_descriptor.py` (`ZeroStartBoundary`, `Mode`, `DescriptorSystem`,
  `assemble_descriptor`, `commanded_pwm_mode`, `true_zero_initial_vector`)
- `zero_start_hybrid_solver.py` (`HybridStep`, `HybridTrajectory`,
  `advance_fixed_diode_step`, `diode_observation`, `complementarity_admissible`,
  `next_pwm_edge_s`)
- `periodic_affine_solver.py` (`AffinePeriodMap`, `PeriodicFixedPoint`,
  `PeriodicOrbitMetrics`, `propagate_fixed_diode_period`,
  `build_affine_period_map`, `solve_periodic_fixed_point`,
  `periodic_orbit_metrics`)
- `commutation_capacitance.py` (`CommutationCapacitance`,
  `from_device_population` -- ALREADY the exact "plug in a device's
  parameters" data structure the user asked for; not yet wired into any
  dynamic solver anywhere in the original codebase, confirmed by `grep`)
- `commutation_feasibility.py` (the closed-form single-phase formulas,
  used only for the Section 6 validation cross-check, not modified)
- `device_library.py`, `evidence.py` (dependencies of the above)

## 3. Exactly what is added, in the copy only

1. **`ZeroStartBoundary` gains two new optional fields**: `dead_time_s:
   float = 0.0` and `switch_capacitance: CommutationCapacitance | None =
   None`. Both default to values that reproduce the ORIGINAL behavior
   exactly (zero dead time, zero capacitance) -- this is a mandatory
   regression check (Section 6, first gate) before anything else is
   trusted.
2. **`Mode` changes from one boolean per phase (`high_side_on`, low side
   forced complementary) to two independent per-phase states**
   (`high_side_on: tuple[bool,...]`, `low_side_on: tuple[bool,...]`,
   both `False` simultaneously representing dead time for that phase).
3. **`commanded_pwm_mode` extended** to emit a `HIGH -> DEADTIME -> LOW ->
   DEADTIME -> HIGH...` schedule when `dead_time_s>0`, centered on the
   existing fixed-timing edges (same `T/4`-shifted phase pattern,
   unchanged) -- collapsing to the exact original two-state schedule when
   `dead_time_s=0`.
4. **`assemble_descriptor` gains parallel capacitance at every switch
   branch** (`vin-a1`, `a1-a2`, `a2-a3`, `a3-x4` for the four high sides;
   `x1-g`...`x4-g` for the four low sides), sourced from
   `boundary.switch_capacitance.high_total_f`/`low_total_f` when set,
   `0.0` (no change) when `None`. This is a direct, mechanical use of the
   EXISTING `add_capacitance` helper already in the file -- no new linear-
   algebra machinery required.
5. **One new function, `resolve_deadtime_window`**, that steps through a
   commanded dead-time interval at a fine, fixed sub-step (default `50 ps`,
   matching this project's own established SPICE `TMAX` convention from
   `R04E16-R04E26`), using the EXISTING `advance_fixed_diode_step`
   backward-Euler machinery unchanged, and reports: the minimum observed
   `|V(high-side node, next node)|` reached during the window, the time
   it occurred, and whether it crossed below a stated tolerance (default
   `1 mV`, matching A42's own already-published precision) before the
   window's commanded end -- i.e. a direct, non-inferred ZVS/no-ZVS
   verdict, reusing A37/A48's own existing SPICE-side diagnostic
   convention (residual voltage at forced turn-on) rather than inventing
   a new metric.

No other function signature changes. `build_affine_period_map`/
`solve_periodic_fixed_point`/`periodic_orbit_metrics` are used
UNCHANGED against boundaries that now happen to include capacitance and
dead time -- the affine-map machinery itself does not need to know
capacitance was added, since it is still a linear system (constant
capacitance only, Section 7).

## 4. Provenance of every new value used in the validation run (Section 6)

| Value | Source | Category |
|---|---|---|
| `CH=385 pF`, `CL=770 pF` | `A42_zero_snubber_negative_current_threshold/BOUNDARY.md`, "P25/external GS61008T charge-equivalent" | `EXTERNAL_DEVICE_DATA` (GS61008T datasheet-derived `Co(tr)`), reused verbatim from A42, not re-derived |
| Negative-current targets `7.76%`, `7.77%` of `125 A` | `A42_zero_snubber_negative_current_threshold/RESULTS.md`, "Outcome" section | `CROSS_PAPER_EXTENSION`-adjacent, A42's own already-published bracket, reused verbatim as the validation target, not re-derived |
| `dead_time_s` sub-step `50 ps` | This project's own established `TMAX` SPICE convention (`R04E16-R04E26`) | `NUMERICAL_IDEALIZATION` (a numerical-resolution choice) |
| Zero-crossing tolerance `1 mV` | A42's own published precision (`13.924 mV` no-cross vs `0 V` cross, reported to mV precision) | `NUMERICAL_IDEALIZATION` |
| Everything else (`LPHASE=1.4666667 nH`, `IPEAK=125 A`, `RHS`/`RLS` from GS61008T typical params) | A42's own already-published boundary, reused verbatim | See A42 `BOUNDARY.md` for original provenance |

## 5. What question this experiment answers

Can a copy of the parallel math model's own fast affine-periodic solver,
extended with real switch capacitance and genuine dead time, reproduce
A42's own already-SPICE-verified single-phase local ZVS threshold
(no crossing at `7.76%`, crossing at `16.6469 ns` for `7.77%`) -- to
validate the extension BEFORE it is trusted for anything new (the
four-phase joint case, or arbitrary future device parameters)?

## 6. Acceptance gates -- in order, each is a hard stop if failed

1. **Regression gate**: with `dead_time_s=0`, `switch_capacitance=None`,
   every existing behavior (the already-published `ZERO_START_
   AFFINE_PERIOD_FIXED_POINT.md` result: map residual `2.6e-11`, one-
   period closure error `2.3e-8`) must reproduce EXACTLY (bit-for-bit or
   to floating-point tolerance) through the copy. If this fails, the
   copy itself has a transcription bug -- stop and fix before adding
   anything new.
2. **A42 single-phase validation gate**: with `CH=385 pF`, `CL=770 pF`,
   `dead_time_s` set generously (e.g. `10 ns`, well above A42's own
   observed crossing time), a single-phase local commutation case
   (matching A42's own boundary as closely as this framework's own
   four-phase-only topology allows -- documented explicitly if an exact
   match is not possible) must show: **no crossing at `7.76%`** (minimum
   `|Vds|` staying near A42's own `13.924 mV`, not `0`), **a crossing at
   `7.77%`** within a stated tolerance of A42's own `16.6469 ns` timing
   (a `20%` timing tolerance is proposed given this is a materially
   different numerical method -- backward Euler descriptor vs LTspice's
   own trapezoidal/Gear solver -- not a guarantee of exact agreement;
   state whatever tolerance is actually achieved plainly, do not lower
   the bar after seeing the result).
3. **Only if both gates pass**: this prototype may be reported as
   validated for the single-phase case, and a follow-up (NOT performed
   here) could attempt the four-phase joint case. If either gate fails,
   report which one, by how much, and stop -- do not proceed to the
   four-phase case on an unvalidated single-phase result.

## 7. What this experiment cannot prove

- A positive validation result (both gates passed) would NOT itself
  constitute a four-phase joint-periodic-ZVS answer -- it would only
  certify the single-phase local physics is now correctly represented,
  which is a prerequisite for, not the same as, the four-phase question
  this whole thread exists to eventually answer.
- Constant/time-equivalent capacitance only (`Co(tr)`-style), matching
  A42's own convention -- NOT the nonlinear digitized `Coss(V)` A47 used.
  Extending to nonlinear capacitance (which A47 showed makes ZVS
  slightly HARDER, not easier) would break the linear affine-map
  machinery and is explicitly out of scope for this prototype.
- Does not modify, and is not merged into, `src/scb_ivr/` under any
  outcome per Section 0.
- Does not attempt the four-phase joint case, does not attempt any new
  device other than GS61008T (the only device with an already-published
  SPICE cross-check to validate against), does not claim any P24/P25
  reproduction.
- Consistent with this project's own standing practice regarding the
  parallel math-model effort: this experiment COPIES specific named
  files (Section 2) for its own independent extension, but does not
  claim to speak for or represent that effort's own future direction --
  it remains a Track-A-side, session-local prototype until/unless the
  user decides otherwise.
