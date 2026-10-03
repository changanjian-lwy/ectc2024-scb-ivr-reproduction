# A128 - co-simulation of the Vin feed-forward (A127 hybrid) at 2.5 MHz (BOUNDARY)

Extension `ml_design_assist`. **Written and committed with the RTL before
the runs.**

**Decision it changes:** whether the 2.5 MHz design closes its last hard
constraint (rising line steps) with a Vin sensor, or needs a bus-slew
spec; and whether the learned falling-step rule earns an RTL feature.

**Cheaper check done first:** D63 (A127; `a128_predict.py`, RTL-exact).

**Budget:** 8 co-simulation runs, ~1 h on 10 cores.

## 1. What and why

**The design:** A124's 2.5 MHz design plus `scb_vff.v`. Spec:
`SPEC_RTL.md`. Opt-in with cfg "vff"; in mode P only.
- **Vin** is sampled with Vo's ADC sample: 20 mV codes, once per period.
- **Phase 1's Ton cap** = L·180 A / rail. The rail is estimated from Vin
  (one-step prediction, 2^−6 low-pass), and the cap applies from the
  next period (a one-period lag). This is cap_vin, the decision rule of
  A127.
- **The learned falling-step rule** (A127 s1, distilled, 6 parameters):
  - scale_k = 1 + c_k · max(lp2 − Vin, 0), with c = (+64, −47, −47,
    −139) Q16 per code;
  - it moves Ton from phases 4 and 2-3 to phase 1 while Vin falls.
- **A DEVIATION from P24:** P24 has no Vin sensing, so this lives in an
  extension.

**Checks already done:**
- RTL unit tests, 59/59: the 56 existing plus 3 new.
  - vff off passes ton;
  - falling step: each phase's scale exact;
  - rising step: phase 1's cap = k·2^8 / rail exact.
- Bit-identity with vff off (criterion 0).

**Rows:** A124's seven step rows and n0, with the same configurations
plus "vff".

## 2. Criteria

0. **Identity with vff off** (before the runs):
   - `scripts/cosim_regression.py --full` passes;
   - A124's p125_l_p48_1us, rerun with the new code, has identical
     sections.
1. **+4.8 V / 5 µs: peak ≤ 200 A** (A124 210.2). This is the hard
   constraint under the ≥ 5 µs bus slew.
2. **−4.8 V / 1 µs: peak ≤ 200 A** (A124 215.9).
3. **+4.8 V / 1 µs:** the peak falls by ≥ 10 A from A124's 217.7.
4. **No harm:**
   - the load rows' peaks within ±3 A of A124 (177.7 / 143.9);
   - every step row's |Vo extreme| ≤ A124's + 3 mV;
   - no overlap, no runaway;
   - n0: efficiency within 0.05 points of 90.61%, start-up peak within
     ±2 A of 163 A, HS turn-on voltages within 0.1 V.

## 3. Predictions (D63, RTL-exact; A125's bands at 80%)

| row | D63 vff (none) | M80 band | G80 band | Vo D63 vff (none), mV |
|---|---|---|---|---|
| +4.8 V 1 µs | 186.4 (213.5) | 163-210 | 184-221 | +7.8 (+13.1) |
| +4.8 V 5 µs | 175.8 (186.7) | 154-198 | 173-208 | +5.6 (+7.1) |
| −4.8 V 1 µs | 169.0 (206.2) | 147-191 | 167-200 | +24.0 (+54.0) |
| −4.8 V 5 µs | 169.5 (168.1) | 148-191 | 167-201 | +26.3 (+33.2) |
| −8 V 10 µs | 168.0 (164.5) | 146-190 | 166-199 | +34.3 (+34.4) |
| +62.5 A | 177.1 (177.1) | 154-200 | 175-210 | −10.1 |
| −62.5 A | 144.2 (144.2) | 126-163 | 142-171 | +16.8 |

- **|Vo extreme| band:** ×0.56-1.44 of D63 (A125, post hoc).
- **This is A125's prospective test:** how many of the 7 rows land in the
  M80 and G80 bands (nominal ≥ 80%).

## 4. Decision rule

- **If criteria 1, 2 and 4 hold:**
  - the 2.5 MHz design gets the Vin feed-forward as its extension option;
  - the rising-step limit is closed for slews ≥ 5 µs;
  - the RL line (A125-A128) is finished, so the trade-off map, the
    status file and the README are updated once.
- **Otherwise:** record it; the bus-slew spec stays the answer.
