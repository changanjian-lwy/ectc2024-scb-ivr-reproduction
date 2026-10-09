# A182 - A180's switched clamp opened by a real detector (RESULTS)
Boundary: eda909c. Post hoc script: 3008c5d. Records: release records-a182 (runs/*.json, run log); a182_summary.json;
a182_posthoc_predev.json. Plant: A180's open-loop LTspice power stage of one P24 module. It is not the cosim plant:
no controller, no valley timing, no package loop, and no clamp loop inductance.

## 0. Verdict (0 of 4 as registered; the post hoc reading at 0.75 V passes 2 and 3)
- **Criterion 1 as registered.** It measured the pre-step deviation from t = 0. The .ic settling reaches 1.129 V at
  0.95 µs, so 0.75 V "false-triggers" and the registered fallback moved criteria 2-4 to 1.5 V.
  - Post hoc: in steady state (10-40 µs) max |V(d(4-k)) - Vcs_k| is 0.29 V, as predicted (0.25-0.45). So 0.75 V does
    not fire on steady ripple.
- **1.5 V threshold.** It fires 0.38 µs after the start of a +4.8 V / 1 µs step. With 0.3 µs more, rail 1 rises
  +3.33 V on up1 (bound 2.32) and -3.94 V on dn1 (bound 2.76). At 0.1 µs, up1 gives +2.35 V. So no tested delay meets
  criteria 2-3 at 1.5 V.
- **0.75 V threshold** (fires 0.14 / 0.25 µs after the step on up1 / dn1).
  - Delays 0.1 and 0.3 µs keep the ideal trigger's benefit: up1 +2.15 / +2.16 V and 161 A (ideal +2.17 V, 162 A);
    dn1 -2.43 / -2.48 V (ideal -2.46 V).
  - The price is the clamp current: late closure shares charge hard. At 0.3 µs the clamp peak is 289 A against the
    ideal's 146 A (criterion 4's bound 219 A), and the energy is +7 µJ per event.
  - At 1.0 µs the benefit is gone: up1 +4.27 V / 206 A (diode-only A180 d30: +4.27 V), dn1 -4.44 V (base -4.44). The
    clamp peak is 376 / 519 A.
- **5 µs ramps** tolerate the late trigger: every setting holds +1.97..+2.33 V (ideal +2.03).
- **C_DC 60 µF** at 0.75 V / 0.3 µs: up1 +2.16 V, the same as 20 µF. The window opens after the ladder size matters,
  so the 60 µF ideal's +1.67 V is lost.
- **Detector spec this model supports.**
  - Threshold about 0.75 V, i.e. 2.6 × the 0.29 V steady deviation.
  - Total latency (detection plus delay) within about 0.45 µs for a 1 µs line step.
  - A clamp switch rated for about 2 × the ideal-trigger current, or current-limited. The peak is resistance-limited
    here (about 6 mΩ loop, no inductance), so it is an upper bound, and a loop inductance would ring.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | pre-step max \|deviation\| < vth, both thresholds | FAIL at 0.75 V (1.129 V, .ic settling at 0.95 µs; steady 0.29 V); pass at 1.5 V |
| 2 | 1.5 V / 0.3 µs up1: rail1_exc ≤ 2.32 V and peak ≤ 222.6 A | FAIL 3.33 V (peak 178.8 A) - post hoc 0.75 V: 2.16 V, 161.4 A |
| 3 | 1.5 V / 0.3 µs dn1: \|rail1_exc\| ≤ ideal 2.46 + 0.30 V and peak ≤ 178.2 A | FAIL 3.94 V (peak 150.1 A) - post hoc 0.75 V: 2.48 V, 149.8 A |
| 4 | clamp peak ≤ 1.5 × ideal (218.7 A) | FAIL 323.8 A at 1.5 V - post hoc 0.75 V: 289.0 A, also FAIL |

Predictions:
- Right:
  - the steady deviation (0.29 V; predicted 0.25-0.45, but criterion 1 measured from t = 0);
  - t_det on up1 / dn1;
  - the ideal row (+2.17 V; predicted 1.8-2.2);
  - 0.1 µs and 1.0 µs on up1 (+2.15 / +4.27 V);
  - up5 (+2.00 V);
  - 60 µF (+2.16 V);
  - the clamp spike at 2.0-2.2 × the ideal (predicted 1.5-3 ×);
  - the extra energy, +7 µJ at 0.3 µs (predicted 5-25).
- Better than predicted: 0.75 V at 0.3 µs gave +2.16 V and 161 A, against 2.3-3.4 V and 170-215 A. Hard sharing at
  closure pulls rail 1 straight back.
- Wrong: the 1.5 V penalty was predicted at +0.2-0.6 V over 0.75 V. It is +0.20 V at 0.1 µs, +1.17 V at 0.3 µs, and
  0 V at 1.0 µs, where both have lost the benefit.

## 2. Decision
By the registered rule:
- With 2 and 3 failing at the fallback threshold, the benefit needs a trigger faster than tested at 1.5 V ("none
  tested").
- With 4 failing, the claim carries the hard-sharing caveat.

Read with the post hoc steady deviation, a 0.75 V detector with ≤ 0.3 µs delay keeps the full benefit, at about twice
the clamp current. The lscb_ladder line closes here. The closed-loop step 2 is not run (user, 2026-10-09), and a
current-limited clamp stays an open item.

## 3. Limits
- No clamp loop inductance. The spike is resistance-limited (an upper bound), and a real loop would ring at
  switch-open.
- I(SL_k) peaks (~10 kA in every run, ideal included) are sub-picosecond Coss discharges of the 0.1 mΩ ideal switch.
  They are not used.
- One step position per row, and the next LS interval is 0-0.45 µs away. The detector is ideal apart from its
  threshold and delay: no offset, noise or retriggering, and no load-step false triggers.
