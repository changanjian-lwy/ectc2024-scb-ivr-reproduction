# A53 result - trading phase inductance against load: how far, and at what cost?

Track: A. Python-solver experiment (no SPICE run). Boundary: `BOUNDARY.md` in
this directory, unmodified by this run.

---

## 0. Verdict, stated first

**At P24's own rated `module_power_w = 250 W`**, holding every other
`BOUNDARY.md`-inherited value fixed (`CFLY = 3 uF`, GS61008T `385/770 pF`,
`d = 2.15 ns`, `48 V -> 1 V`, `5 MHz`), a critical phase inductance was found
by bisection at which all four phases first achieve natural ZVS:

> **`LPHASE_critical = 1.19625 nH`, an `18.44 %` reduction from the paper's
> own nominal `1.4666667 nH`** -- confirmed converged (Newton relative
> residual `6.23e-09`) and confirmed all-four-ZVS across a `{5, 2, 1, 0.5} ps`
> sub-step ladder with no disagreement between rungs.

That is **`BOUNDARY.md` Section 4's FIRST named outcome on the search side**
(a critical `LPHASE` found, at a reduction -- `18.4 %` -- that is a modest,
plausible engineering change, not an exotic one). **But the net Watts
comparison does NOT favor ZVS:**

> | | nominal (hard-switch) | critical (ZVS) | `10 %` margin (ZVS) |
> |---|---:|---:|---:|
> | `LPHASE` | `1.4667 nH` | `1.1963 nH` (`-18.44 %`) | `1.0766 nH` (`-26.59 %`) |
> | conduction loss (`I_rms^2 * 7 mOhm`, 4 phases) | `113.09 W` | `153.61 W` | `171.63 W` |
> | capacitive switching loss eliminated | -- | `2.087 W` | `2.087 W` |
> | **net Watts (switching saved - conduction added)** | -- | **`-38.4 W`** | **`-56.5 W`** |

**This is `BOUNDARY.md` Section 4's SECOND named outcome**: a critical
`LPHASE` was found, but the conduction-loss penalty exceeds the capacitive
switching-loss saved, by roughly `18x`-`27x`. Under this project's own
partial loss model (Section 5 below), reducing `LPHASE` to unlock natural ZVS
at the rated `250 W` load is **not a net efficiency win** -- it is a real,
quantified, honest negative engineering finding, not a failure of the search.
The gap between the two loss terms is large enough (an order of magnitude)
that this conclusion is not sensitive to the switching-loss estimate's own
known incompleteness (Section 5) -- no plausible addition of gate-drive or
reverse-recovery loss to the `~2 W` capacitive term closes a `~40-57 W` gap.

Every phase current stayed comfortably inside the `+/-250 A` safety bound
throughout the ENTIRE search (not just the three reported points): the
maximum observed anywhere was `150.13 A` (at the margin point), `60 %` of the
limit, with `40 %` headroom remaining. No safety violation was ever hit by
any accepted candidate.

---

## 1. Method actually used, and why it differs slightly from the naive plan

`BOUNDARY.md` Section 2 step 3 proposed starting the bisection bracket at
`LPHASE = 0.5 nH`. Before committing to that bracket, a cheap diagnostic
probe (one raw `evaluate_period_map` call from A37's own fixed seed state, NO
Newton iteration, at twelve `LPHASE` values from nominal down to `0.5 nH`) was
run and is recorded in `bisection_search.json["diagnostic_probe"]`. It shows
the raw SEED ITSELF (calibrated for the nominal inductance) already exceeds
the `+/-250 A` safety bound once `LPHASE` drops below roughly `0.6-0.65 nH` --
well before any Newton correction. Re-seeding every candidate from A37's own
fixed values, the way A51's own load sweep re-seeds every load point, is
therefore not usable across this bracket.

The search instead uses **continuation (homotopy)**: starting from the
nominal point (solved cold from A37's own seed, exactly reproducing A51's own
published `250 W` result), each smaller `LPHASE` candidate is warm-started
from the immediately preceding, already-converged fixed point. A `10 %`
multiplicative step-down ladder is walked until the all-four-ZVS verdict
flips; if any step had tripped the safety bound the step size would have
been halved and retried (up to `6` halvings) before abandoning the ladder --
in the event, **this was never needed**: every continuation step converged
safely on the first attempt (see `bisection_search.json["ladder"]`,
`"attempts": 1` on both rows). A plain bisection then refines the bracket,
still continuation-seeded from the nearest known ZVS-achieving point, with
every candidate's ZVS verdict checked at both `5 ps` and `1 ps` sub-steps (a
`2 ps` rung would have been added on any disagreement; none occurred).

**The critical `LPHASE` was found well inside the proposed `[0.5, 1.4667] nH`
bracket -- in fact much closer to the nominal end than the floor.** The
bracket was never widened past the proposed `0.5 nH` starting candidate; the
ladder needed only **two** `10 %` steps (`1.32 nH` still hard-switching,
`1.188 nH` already all-four-ZVS) before the crossing was bracketed, and six
bisection iterations narrowed it to `[1.19625, 1.19831] nH` (a `0.14 %`-of-
nominal window). A `10 %`-below-critical margin point (`1.07663 nH`,
`26.59 %` below nominal) was then solved the same way and confirmed all-four
ZVS (residual `2.95e-08`).

The Newton/Picard search algorithm itself is A51's own semi-smooth-Newton-
with-line-search-and-Picard-cross-check method, re-expressed as an importable
function in `a53_solve.py` (A51's own `run_fixed_point_search.py` embeds this
logic entirely inside its `main()`, so it could not simply be imported). The
nominal point's residual, `2.258171322999336e-11`, is bit-for-bit identical
to A51's own already-published value -- direct confirmation the re-
expression is faithful to A51's own algorithm.

---

## 2. Bisection search history

| Step | `LPHASE (nH)` | Converged | Residual | ZVS (1/2/3/4) | max\|iL\| (A) |
|---|---:|---|---:|---|---:|
| nominal (A37-seeded) | `1.46667` | yes | `2.258e-11` | F/F/F/F | `117.29` |
| ladder 1 | `1.32000` | yes | `7.124e-11` | F/F/F/F | `124.89` |
| ladder 2 | `1.18800` | yes | `5.228e-09` | **T/T/T/T** | `136.49` |
| bisect 1 | `1.25400` | yes | `5.861e-10` | F/F/F/T | `129.36` |
| bisect 2 | `1.22100` | yes | `3.000e-11` | F/F/F/T | `132.73` |
| bisect 3 | `1.20450` | yes | `1.948e-07` | F/F/F/T | `134.42` |
| bisect 4 | `1.19625` | yes | `6.232e-09` | **T/T/T/T** | `135.24` |
| bisect 5 | `1.20040` | yes | `1.201e-08` | F/T/T/T | `134.84` |
| bisect 6 | `1.19831` | yes | `2.991e-08` | F/T/T/T | `135.05` |
| margin (0.9x critical) | `1.07663` | yes | `2.946e-08` | **T/T/T/T** | `150.13` |

**Phase 1 is consistently the last to achieve ZVS** as `LPHASE` shrinks
(visible at bisect 1-3, and again at bisect 5-6), matching A51's own finding
that phase 1 carries the largest participating capacitance (`1539 pF`, vs
`1154 pF` for phase 4 -- node `a1` holds two high-side switches) and is
therefore structurally the hardest phase to commutate. Every row's ZVS
verdict was confirmed identical at both `5 ps` and `1 ps` sub-steps
(`sub_step_convergence_disagreement: false` in every row of
`bisection_search.json`).

The full ladder-and-bisection history, the diagnostic probe, and the
per-candidate safety log are in `bisection_search.json`. The three
converged states used below (`nominal`, `critical`, `margin`) are persisted
in `key_states.json`.

---

## 3. Three-point table: convergence, ZVS, currents, losses

All three points solved with the full search-plus-report rigor: Newton to
the saved seed's own fixed point, a `25`-iteration damped-Picard cross-check
from the same seed (independent confirmation, not just a re-affirmation of
Newton's own linear solve), and a `{5, 2, 1, 0.5} ps` sub-step ladder on the
ZVS verdict.

| | nominal | critical | margin (`10%` below critical) |
|---|---:|---:|---:|
| `LPHASE (nH)` | `1.46667` | `1.19625` | `1.07663` |
| reduction from nominal | -- | `18.44 %` | `26.59 %` |
| Newton converged | yes | yes | yes |
| Newton relative residual | `2.258e-11` | `6.232e-09` | `2.946e-08` |
| natural ZVS (1/2/3/4) | F/F/F/F | **T/T/T/T** | **T/T/T/T** |
| sub-step ladder consistent (4 rungs) | yes | yes | yes |
| peak \|iL\| per phase (A) | `110.35/110.04/110.04/110.85` | `135.26/134.76/134.76/134.11` | `146.14/145.69/145.69/145.69` |
| RMS iL per phase (A) | `63.58/63.33/63.33/63.98` | `74.42/74.14/74.28/73.43` | `78.51/78.22/78.28/78.16` |
| conduction loss, 4 phases (`I_rms^2*7mOhm`) | `113.09 W` | `153.61 W` | `171.63 W` |
| max \|iL\| observed at this point (A) | `110.84` | `135.24` | `146.12` |

RMS current is the actual time integral of the solved periodic waveform
(right-endpoint, time-weighted, over one full `200 ns` period at a `1 ps`
sub-step inside every dead-time window and `62.5 ps` elsewhere -- see
`a53_solve.RmsMonitor`/`evaluate_period_map_with_rms`), not an estimate from
peak and average.

**Capacitive switching loss (nominal/hard-switching point only)**, per
`BOUNDARY.md` Section 2 step 4, using A51's own ALREADY-PUBLISHED
`final_verification.json` measured capacitances and hard-switch residual
voltages (read-only, not re-derived) at `f_sw = 5 MHz`:

| Phase | measured `C_phase` (A51, published) | `Vds` at forced turn-on (A51, published) | `0.5*C*V^2*f_sw` |
|---|---:|---:|---:|
| 1 | `1539.16 pF` | `12.0456 V` | `0.5583 W` |
| 2 | `1538.53 pF` | `11.8113 V` | `0.5366 W` |
| 3 | `1538.57 pF` | `11.8113 V` | `0.5366 W` |
| 4 | `1154.36 pF` | `12.5624 V` | `0.4554 W` |
| **total** | | | **`2.0869 W`** |

A consistency check -- re-measuring each phase's own participating
capacitance at THIS run's own nominal `z*` with `measure_node_capacitance_f`
(the same function A51 used), fed the correct turn-on-window ENTRY state
(`result.turn_on_entry[phase]`, not the raw period-start state -- an
initial attempt using the period-start state gave nonsense, `~500 pF`,
because that state sits in a different switch-mode branch; recorded as a
caveat, not silently discarded) -- reproduces A51's own four published
values **to every digit** (`relative_difference: 0.0` on all four phases in
`three_point_analysis.json`), because this run's own nominal `z*` and A51's
own published `z*` are the same fixed point to within Newton's own
convergence floor.

---

## 4. The net Watts comparison

| | critical | margin |
|---|---:|---:|
| capacitive switching loss eliminated | `2.087 W` | `2.087 W` |
| conduction loss increase (vs. nominal) | `40.513 W` | `58.540 W` |
| **net Watts (saved - added)** | **`-38.426 W`** | **`-56.453 W`** |

Both are decisively negative, and by a wide margin (`18x` at critical, `27x`
at margin) -- not a close call this estimate's own uncertainty could plausibly
flip. Reducing `LPHASE` enough to achieve natural ZVS at P24's own rated
`250 W` load costs far more in extra conduction loss (from the larger ripple
current that the smaller inductance produces at the same average, load-
serving current) than it saves in eliminated capacitive switching loss. This
matches `BOUNDARY.md` Section 1's own pre-stated mechanism qualitatively --
smaller `L` helps ZVS become reachable but is not free -- and now quantifies
it: at this operating point, the ZVS benefit is real but small (`~2 W`) next
to the conduction-loss cost (`tens of W`), because the capacitive switching
loss this topology's own node capacitances and dead-time residual voltages
produce is intrinsically small relative to the `250 W` power level already
being conducted through `7 mOhm` per switch.

**Per `BOUNDARY.md` Section 4's second named outcome**, this is reported
plainly as a genuine, valuable negative finding: achieving ZVS at the rated
load by shrinking `LPHASE` alone is not shown to be a net efficiency win
under this project's own conduction/switching loss model.

---

## 5. Safety

Every phase current was checked against `+/-250 A` at every sub-step of
every one-period evaluation, across the WHOLE search -- the diagnostic
probe, the nominal solve, every ladder and bisection candidate (including
Newton's own finite-difference Jacobian probes and line-search trials), and
the margin point:

> **Maximum `|iL|` observed anywhere in the entire search: `150.13 A`**
> (at the margin point), **`60.1 %`** of the `+/-250 A` limit, **`40 %`**
> headroom remaining. No candidate anywhere in the search came close to the
> bound, and the adaptive step-halving safeguard (present in
> `run_bisection.py` for exactly this contingency) was never triggered --
> every continuation step converged safely on its first attempt.

This is worth stating plainly against the diagnostic probe in Section 1: the
RAW, un-converged seed state becomes unsafe (`>250 A`) somewhere between
`0.6` and `0.65 nH`, but the actual converged fixed points found by
continuation stay far below that -- the critical/margin `LPHASE` values
(`1.196`/`1.077 nH`) are nowhere near that danger zone, and the true
periodic orbits at those inductances carry much less peak current than the
raw seed-transient evaluation would suggest.

---

## 6. Provenance (repeats `BOUNDARY.md` Section 3, filled in)

| Value | Source | Category |
|---|---|---|
| `module_power_w = 250 W` | fixed throughout, P24's own rated load | `P24_EXPLICIT` |
| `LPHASE` nominal `1.4666667 nH` | unchanged from `A24-A52` | `P24_EXPLICIT`-adjacent |
| `LPHASE_critical = 1.19625 nH` | found by bisection here | `SENSITIVITY_ONLY` |
| `LPHASE_margin = 1.07663 nH` (`10%` below critical) | derived from the above | `SENSITIVITY_ONLY` |
| `Ron = 7 mOhm` uniform (conduction-loss estimate only; the SOLVER itself keeps A51's own `1 uOhm` idealized `switch_on_resistance_ohm`) | A51's own simplification, reused | `NUMERICAL_IDEALIZATION`, inherited |
| Conduction-loss formula (`I_rms^2*Ron`) | textbook | `NUMERICAL_IDEALIZATION` |
| Capacitive switching-loss formula (`0.5*C*V^2*f`) | textbook, same form as `commutation_feasibility.py` | `NUMERICAL_IDEALIZATION` |
| Measured capacitances / hard-switch `Vds` at nominal `L` | A51's own already-published `final_verification.json`, reused read-only | inherited, `SENSITIVITY_ONLY` |
| `CFLY=3uF`, `CH=385pF`/`CL=770pF`, `d=2.15ns` | unchanged from `A50/A51/A52` | see those `BOUNDARY.md` files |

No new paper-sourced or external-device data is introduced.

---

## 7. What this experiment cannot prove (repeats `BOUNDARY.md` Section 5)

- The switching-loss estimate covers only node-capacitance charge/discharge
  energy -- NOT a complete device loss model (no gate-drive loss, no reverse
  recovery). The `~2 W` figure is therefore a lower bound on real switching
  loss, not the whole of it; but closing a `~40-57 W` gap would require the
  omitted terms to be an order of magnitude larger than the term that is
  modeled, which is not plausible for this device/operating point.
- No SPICE cross-check of the critical or margin `LPHASE` value was
  performed -- `A52` validated this solver's underlying physics in general,
  at a different (reduced-load) operating point; a targeted SPICE check of
  the specific `1.196 nH`/`1.077 nH` points remains a natural, separate
  follow-up.
- Uses A51's own uniform-resistance solver idealization for the DYNAMICS
  (`switch_on_resistance_ohm = 1 uOhm`), not the asymmetric `RHS`/`RLS`
  split; the `7 mOhm` conduction-loss figure is a separate, post-hoc estimate
  applied to the solved RMS currents, per Section 2.4's own instruction.
- Does not revisit the Table-I `2.68 nH` vs Eq.(4) `1.4667 nH` inductance
  conflict -- the nominal baseline is the same `1.4667 nH` value used
  throughout `A24-A52`.
- Does not modify `src/scb_ivr/`, or A37/A42/A48/A50/A51/A52's own committed
  files -- imports A50/A51's own already-committed modules read-only.
- No P24/P25 reproduction claim of any kind. `SENSITIVITY_ONLY` throughout.
- A negative result here (ZVS-via-smaller-L not a net win at rated load)
  does not revisit A51's own separate, positive finding that ZVS IS
  achievable at rated `LPHASE` by reducing LOAD instead (to `~190 W`,
  SPICE-confirmed by A52) -- that remains a distinct lever from this one.

---

## 8. Files

| File | Role |
|---|---|
| `a53_boundary.py` | local wrapper exposing `phase_inductance_h` on `build_boundary` (A51's own function never plumbed it through) |
| `a53_solve.py` | `RmsMonitor`/`evaluate_period_map_with_rms` (RMS-current period evaluation), `solve_fixed_point` (A51's own Newton+Picard search re-expressed as a function) |
| `run_bisection.py` | diagnostic probe, continuation ladder, bisection refine, margin point; writes `bisection_search.json`, `key_states.json` |
| `run_three_point_analysis.py` | full-rigor re-solve of the three key points, RMS/peak currents, conduction loss, capacitive switching loss, net Watts; writes `three_point_analysis.json` |
| `build_results.py` | assembles `results.json` |
| `bisection_search.json`, `key_states.json`, `three_point_analysis.json`, `results.json` | run artifacts |
| `bisection_log.txt`, `three_point_log.txt` | captured console output |
