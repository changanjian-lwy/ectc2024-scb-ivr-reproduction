# A62 - load sweep at fixed 250 W-tuned dead times (BOUNDARY)

Track: A. Classification: `SENSITIVITY_ONLY`, an operating-point extension
of A59. Not a P24/P25 reproduction. Part of the user's 2026-09-28
direction to finish all self-doable work before asking the advisor.

## 0. Why this experiment exists

A56-A59 compare the two designs only at the 250 W rated point. A real
converter spends most of its time below rated load, and the two designs
behave differently there:

- The large-ripple design keeps its ~300 A peak-to-peak ripple at any load,
  so its circulating conduction loss barely falls as load falls.
- The baseline's ripple is smaller. As load falls its valley current goes
  negative, so it approaches natural ZVS at light load.
- Both designs keep dead times that were fixed at 250 W. The low-side
  transition is driven by the valley/peak current, so it slows or speeds up
  with load, and the tuned `d_fall` is no longer matched.

## 1. Declared boundary

- Model: A59's reference model, unchanged. That is: nonlinear EPC2067
  `Coss(V)`, per-device Ron 1.55 mOhm (the typical device at Tj ~ 60 C per
  A60's Fig. 9), asymmetric fixed dead times, first-order Fig. 8 pricing.
- Dead times: each design keeps its A59-tuned `(d_rise, d_fall)` at every
  load. A fixed-timing driver does not retune with load; that is the
  realistic case tested here.
- Load: `Vout` is regulated to 1 V by `Ton_cmd` at output power
  `P in {250, 200, 150, 100, 50, 25}` W. The load resistance is `1 V^2 / P`
  (`module_power_w = P`). This is the only boundary change per point.
- Regulation, the current screen, accounting and continuation are A58's.
  Points run from 250 W downward, each seeded by the previous one.

## 2. Outputs

For both designs at each load: `P_A`, `P_B` (Fig. 8, 25 C), efficiency
`P/(P + P_B)` (partial-loss proxy), ZVS verdicts, residual voltages,
residual reverse times, `Ton_cmd` and peak current. Also the load at which
the large-ripple design stops being the lower-loss design, if it does.

## 3. Provenance

| Value | Source | Category |
|---|---|---|
| Load points, fixed dead times across load | This document | `PROJECT_DECISION` |
| Everything else | A59 (and A58/A57) | inherited |

## 4. What the result can and cannot decide

Decides: under fixed dead times tuned at 250 W, whether the large-ripple
design's advantage holds across load, and where it reverses.

Cannot decide: load-adaptive dead-time or frequency control, phase
shedding, light-load modes (burst/DCM), magnetic loss, hardware
efficiency, or paper reproduction. P24 reports its efficiency curve, but
this proxy is not comparable to it.

## 5. Constraints

Do not modify `src/scb_ivr/`, `results/`, `paper_locked/`, or any A37-A61
file. Never overwrite a result JSON. Retain failed points.
