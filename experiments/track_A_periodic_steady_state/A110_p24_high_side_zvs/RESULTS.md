# A110 - high-side zero-voltage turn-on by the negative current (RESULTS)

Track A, main line. One factor: the negative-current target (5% in the
design, here 10-30% of the 125 A peak).

**Boundary:** `BOUNDARY.md`, committed (82813c8) before any run.

**Records:**
- `cosim/run_*.json`, `cfg_*.json`;
- `a110_summary.json` (`a110_analyze.py`).

**Models:**
- **Physical:**
  - Verilog RTL;
  - A88's plant (kernel2: datasheet Coss(V), reverse conduction);
  - A105's I2 with `slot_lo`;
  - 25 C, one module.
- **Mathematical:**
  - D57's free valley (high-side turn-on V_DS);
  - D58's boundary-mode relations;
  - D62's middle-case loss model, applied to each run's measured
    waveforms, its reverse conduction included.

## 0. Verdict

1. **The high side can turn on at (or near) zero voltage. D57's energy
   balance predicts it quantitatively.**

   | target | high-side turn-on, phases 1/2/3/4 | D57 | efficiency (D62 middle) | predicted |
   |---|---|---|---|---|
   | 5% (design) | 8.96 / 8.91 / 8.91 / 9.07 V | 8.96 | 87.92% | 88.16% |
   | 10% | 7.06 / 6.98 / 6.98 / 6.87 V | 7.02 | 89.10% | 89.28% |
   | 15% | 5.05 / 4.94 / 4.94 / 4.59 V | 4.98 | 89.84% | 89.97% |
   | **20%** | 2.98 / 2.86 / 2.85 / 2.26 V | 2.89 | **90.17%** | 90.26% |
   | 25% | 0.86 / 0.69 / 0.70 / **−0.16** V | 0.74 | 90.14% | 90.21% |
   | 30% | 1.16 / **−1.27 / −0.84** / 1.59 V | ≤ 0 | 89.42% | 89.91% |

   - **Efficiency:** the best is at 20%, **+2.25 points over the
     design's 5%**. The loss falls from 34.4 to 27.2 W per module.
   - **Where the gain comes from:**
     - the high side's hard turn-on: 8.9 → 0.7 W;
     - gate drive: 7.4 → 6.0 W, from the lower frequency (4.31 →
       3.52 MHz);
     - against conduction: 12.3 → 14.2 W.
   - **Zero voltage is first reached at 25%** (phase 4), as D57's 26.7%
     predicts.
2. **At 30% the controller's timing breaks down.** This was registered
   as the falsifying outcome.
   - **Peak:** 236 A, in steady state at 203.6 µs, phase 4.
   - **Hard turn-ons:** up to 15.7 V, in between the zero-voltage ones.
   - **Turn-on timing:** 1553 of 6000 turn-ons flagged early. Phase 1's
     predicted delay drifts to 2.8 ns (7.5 ns at 25%).
   - **Load steps:**
     - the −62.5 A step does not settle back within 1% before the run
       ends (`step_stats` reports inf, the review's fix at work);
     - the +62.5 A step takes 43 µs (8.4 µs at 5%).
   - **With 30 ps jitter:** the turn-off spread rises to 7-20 A sd (0.5 A
     at 5%).
   - **Cause:** the predictive turn-on is corrected against the measured
     valley of V_DS. Once the node reaches the rail, the high side's
     reverse conduction clamps V_DS near 0 and the valley is a flat
     plateau. The measurement then reports "flat" (no update), and the
     other updates push the delay off.
   - **The physics allows zero voltage at 30%. The valley measurement
     does not define a target for it.**
3. **The design's 5% is far from the loss optimum.** At 20% the high side
   still turns on at ~2.3-3.0 V, not zero voltage, but the loss is
   nearly the zero-voltage minimum and the controller is stable
   (Section 1).
   - **Candidate for the design:** 20%. Its load steps and the standard
     matrix are not yet run.

## 1. Registered criteria (BOUNDARY Section 3)

| criterion | 10% | 15% | 20% | 25% | 30% |
|---|---|---|---|---|---|
| high-side V_DS within ±0.6 V of D57 (10-25%); ≤ +0.3 V at 30% | pass | pass | **miss** (phase 4 2.26 V, 0.63 off) | **miss** (phase 4 −0.16 V, 0.90 off: it reached zero) | **miss** (1.16 / 1.59 V on phases 1/4) |
| Ton within ±4% | **miss** (−8%) | **miss** (−11%) | **miss** (−14%) | **miss** (−17%) | **miss** (−7%) |
| period within ±4% | pass | pass | pass | pass | pass |
| peaks within ±5 A of 2I + i_neg | pass | pass | pass | pass | **miss** (167-171 A, +5-9) |
| no overlap; peak ≤ 200 A | pass | pass | pass | overlap pass; **peak 204 A** (77 µs, after the handover) | overlap pass; **236 A** |
| low side ≤ 0 V; Vo ±1 mV | pass | pass | pass | pass | **low side +1.21 V**; Vo pass |
| efficiency within ±0.7 points | pass | pass | pass | pass | pass |

**Across rows:**
- efficiency maximum at 15-25%: pass (20%);
- 30% at least 1 point above 5%: pass (+1.50).

**At 30%:**
- **load steps within ±25%:**
  - +62.5 A: −15.55 mV, pass;
  - −62.5 A: **miss**, −21.84 mV against +11.30 mV, and not recovered.
- **jitter:**
  - sd **miss** (7-20 A);
  - high side ≤ 0.5 V **miss**.

**Ton's registered relation was wrong:**
- Ton = (peak − valley) L / (V_rail − Vo) ignores the current's change
  during the resonant transitions. The current rises from the turn-off
  value toward the turn-on value while the node swings.
- So the measured Ton is 7-17% shorter, while the period (registered by
  the same relations) is within 4%.
- The waveform inputs to D62 are measured, not taken from this relation,
  so the efficiencies are not affected.

## 2. What this answers, and next

**Why the module did not switch its high side at zero voltage.**
- P24's 1-2% (and the design's 5%) is far below the ~27% that the node's
  capacitance needs with Eq. (4)'s 1.47 nH (D57).
- With enough negative current the circuit does reach zero voltage, as
  predicted.

**What stops it at 30% is the turn-on timing rule, not the circuit.**

**Next, A111 (candidate):** a zero-voltage-aware turn-on measurement.
- When V_DS reaches zero (the node at the rail), report that instant as
  the target. The high side then turns on as the node arrives, with the
  least reverse conduction, instead of a "flat" no-update.
- It is a change in the controller-side measurement (the bridge's analog
  function) behind an opt-in key, with bit-identical defaults.
- Then 25-30% can be tested for a stable zero-voltage design, and 20%
  run through the standard matrix as the efficiency-optimal candidate.
