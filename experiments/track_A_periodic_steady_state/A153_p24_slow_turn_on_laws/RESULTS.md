# A153 - D68's slow-turn-on laws tested where no run has been (RESULTS)
Boundary: c3b454b. Records: release records-a153 (7 runs). Outputs: a153_summary.json (a153_analyze.py), a153_predictions.json.

## 0. Verdict
- **PASS 5/5. D68's two laws hold at turn-on rates and loop inductances never run before.** The package drive spec is
  now a pair of formulas: start-up ton_S(d) = 35.5 + K (d^-1/2 - 72^-1/2), and L * di/dt_on <= 3.2 V for <= 40 V.
- **Overshoot (x = L * di/dt_on):** 75 pH x 40 A/ns 39.8 V (predicted 39.2), 125 pH x 24 39.1 V (39.2), both x 3.0 V;
  125 pH x 32 42.5 V (42.5, x 4.0: over 40 V as predicted); 75 pH x 24 37.0 V (36.8, x 1.8). Errors -0.1..+0.6 V.
- **Start-up with D68's ton_S:** peaks 152-155 A at 75 / 125 pH; Vo before the handover within 0.004 V of the 72 A/ns
  value (1.0101-1.0148 V).
- **Start-up law at 100 pH, ton 35.5:** Vo 0.9708 / 0.9376 / 0.8762 at 24 / 12 / 6 A/ns, inside D68's band; D68 is
  closer than A152's 36 A / d rule at 24 and 6 A/ns (errors 0.007 / 0.012 against 0.017 / 0.016 V). The lost on-time is
  1.60 / 2.78 / 4.94 ns against 72 A/ns: K = 16.9 on the six 100 pH points (residuals <= 0.15 ns); the pooled K 15.6
  under-reads 100 pH by 0.1-0.4 ns.
- **Controller unchanged:** 0 NEW oracle events, 0 late fires, post-step peaks 172-175 A, Vo inside 1 % throughout the
  line step (7-9 mV, as A152's S50 / S100).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | start-up Vo in D68's band +-0.005 V; D68 closer than A152's rule at 24 / 6 A/ns | PASS (u24 inside by 0.3 mV of the widened band) |
| 2 | max V_DS within +-1.0 V of the x-curve, 4 rows | PASS (-0.1..+0.6 V) |
| 3 | 40 V side as predicted, 4 rows | PASS (39.8 / 39.1 / 37.0 <= 40; 42.5 > 40) |
| 4 | start-up peak <= 165 A, handover Vo within +-0.015 V | PASS (152-155 A; 0.002-0.004 V) |
| 5 | COMPLETED, post-step <= 190 A, 0 NEW | PASS |

## 2. Limits
- One row (+4.8 V / 1 us) per point, nominal L and Cs, Q 7, 25 °C; the x-rule is calibrated and tested to 150 pH only
  (above, the turn-off ring binds: A154).
- The start-up law's K depends a little on L (14.6-16.9); a margin of ~0.3 ns in ton_S covers it, and over-compensation
  is the safe side (A152).
