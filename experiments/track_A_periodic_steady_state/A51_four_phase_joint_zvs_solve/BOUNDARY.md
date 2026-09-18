# A51 - searching for a self-consistent four-phase joint periodic ZVS state, using A50's validated fast solver (BOUNDARY)

Track: A (periodic steady-state reproduction). This is the main-line
continuation the user explicitly directed 2026-09-18 ("你直接开始搞4相的吧
你执行的时候必须要专注在主线任务") after A50 validated the underlying
single-phase physics. Any side-question needing its own verification
must be spun off as a separate, explicitly-scoped experiment, not folded
into this one (per the same instruction, "如果有需要验证的可以新开").

## 0. Scope statement

This does not claim a P24/P25 reproduction. It is the first attempt in
this project's history to search for a four-phase joint periodic ZVS
state using a FAST (seconds-per-evaluation) solver instead of SPICE
(20-100+ minutes per candidate, as A24-A49 required). A negative or
partial result is a fully valid, reportable outcome (Ground Rule 7,
unchanged) -- this experiment's job is to search competently and report
honestly, not to manufacture a positive result.

## 1. Pre-flight consistency check performed before writing this boundary

Per explicit user instruction ("这个单相的边界条件你也要看一下是不是真的
一贯而终的 不要中间又换了就又不行了"), before designing this experiment
the following was checked, not assumed:

**Finding: `A41/A42/A45/A47/A48/A50` all inherited the same cross-topology
`CFLY=53.8 uF` placeholder** (`CURRENT_ASSUMPTION_CROSSCHECK.md`'s own
already-documented finding: the value is EPE2019 Table I's CSC-buck
component list, a different topology, not a P24 value) -- the SAME error
`R04E8`/`R04E21`/`A49` already corrected to `3 uF` elsewhere in this
project, but never corrected in the `A41-A48`/`A50` lineage.

**Directly tested, not assumed, using A50's own validated solver**
(reproduced independently before writing this document):

| `CFLY` | `7.76%` min `|Vds|` | `7.77%` crossed | `7.77%` crossing time |
|---:|---:|:---:|---:|
| `53.8 uF` (A42's own value) | `7.867 mV` | yes | `t=23.14711541 us` (absolute) |
| `3 uF` (corrected value) | `9.094 mV` | yes | `t=23.14711995 us` (absolute) |

The qualitative bracket (no-cross at `7.76%`, cross at `7.77%`) and the
crossing time (agreement to `5 us`-scale... actually agreement to within
`5 ns` of an `23 us`-scale absolute time, i.e. sub-`0.0001%`) are
UNCHANGED by this correction -- confirmed analytically too:
`a42_local_validation.py`'s own closed-form `analytic_lossless_
commutation` depends only on `LPHASE`, switch capacitance, `Vout` and the
negative current -- `CFLY` does not appear in it at all, because the
flying capacitor is orders of magnitude larger than the switch
capacitance and acts as an effectively fixed voltage source on the
few-nanosecond commutation timescale, regardless of whether it is `3 uF`
or `53.8 uF`. **Conclusion: A50's own single-phase validation remains
valid under the corrected `CFLY`, and this experiment uses `CFLY=3 uF`
throughout** (matching Track B's `R04E8` correction and `A49`'s own
already-established fix), not A42's own uncorrected legacy value -- this
is the one deliberate departure from "reuse A50/A42 exactly."

## 2. What is reused, unchanged, from A50

**No new source copy is made.** This experiment imports A50's own
already-committed, already-validated `solver_copy` package directly
(`experiments/track_A_periodic_steady_state/A50_zvs_capable_solver_
prototype/solver_copy/`) -- that package is no longer "the other track's
protected code" (it was copied there specifically for this project's own
Track-A use and passed both its own validation gates); duplicating it
again here would only create a second copy to keep in sync for no
benefit. The `src/scb_ivr/` constraint from A50 Section 0 still applies
unchanged: nothing under `src/scb_ivr/` is read from or written to here
either.

## 3. The problem, stated precisely

Represent the full system state as the same 20-variable descriptor vector
`z` already used throughout (`src/scb_ivr/zero_start_descriptor.py`'s own
node/inductor/source ordering). One PWM period, with real dead time and
switch capacitance now present (A50's own extension), induces a map
`z_next = F(z)` that is **not affine** (unlike the ideal, zero-capacitance
case `periodic_affine_solver.py` already solves in closed form) --
whether and when each phase's own dead-time window ends in a natural
zero-voltage crossing depends on the state itself, so `F` must be
evaluated by literally propagating one period forward through the
event-resolving logic (fine sub-stepping inside each of the four
dead-time windows via `resolve_deadtime_window`, coarser stepping
elsewhere via the existing `advance_fixed_diode_step`), not read off a
precomputed matrix.

**The question**: does `z* = F(z*)` have a solution reachable from a
reasonable seed, and if so, does every one of the four phases actually
achieve a natural zero-voltage crossing at that solution (not a forced/
hard turn-on)? A solution where `F(z*)=z*` but one or more phases are
hard-switched is still periodic but is NOT a ZVS solution -- both
conditions must be checked and reported separately, not conflated.

## 4. Method (latitude for engineering judgment within these guardrails)

1. **Seed from `A37`'s own already-published best candidate**
   (`A37_p25_9pct_joint_seven_state_200ns_periodic_solve/`'s own
   `IL1_INIT=5.2947`, `IL2_INIT=21.205095337`, `IL3_INIT=41.5782701063`,
   `IL4_INIT=84.1447433786`, `VC1_INIT=36.000066454`, `VC2_INIT=
   23.9999142326`, `VC3_INIT=12.0006048777`) -- this project's own most-
   converged four-phase SPICE candidate to date (3 of 15 residuals),
   NOT the math model's own ideal periodic orbit, which `A49` already
   found performs WORSE in this exact style of test. Convert to this
   framework's own 20-variable descriptor ordering explicitly and show
   the conversion (do not silently assume the mapping).
2. **Evaluate `F(z)` by full event-resolved one-period propagation**,
   using `CFLY=3 uF` (Section 1), `CH=385 pF`/`CL=770 pF` (GS61008T,
   unchanged from A42/A50), `IPEAK=125 A`-scale currents (consistent with
   the seed), and a `dead_time_s` chosen from `A48`'s own already-
   published practical bracket (centered near `2.15 ns` for the `7.77%`
   single-phase case) as a starting value -- report plainly if a
   different dead time turns out to be needed for the coupled case.
3. **Search for `z*` such that `F(z*)=z*`**, either by direct (damped)
   Picard iteration or by a numerically-differentiated Newton step,
   whichever the implementer finds converges -- this is an engineering
   choice, not a boundary constraint. Cap the search at a stated, finite
   number of iterations (propose 50, adjustable if progress is still
   visibly being made) and report the final residual whether or not it
   reaches a stated tolerance (propose `1e-6` relative, matching this
   project's own established `solve_periodic_fixed_point` convention) --
   do not silently keep iterating past a predeclared budget in search of
   a nicer number (Ground Rule 7).
4. **At the (converged or best-effort final) state, check EVERY phase's
   own dead-time window independently** using `resolve_deadtime_window`
   with step-size convergence (per A50's own established discipline --
   do not report a single-sub-step result as final): did it cross, at
   what time, at what residual voltage if not. Report all four phases'
   own results individually, explicitly following `A44`'s own finding
   that phases are NOT interchangeable and the flying-capacitor voltages
   (not device parameters) are the high-leverage coordinates -- do not
   assume phase symmetry.

## 5. Provenance of every value used

| Value | Source | Category |
|---|---|---|
| `CFLY=3 uF` | `R04E8`'s own correction, `A49`'s own precedent, re-validated for this specific use in Section 1 above | `NUMERICAL_IDEALIZATION`-adjacent engineering correction |
| Seed state (`IL1-4_INIT`, `VC1-3_INIT`) | `A37`'s own already-published best candidate | `CROSS_PAPER_EXTENSION` (`9%` branch), reused verbatim, not re-derived |
| `CH=385 pF`, `CL=770 pF`, `RHS`/`RLS` | `A42`'s own already-published GS61008T plug-in, re-validated in `A50` | `EXTERNAL_DEVICE_DATA` |
| `dead_time_s` starting value (`~2.15 ns`) | `A48`'s own already-published practical bracket | `SENSITIVITY_ONLY`, inherited, explicitly open to revision (Section 4.2) |
| `IPEAK=125 A` | P24's own locked Table-1 peak current | `P24_EXPLICIT` |
| Everything else | See A37/A42/A48/A50 `BOUNDARY.md` for original provenance | unchanged |

## 6. Success/failure conditions

- **A genuine fixed point found (`F(z*)-z* ` below tolerance) with all
  four phases independently confirmed to cross naturally**: this would be
  the first self-consistent four-phase joint ZVS periodic state found
  anywhere in this project's history, by any method. Report with full
  numerical detail and flag prominently for the user -- this is a
  significant result if it happens.
- **A fixed point found but one or more phases do NOT cross naturally**
  (hard-switches instead): report exactly which phase(s), the residual
  voltage at forced turn-on for each, and -- per `A44`'s own finding --
  which state coordinates (`VC1`/`VC2`/`VC3` most likely) the failure is
  most sensitive to, if that can be characterized cheaply within this
  experiment's own remaining budget. This is a genuinely informative
  negative/partial result, directly comparable to `A37`'s own "H3/H4
  never admit" finding but now backed by a much larger, fast-searchable
  neighborhood instead of `174` slow SPICE points.
- **No fixed point found within the iteration budget** (map does not
  converge, or diverges): report the iteration trajectory's own
  behavior (diverging, oscillating, or just slow) plainly, and do not
  extend the budget silently without flagging that this was done and why.
- Every phase current must stay within `+/-250 A` throughout the search
  (same standing safety bound as every other experiment in this project).

## 7. What this experiment cannot prove

- A positive result (self-consistent ZVS state found) would NOT itself
  constitute a P24/P25 reproduction claim -- it would be strong grounds
  for a SPICE cross-check (build the corresponding real netlist and
  verify independently, the same discipline `R04E20`-style cross-track
  results already follow), not a substitute for one.
- Does not modify `src/scb_ivr/`, `A37`'s own files, `A42`'s own files,
  or `A50`'s own already-committed files -- imports A50's `solver_copy`
  read-only.
- Does not attempt any device other than GS61008T, nor the P24-primary
  `1-2%` branch (this remains the `9%`-branch-adjacent search, same
  standing limitation as `A37`).
- Does not resolve `MINIMUM_INFORMATION_REQUEST.md`'s own standing gaps
  (real dead-time/driver data from Mihai) -- `dead_time_s` here remains
  an engineering choice (Section 5), not a confirmed hardware value.
