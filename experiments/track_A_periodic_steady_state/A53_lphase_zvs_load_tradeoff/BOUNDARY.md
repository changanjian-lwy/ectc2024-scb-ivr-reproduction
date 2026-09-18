# A53 - trading phase inductance against load: how far can the ZVS boundary be pushed toward P24's own rated 250 W, and at what cost? (BOUNDARY)

Track: A (periodic steady-state reproduction). Main-line continuation
per explicit user direction 2026-09-19 ("代价...是个要权衡的工程问题
不是免费的。你做一下这个的自动化调整工作 看能不能找到一个平衡点" --
automate the search for a balance point in this cost/benefit tradeoff).

## 0. Scope statement

This does not claim a P24/P25 reproduction. It is an engineering
optimization built on top of the already-validated `A50`/`A51` fast
solver: `A51`'s own load sweep found that P24's rated `250 W` load
defeats natural ZVS on all four phases (with the paper's own nominal
`LPHASE=1.4666667 nH`), while ZVS is achieved at `~190 W`. Reducing
`LPHASE` increases the phase-current ripple, which is the OTHER lever
(besides load) in the same `i_min = i_avg - dI/2` balance already
established (`A51`'s own `run_load_sweep.py` docstring, quoted in the
prior consolidation) -- this experiment holds load at P24's own rated
`250 W` and searches `LPHASE` downward instead, to find how much
inductance reduction is needed, and quantifies what it costs.

## 1. Why this is a real tradeoff, stated with the actual formulas being used, not just qualitatively

Two competing effects as `LPHASE` decreases, both already implicit in
the solver's own physics (not new assumptions):

- **Ripple current increases** (`dI` scales roughly `1/L` for fixed
  voltage/on-time), which is exactly the quantity that must exceed
  `2*(i_avg + I_threshold)` for `i_min` to dip below `-I_threshold`
  (Section on mechanism, prior consolidation) -- so smaller `L` helps
  ZVS become reachable at a higher `i_avg` (i.e. higher load).
- **The ZVS current threshold itself also changes with `L`**
  (`threshold_current_a` in `A50`'s own `a42_local_validation.py`:
  `threshold ∝ sqrt(C/L)`, i.e. threshold INCREASES as `L` decreases) --
  partially offsetting the ripple benefit, not free.
- **Conduction loss increases** with the larger RMS current a bigger
  ripple implies, at the SAME average (load-serving) current.
- **Capacitive switching loss decreases toward zero** once ZVS is
  achieved (the charge/discharge-loss component `0.5*C*V^2*f_sw` per
  hard-switched transition is exactly what a natural zero-voltage
  crossing eliminates) -- this is the benefit side of the same tradeoff,
  in the same units (Watts), enabling a genuine net comparison.

This experiment quantifies BOTH sides in Watts using the SAME already-
validated solver and formulas already present in this project's own
code (`A50`'s `commutation_feasibility.py`/`a42_local_validation.py`),
not new, unverified estimates.

## 2. Method

1. **Reuse `A51`'s own already-committed `a51_period_map.py` functions**
   read-only (`build_boundary`-equivalent construction, `a37_seed_state`,
   `evaluate_period_map`, `relative_residual`) -- do not modify A51's own
   file. Write a new, local wrapper that adds `phase_inductance_h` as an
   explicit parameter to the boundary construction (`ZeroStartBoundary`'s
   own dataclass already has this field with the paper's own nominal
   default; A51's own `build_boundary` simply never exposed it as a
   sweep variable).
2. **Fix `module_power_w=250.0`** (P24's own rated load, `IPEAK_P24_A`-
   consistent) throughout -- this is the one change from A51's own load
   sweep: hold load at the paper's own value, sweep `LPHASE` instead.
3. **Bisect `LPHASE`** between the paper's own nominal `1.4666667 nH`
   (already confirmed: all four phases hard-switch at `250 W`, `A51`'s
   own result) and a substantially smaller candidate (propose starting
   at `0.5 nH`; adjust the bracket if the boundary is not inside it,
   report whatever bracket was actually needed) to find the CRITICAL
   `LPHASE` at which the four-phase joint fixed point first achieves
   natural ZVS on all four phases at `250 W`. Use the same Newton/Picard
   fixed-point search discipline `A51` established (cap iterations,
   report residual and convergence plainly, do not force a nicer number).
4. **At three points -- the paper's own nominal `L`, the critical
   boundary `L`, and a stated safety-margin `L`** (propose `10%` further
   below critical, adjustable and to be reported plainly if changed) --
   report, for each: convergence/residual, per-phase natural-ZVS
   verdicts (with the same step-size-convergence discipline `A50`/`A51`
   established, not a single sub-step), peak and RMS phase currents
   (RMS computed from the actual solved periodic waveform, not
   estimated), and:
   - **Conduction loss estimate**: `sum over 4 phases of I_rms^2 *
     Ron` (`Ron=7 mOhm`, matching `A51`'s own uniform-resistance
     convention -- do not silently switch to asymmetric `RHS`/`RLS`
     here, for the same reason `A52` gave: it would test a different
     model than the one whose ZVS states are being compared).
   - **Capacitive switching-loss estimate** (only meaningful at the
     nominal-`L`/hard-switching point): `sum over 4 phases of
     0.5 * C_phase * Vds_at_forced_turn_on^2 * f_sw`, using each
     phase's own ALREADY-MEASURED participating capacitance and hard-
     switch residual voltage from `A51`'s own already-published `250 W`
     result (`measure_node_capacitance_f`, already used in `A51`) --
     explicitly labelled as an ENGINEERING ESTIMATE covering only the
     node-capacitance charge/discharge component of switching loss, NOT
     a complete device switching-loss model (no gate-drive loss, no
     reverse-recovery, no measured hardware data).
5. **Report the net Watts comparison**: conduction-loss increase (nominal
   L to critical/margin L) vs capacitive switching-loss decrease
   (hard-switching to ZVS) -- state plainly whether the net effect is a
   loss reduction, an increase, or inconclusive given the estimate's own
   stated limitations. Do not round this into a single confident number
   if the underlying estimate does not support that precision.

## 3. Provenance of every value

| Value | Source | Category |
|---|---|---|
| `module_power_w=250 W` | P24's own rated per-module power (`SOURCE_COVERAGE_MATRIX.md`, already `LOCKED`) | `P24_EXPLICIT` |
| `LPHASE` nominal `1.4666667 nH` | P24 Eq. (4)-derived value, already used throughout `A24-A52` | `P24_EXPLICIT`-adjacent (the Table-I `2.68 nH` conflict branch is unchanged/not revisited here) |
| Critical/margin `LPHASE` values | New for this experiment: found by bisection, not assumed | `SENSITIVITY_ONLY` |
| `Ron=7 mOhm` uniform | `A51`'s own simplification, reused for direct comparability | `NUMERICAL_IDEALIZATION`, inherited |
| Conduction-loss formula (`I_rms^2*Ron`) | Standard, textbook resistive-loss relation | `NUMERICAL_IDEALIZATION` (a general-physics estimate, not a P24/P25 equation) |
| Capacitive switching-loss formula (`0.5*C*V^2*f`) | Standard, textbook capacitive charge/discharge energy relation, same form already used in `commutation_feasibility.py`'s own `isolated_lc_capacitance_ceiling_f`/related functions | `NUMERICAL_IDEALIZATION` |
| `CH=385 pF`/`CL=770 pF`, `CFLY=3 uF`, `dead_time_s=2.15 ns` | Unchanged from `A50`/`A51`/`A52` | See those `BOUNDARY.md` files |

No new paper-sourced or external-device data is introduced.

## 4. Success/failure conditions

- **A critical `LPHASE` is found within the search bracket, at a
  reduction that seems practically achievable (report the actual
  percentage reduction from nominal; do not pre-judge what counts as
  "achievable"), and the net Watts comparison favors ZVS**: a genuinely
  actionable engineering recommendation -- report clearly, with the
  explicit caveat that this remains `SENSITIVITY_ONLY` (Section 5) and
  the capacitive-loss estimate's own stated limitations.
- **A critical `LPHASE` is found but the conduction-loss penalty
  exceeds the capacitive switching-loss saved**: report this plainly --
  achieving ZVS at rated load this way would not be a net efficiency win
  under this specific (partial) loss model, which is itself a valuable,
  honest finding, not a failure of the experiment.
- **No critical `LPHASE` is found inside a reasonable bracket** (e.g. the
  boundary requires `LPHASE` below some value judged impractical, or the
  search does not converge): report the bracket actually explored and
  where it was abandoned, per Ground Rule 7 -- do not silently keep
  shrinking `L` in search of a result.
- Every phase current must stay within `+/-250 A` throughout the search
  (report explicitly if the reduced-`L` ripple pushes any case close to
  this bound -- a real practical constraint, not just an efficiency one).

## 5. What this experiment cannot prove

- The switching-loss estimate covers only node-capacitance charge/
  discharge energy -- NOT a complete device loss model. A real
  efficiency claim would need real device switching-loss data (gate
  charge, reverse recovery, etc.), which remains one of
  `MINIMUM_INFORMATION_REQUEST.md`'s own standing gaps.
- Does not include a SPICE cross-check of whichever specific `LPHASE`
  value is eventually recommended -- `A52` already validated this
  solver's underlying physics in general; a targeted SPICE check of the
  SPECIFIC recommended operating point (mirroring `A52`'s own method)
  remains a natural, separate follow-up, not performed here.
- Does not use the asymmetric, more realistic `RHS`/`RLS` (Section 2.4's
  own restated reason) -- inherits `A51`'s own uniform-resistance
  simplification.
- Does not revisit the Table-I `2.68 nH` vs Eq.(4) `1.4667 nH`
  inductance-branch conflict (`Gate 3` in `NEXT_STEPS_2024_MAIN.md`) --
  the nominal-`L` baseline used here is the SAME `1.4667 nH` value
  already used throughout `A24-A52`, not a re-litigation of that
  standing conflict.
- Does not modify `src/scb_ivr/`, or A37/A42/A48/A50/A51/A52's own
  committed files -- imports A51's own already-committed modules
  read-only.
- A positive result (a practical, net-beneficial `LPHASE` reduction
  found) would motivate, not replace, the SPICE cross-check and the
  Mihai-data request already recommended in
  `CONSOLIDATED_FINDINGS_A49_A52_2026-09-19.md`.
