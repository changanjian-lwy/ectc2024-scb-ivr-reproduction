# A132 - negative-current target self-tuning (BOUNDARY)
Track A, main line (2.5 MHz design, A124 + A129's gated feed-forward). Written and committed before the cosim runs.
Looked at beforehand: step 1 (`a132_predict.py`: D57 + D62 + D63, below) and six 500 µs n0 pilots (tmp/, fixed target at
c0.7_l1.3, c1.0_l1.3, c0.7_l1.0, c1.3_l0.7; loop on at c0.7_l1.3, c1.3_l0.7).
Decision it changes: whether the depth loop (cfg "dep") joins the adopted design, so that the ZVS margin and the
turn-on V_DS stop depending on L and C_node. Cheaper check done first: D57 / D63 over L x C_node ±30% (25 / 9 corners).
Budget: 64 runs + 2 identity reruns, ~1 h at --jobs 6.

## 1. What and why
- i_tgt 15.625 A was set by D57 for EPC2067 + 2.933 nH. D57's node scales with s = √(k_C / k_L) (checked to 0.011 A):
  I_th = 23.57 s A, V_on(i) = V_on0(i / s). The fixed target over ±30% (s 0.73-1.36): margin ≥ 1.67 A (c0.7_l1.3;
  phase 4 −0.10 A, phase 1 −0.27 A at 43.2 V: the valley disappears, T12) and V_on 5.8 V, −0.43 points at c1.3_l0.7.
  A constant V_on (depth s · 15.625 A) keeps margin ≥ 5.83 A (2.77 A at 40 V), ≤ 0.06 points from each corner's best.
  D63 (no feed-forward): fixed c0.7_l1.3 crosses 6.2 A for 721 periods after −8 V; the loop's targets bring every
  corner back to the nominal ≤ 2.1 A x ≤ 26; cost +7 A peak at c1.3_l0.7 (186 → 193 A, slow rows).
- Method (RTL `scb_dep.v` in scb_ctrl, bridge, plant): a V_DS comparator at phase 1's predictive turn-on (V_DS > 3.9 V,
  the nominal cosim value 3.90 ± 0.05 V); windows of 32 reports; majority -> ±step (Dong 2022 / A100 variable step, ≤ 4
  codes), code 0.25 A (trim LSB), range −24..+28; a window with |Vo error| > 4 ADC codes is discarded (transients do
  not move the depth). The target moves every use of i_target (comparator, floor = target − 2 A, crossing, residual).
  Plant: cfg circuit "coss_scale" multiplies the datasheet Coss(V) (c_high / c_low alike); absent = unchanged.
- Corners: nom, c0.7_l1.3 (worst margin), c1.3_l0.7 (worst V_on). Arms: off (fixed) on the 8 step rows (nominal off =
  A129's records), on on the 16 rows (A124's 7 step rows + n0, standard matrix m1n m1p m3n m3p j30 j100 s_m25 s_p25).
- Pilot finding (not this experiment's question, recorded): **L +30% alone breaks the start-up** - mode S's timing hands
  over a ladder of 16.8 / 10.4 / 10.4 / 10.4 V; phases 2-4 sit at −42 A valleys, V_DS −2 V, up to 80 late fires, ~600 µs
  to relax; C −30% alone does not. c0.7_l1.3's steps and ends therefore move 800 µs later (steps at 1600 µs).
- Not tested: multi-module final design (Track C follow-up if adopted); Coss shape changes (uniform scale only;
  Costinett 2015: the threshold sees the energy-equivalent C); temperature; corners between the two extremes.

## 2. Criteria
1. Identity: A129's g125_l_p48_1us and g125_n0 rerun with this code: sections, turn-ons, low-offs, high-offs identical.
   Unit tests 70/70 (done before the boundary).
2. Convergence (n0, on, mean over the last 200 µs): dep within ±2 codes of s · 15.625 A: nom 0, c1.3_l0.7 +22.7,
   c0.7_l1.3 −16.6; phase 1's HS turn-on V_DS 3.9 ± 0.3 V.
3. Valley kept (n0, on, last 200 µs): every phase's mean HS turn-on V_DS ≥ 0.5 V at every corner.
4. Standard matrix (on, 3 corners; A129's criterion 5): no overlap or runaway; peak ≤ 200 A; LS turn-on V_DS ≤ 0 in the m
   rows; per phase HS turn-on V_DS within ±0.5 V of the corner's n0; j30 turn-off sd ≤ 0.5 A per phase; ±25 A back
   within 1% in ≤ 60 µs.
5. Step rows (on, 3 corners): no overlap or runaway; peak ≤ 200 A.
6. Inert at nominal (on vs A129's g125, 16 rows): peak ±3 A; load rows' Vo extreme ±3 mV; per phase HS turn-on V_DS
   ±0.2 V; dep within ±2 codes throughout mode P.
7. Efficiency (n0, last 200 µs, A115's measurement + D62 middle with Coss x k_C): on ≥ off − 0.05 points at both
   corners, and on − off ≥ +0.2 points at c1.3_l0.7.

## 3. Predictions (not criteria)
| corner | arm | depth A (code) | V_on ph1 / ph4 V | margin ph1 / ph4 A | eff % | steady peak A |
|---|---|---|---|---|---|---|
| nom | both | 15.6 (0) | 3.86 / 2.94 | 7.95 / 5.54 | 90.43 (A124 measured 90.61) | 144 |
| c0.7_l1.3 | off | 15.6 | 1.13 / −0.07 (crossing) | 1.67 / −0.10 | 90.96 | 143 |
| c0.7_l1.3 | on | 11.5 (−16.6) | 3.86 / 2.94 | 5.83 / 4.06 | 91.01 | 139 |
| c1.3_l0.7 | off | 15.6 | 5.81 / 5.07 (pilot 5.8 / 5.5) | 16.5 / 13.2 | 89.14 | 145 |
| c1.3_l0.7 | on | 21.3 (+22.7; pilot 22-23) | 3.86 / 2.94 (pilot 3.9 / 3.3) | 10.8 / 7.6 | 89.51 | 151 |
Transients (D63 without feed-forward, slow rows): on − off peak c1.3_l0.7 +7 A, c0.7_l1.3 0 A; c0.7_l1.3 off: phase 1
crossing after −8 V persists (40 V steady), on: none beyond ~2 A. Nominal step-row peaks: A129's (worst 181.5 A).

## 4. Decision rule
- 1-7 pass: dep (von_set 3.9 V, wsh 5, smax 4, ehold 4) joins the adopted design; next: the multi-module final design.
- 6 fails (not inert at nominal): one amendment of wsh / ehold, else dropped.
- 4 / 5 fail on a row where the off arm fails too: a design limit at that corner, not the loop's; recorded.
- 7 fails: adoption rests on the margin (2-3) alone. The L +30% start-up goes to the scorecard as an open item either way.
