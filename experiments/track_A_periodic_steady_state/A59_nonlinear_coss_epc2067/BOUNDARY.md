# A59 - nonlinear EPC2067 Coss(V) in the four-phase periodic solver, with A58's dead-time tuning redone (BOUNDARY)

Track: A. Classification: `SENSITIVITY_ONLY` device-model extension of
A58, with one new `EXTERNAL_DEVICE_DATA` input. Not a P24/P25
reproduction. Per user direction 2026-09-28: first finish everything that
public data and our own modeling can do, and only then ask the advisor.
Nonlinear Coss is item 2 of `results/MINIMUM_INFORMATION_REQUEST.md`, and
the EPC2067 datasheet publishes it.

## 0. Why this experiment exists

A56-A58 model each switch's output capacitance as a constant `Co(tr)` =
1860 pF per device (0-20 V). Each switch here blocks ~12 V, which is
exactly where EPC2067's `Coss(V)` falls steeply (Fig. 5a: ~2460 pF at 0 V,
~2000 pF at 10 V, ~1063 pF at 20 V). Over 0-12 V the equivalent
capacitances are larger: 2210 pF charge-equivalent (+18.8%) and 2108 pF
energy-equivalent (+13%). The model therefore understates both the charge
ZVS must move and the energy a hard turn-on dumps. A58's near-ZVS optimum
sits at 0.7-1.7 V residuals, where `Coss` is largest, so both designs and
their tuned dead times must be redone with the real curve.

## 1. The device data (`EXTERNAL_DEVICE_DATA`)

- EPC2067 datasheet, revision of 2021-10-21, SHA-256 recorded by
  `digitize_epc2067_coss.py`. Fig. 5a (`Coss`, linear scale) and Fig. 6
  (`Qoss`, `Eoss`) are digitized from the PDF vector paths.
- **Primary model**: per-device `C(V)` is the monotone PCHIP interpolant
  of the Fig. 5a points, and `q(V)` is its exact antiderivative. For
  `V < 0` it is extended evenly (`C` even, `q` odd), as in A47; above 40 V
  it is held constant. The negative-voltage continuation is a
  `NUMERICAL_IDEALIZATION`.
- Cross-check against the printed typical values (all within 1%): Q(20 V)
  37.28 vs 37 nC; Co(tr) 1864 vs 1860 pF; Co(er) 1598 vs 1597 pF;
  Coss(20 V) 1063 vs 1071 pF. Fig. 6 read directly gives Q(20 V) 37.75 nC
  and Co(er) 1599 pF.
- Found while reading the table: `src/scb_ivr/device_library.py` and
  `paper_locked/04_component_models/EPC2067_typical_params.lib` record
  `Coss = 1607 pF` and `Qoss = 56 nC` as typical. Those are the datasheet's
  MAX column; the typical values are 1071 pF and 37 nC. No computation
  uses them (every active path uses `CapacitanceView.TIME_EQUIVALENT` =
  1860 pF, which is correct). They are reported here, and not edited
  (outside this experiment's write scope).
- Population is unchanged: `NHS = 2`, `NLS = 3` devices per switch. Parallel
  same-voltage devices sum exactly, so `q_branch = n * q_dev`.

## 2. Solver extension (no edits to A50-A58 files)

A50's `_candidate_step` (backward Euler on the descriptor `E dz/dt + A z = r`)
is replaced, only for a new boundary subclass, by a **charge-based**
backward-Euler step. The linear descriptor is assembled as before, with the
constant switch capacitance. The residual then gains, for every switch
branch `b` with incidence vector `B_b`:

    B_b * ( n_b*[q(v_b(z1)) - q(v_b(z0))] - C_lin_b*[v_b(z1) - v_b(z0)] ) / h

It is solved by Newton (Jacobian adds `B_b B_b^T (n_b C(v_b) - C_lin_b)/h`).
The step is charge-conserving by construction. It is installed by object
identity in every holding namespace, as in A58, on top of A55's asymmetric-Ron
and A58's asymmetric-schedule contexts. Tests must prove:

1. With `q(V) = Co(tr) * V` (linear), the stepper reproduces the linear
   period map to relative 1e-10. The first draft said 1e-12. A smoke test
   before any run measured 5.8e-12: rounding accumulated over ~5000 steps
   by the Newton correction, which is exactly zero only in exact
   arithmetic. The threshold was relaxed to 1e-10 for that reason, before
   any result was produced.
2. The Newton step converges on every step of a nonlinear period map (the
   iteration count is recorded; failure raises).
3. The swap is complete (every holder found by identity) and restored.

## 3. Runs

Designs, dynamics, regulation (250 W by `Ton_cmd`, 4 mOhm, `1e-3`), the
current screen, `P_A`/`P_B` accounting (A57/A58 contract, Fig. 8 25 C primary)
and the anchor/continuation discipline are all A58's. The only change is the
capacitor model.

1. **Anchors**: symmetric 2.15/2.15 ns for both designs, seeded from A58's
   linear anchors. Report natural transition times, ZVS verdicts and
   `Ton_cmd` against the linear model.
2. **Re-tuned grids**, declared relative to each nonlinear anchor's measured
   natural transition times: `t_f` (low-side edge) and `t_r` (high-side
   edge), taken as the maximum over phases 1-3 and rounded to 0.05 ns.
   - ZVS design: `d_fall` in `t_f + {+0.4, +0.2, +0.1, 0, -0.1, -0.2, -0.3}`;
     `d_rise` in `t_r + {+0.15, 0, -0.15, -0.3}`, or {2.15, 1.9, 1.6} if the
     high side has no natural admission at the anchor.
   - Baseline: `d_fall` in `t_f + {+0.4, +0.2, +0.1, 0, -0.1, -0.2, -0.3}`;
     `d_rise` in {2.15, 1.0}.
   All `d > 0`. The continuation order is A58's: `d_rise` first at the anchor
   `d_fall`, then `d_fall` lines. One outward extension step is allowed if an
   optimum lands on a grid edge, and it must be reported as an extension.
3. **Step ladder** (62.5 / 31.25 / 15.625 ps) at both tuned optima, plus a
   Richardson-extrapolated source-side `P_in - P_load` check. The energy
   identity's stored-energy term (quadratic in `E`) is not valid for
   nonlinear capacitors and is not used; `P_in - P_load` over a closed
   periodic orbit needs no stored energy.

## 4. Provenance

| Value | Source | Category |
|---|---|---|
| `Coss(V)`, `Qoss(V)`, `Eoss(V)` curves; printed typ values | EPC2067 datasheet Fig. 5a/6, table | `EXTERNAL_DEVICE_DATA` |
| PCHIP interpolation, even `V<0` continuation, constant above 40 V | This document | `NUMERICAL_IDEALIZATION` |
| Charge-based BE + Newton stepper | This document | `NUMERICAL_IDEALIZATION` |
| Everything else | A58 | inherited |

## 5. What the result can and cannot decide

Decides: with the datasheet's nonlinear `Coss(V)`, whether the tuned
large-ripple design still beats the tuned baseline at 250 W; the size of
the difference; and how the ZVS verdicts, transition times and tuned dead
times move relative to A58.

Outcomes, all valid: the advantage survives (report its size); it shrinks
or reverses (report which term moved); or the ZVS design loses high-side
ZVS at 0.6274 nH. In that last case an inductance re-search is the next
self-doable step, not part of this experiment.

Cannot decide: device-to-device `Coss` spread, temperature dependence of
`Coss`, magnetic, gate-drive, thermal or package loss, other loads, or
paper reproduction.

## 6. Constraints

Do not modify `src/scb_ivr/`, `results/`, `paper_locked/`, or any A37-A58
file. Never overwrite a result JSON. Retain failed points. Do not commit
another session's uncommitted files.
