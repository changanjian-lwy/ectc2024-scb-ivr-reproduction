# A180 - LSCB capacitor ladder on the P24 module, open-loop power stage (RESULTS)
Boundary: e31c56e (analysis script 1be3e99; switch-current sign fix fb90e25, act* rows rerun after it). Records:
release records-a180 (runs/*.json, logs); a180_summary.json; figure a180_up1.png. Plant: open-loop LTspice power stage
(lscb_ladder.netlist), not the cosim plant - no controller, no valley timing, no package loop, no gate edges.

## 0. Verdict (2 of 6 as registered: 3 and 6 pass)
- The ladder works only as LSCB itself runs it in a transient - a switched clamp - and only if C_DC >> Cs. On +4.8 V
  in 1 us, rail 1 rises +4.64 V on P24 as is, +2.96 / +2.17 / +1.68 V with the switched clamp at C_DC 6 / 20 / 60 uF
  (Cs 6 uF); phase 1's peak 243 -> 194 / 161 / 152 A. The charge-sharing network predicted 2.97 / 2.08 / 1.57 V.
- LSCB's passive state (0.7 V body diode) does not transfer to GaN low sides: the diode takes the HS-off dead-time
  current (GaN reverse drop 2.09 V), pumping Cs - phase-average spread 11.3 % vs 1.6 %, clamp 0.44 W - and gives
  little on the step (+3.43 V, 200 A). A 3.0 V clamp stays quiet but gives nothing (+4.27 V, 228 A).
- The switched clamp must be off in steady state: closed in every LS on-interval it ties the ladder into the power
  flow, 4.59 W at 250 W (about 1.8 points), rails pulled to 11.95-12.05 V.
- Falling -4.8 V / 1 us: rail 1 -4.44 V as is, -2.44 V switched at 20 uF (criterion 4's 50 % bound missed by 0.22 V);
  the worst phase (4) 198 -> 150 A.
- 5 us ramps: P24 alone already recovers part of the step (+2.83 V, 209 A - close to A124's closed-loop 210 A);
  switched clamp +2.03 V / 161 A at 20 uF, +1.64 V / 149 A at 60 uF.
- Open-loop start-up (0 -> 48 V in 137 us): no variant changes the peaks (166-169 A) or the end rails (0.54-0.59 V
  from 12 V); the switched clamp during the ramp costs 5.6 W.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | d07_c20 up1 rail1_exc <= 0.5 x base (2.32 V) | FAIL 3.43 V |
| 2 | d07_c20 spread <= 3.60 % and clamp loss <= 0.5 W | FAIL 11.26 % (loss 0.437 W) |
| 3 | act_c20 up1 rail1_exc <= 2.32 V and peak <= 222.6 A | PASS 2.17 V, 161.2 A |
| 4 | act_c20 dn1 rail1_exc magnitude <= 2.22 V | FAIL 2.44 V |
| 5 | actall_c20 clamp loss <= 0.5 W and spread <= 3.60 % | FAIL 4.59 W (spread 1.95 %) |
| 6 | act c06 > c20 > c60 and c60 <= 1.86 V | PASS 2.96 > 2.17 > 1.68 V |
Predictions: base up1 / dn1 and the network inside their bands; act within +0.11 V of the network; d07 spread >= 5 %
and step 2.6-3.6 V right, but its predicted 1.0-1.4 V Cs offset was wrong (the SCB balance holds the rails within
0.11 V; the pumping shows as current imbalance) and its loss 0.44 W was below the predicted >= 0.5 W; base up5 2.83 V
below the predicted 3.5-4.8 V (the SCB rebalances within 5 us).

## 2. Decision
The registered rule has no branch for "3 and 6 pass, 5 fails": its first branch needed 5 as well. Read literally,
step 2 (closed-loop cosim) is not authorised by A180. What the runs show: a windowed switched clamp with C_DC >= 20 uF
(4 x 20 uF at 12 V per module, 4.4x the flying capacitance) is the only form that helps; it needs a disturbance
trigger, which here was ideal (the window opened at the step). Step 2 is left as an open decision (README).

## 3. Limits
- Open loop with ideal feed-forward: no valley timing, so the ZVS margin and late fires (P24's binding problems)
  are not seen; peaks are those of an idealised stage (0.1 mOhm switches, linear Coss).
- The window opens exactly at the step; a real detector adds delay, and the clamp's own switch, driver and its
  floating supply are not modelled beyond a 5 mOhm switch.
- One module; no package parasitics in the clamp path (a clamp loop inductance would slow the clamp current).
