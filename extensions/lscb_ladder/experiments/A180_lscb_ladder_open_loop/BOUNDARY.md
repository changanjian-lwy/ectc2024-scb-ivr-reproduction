# A180 - LSCB capacitor ladder on the P24 module, open-loop power stage (BOUNDARY)
Method: math (open-loop LTspice power stage; no RTL, no cosim)
Extension lscb_ladder. Written and committed before the runs. Looked at beforehand: one base steady-state smoke run
for T only (T 452 ns: Vo 1.0035 V at 48 V, rails 12.13 / 11.96 / 11.96 / 11.94 V, phase peaks 139-141 A, valleys
-8..-10 A, Pin - Pout 27.4-28.0 W, phase-average spread 1.6 %). No ladder variant was run.
Decision it changes: whether, in which form and at which C_DC the ladder clamp goes into the closed-loop cosim (step 2);
the EEK5101 video's own-test segment. Cheaper check first: charge-sharing network (a180_predict.py). Budget: 25 runs,
~30 min at 2 jobs.

## 1. What and why
- P24's rising line steps land on rail 1 (A124: 12.3 -> 16.4 V on +4.8 V / 5 us; A148). LSCB (Tong et al., VLSI 2026)
  holds each flying capacitor at its Vin/4 multiple with a C_DC ladder and switches S_DC (body diodes in steady state).
- P24 has no node between cells, so clamp k joins ladder node d(4-k) to a_k (= Vcs_k while SL_k conducts): a diode,
  anode at the ladder, or a switch closed only inside SL_k's on-intervals (plus that diode as its body).
- Risk found while building: the GaN low side reverse-conducts at 2.09 V + 2 mOhm x i (fit_fig8, 3 devices). A clamp
  of lower drop takes the HS-off dead-time current (~140 A x 4.5 ns per period) into Cs_k: charge pumping against
  the SCB's charge balance.
- Model (lscb_ladder.netlist): the cosim circuit (L 2.933 nH, R 0.54 mOhm, Cs 6 uF, Co 4.672 mF, 4 mOhm load, linear
  Coss, reverse diodes), switches 0.1 mOhm; open loop: T 452 ns, phases T/4 apart, dead time 4.5 ns, Ton 38.6 ns x
  48 / vin at each period start (ideal feed-forward) on steps, fixed on start-up.
- Variants: base; d07_c20 (diode 0.7 V / 5 mOhm, LSCB's steady state); d30_c20 (3.0 V, above the GaN LS drop);
  act_c06 / _c20 / _c60 (switch 5 mOhm in a 20 us window from the step, body 3.0 V); actall_c20 (switch in every LS
  on-interval). C_DC ESR 1 mOhm, 1 MOhm balancing resistors.
- Rows: up1 / up5 (+4.8 V over 1 / 5 us at 40 us), dn1 (-4.8 V / 1 us), end 80 us; su (0 -> 48 V over 137.22 us,
  fixed Ton, end 150 us) for base, d07_c20, d30_c20, act_c20 (window = ramp).
- Steady window 30-40 us: spread = (max - min) / mean of the four phase averages. rail1_exc = rail 1's extreme after
  the step minus its steady mean. Peak = max over phases after the step.
- Not tested: controller (valley timing, ZVS margin), package loop, gate edges, closed-loop start-up and handover,
  efficiency beyond the clamp's own loss (V_drop x I integrated).

## 2. Criteria
1. Literal transplant helps the step: d07_c20 up1 rail1_exc <= 0.5 x base.
2. Literal transplant is safe in steady state: d07_c20 spread <= base + 2 points and clamp loss <= 0.5 W.
3. Switched clamp helps the step: act_c20 up1 rail1_exc <= 0.5 x base and peak <= base - 20 A.
4. Switched clamp on the falling step: act_c20 dn1 |rail1_exc| <= 0.5 x base.
5. Always-on switch is cheap: actall_c20 clamp loss <= 0.5 W and spread <= base + 2 points.
6. Size: act up1 rail1_exc falls c06 > c20 > c60, and act_c60 <= 0.4 x base.

## 3. Predictions (not criteria)
- base: up1 rail1_exc 4.3-4.8 V, up5 3.5-4.8 V, dn1 -4.3..-4.8 V.
- Ideal-clamp network (a180_predictions.json): rail 1 +2.97 / +2.08 / +1.57 / +1.20 V at C_DC 6 / 20 / 60 uF / infinite;
  act_c06 / c20 / c60 within +0.4 V of these. So act_c20 is near 0.45 x base: criterion 3 marginal; 6 passes.
- d07_c20 pumps: steady Vcs_k 1.0-1.4 V above its ladder node, rail 1 down and rail 4 up by about that, spread >= 5 %,
  clamp loss >= 0.5 W -> criterion 2 FAILS; up1 rail1_exc 2.6-3.6 V.
- d30_c20: no steady conduction; up1 rail1_exc 4.2-4.6 V.
- Start-up: report only (no base record to set a threshold).

## 4. Decision rule
- 3, 5 and 6 pass -> step 2: the switched clamp as an opt-in cosim plant option (bit-identical off), C_DC the smallest
  size meeting 6's bound, on A124's line steps and start-up; report the ladder's area (four capacitors at 12 V).
- 3 fails but 6's c60 bound passes -> step 2 only at that C_DC, area stated first.
- 1 passes and 2 fails -> LSCB's passive state does not transfer to GaN low sides; step 2 only with a switched clamp.
- 3 and 6 fail -> the ladder does not help P24 in open loop; no cosim; the negative result is reported.
