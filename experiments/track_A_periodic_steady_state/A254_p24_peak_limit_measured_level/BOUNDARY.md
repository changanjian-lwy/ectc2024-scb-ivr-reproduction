# A254 - the peak current limit at a level set from A253's measured overshoot (BOUNDARY)
Method: cosim. Bridge option "ocp" with A253's second fix (f4657c3): a stale turn-off is dropped before the
plant steps, so a run where the limit never acts is its reference bit for bit. Tests 721, regression quick + full
PASS. Track A. Written and committed before the runs.
Looked at beforehand:
- A253 (RESULTS 0): at 130 A on 2.2 nH, the current rose 49-69 A in the 11 ns path, and the gate's turn-off added
  8-14 A. N75 1 MHz reached 212.1 A, S75h 1 MHz 199.1 A.
- A253's rule: "o2 fails with fires: measure the overshoot, then re-register the level". This is that re-registration.

Decision it changes: whether the final configuration adds the limit, which would close item 10 at 1 MHz (and item
2's S75h 125 C re-application rows, if those come under 200 A too).
Cheaper check first: a254_screen.py on the 70 reference records. A linear current ramp over-counts fires (calibrated
on A253: it marks every row that fired). Budget: 35 runs at 10 jobs, about 5 h; the 2 four-module rows run first.

## 1. What and why
- Level(L) = 200 - 5 (margin) - 14 (gate) - 69 x 2.2 / L, down to 5 A: 110 A on 2.2 nH, 125 A on 2.933 nH,
  140 A on 3.813 nH. t_ns 1.0 (+ t_drv 10 ns).
- On 2.933 / 3.813 nH the overshoot is scaled by L, not measured: no row there reached A253's levels.
- The screen at 8 ns marks 33 of 70 rows:
  - 22 on 2.2 nH: every S75h / S75 row, including the item-2 rows and two start-ups; N75 at 60 kHz and 1 MHz; and
    N75's item-3 rows;
  - 11 on 2.933 nH: 9 N0 rows and the 2 four-module rows.
  - At 11 ns it puts no fire in steady state (S75h / N75 / N0, 200-300 us) at any of these levels.
  - On the S75h boards it marks the start-up's handover: about 69 pulses of 150-169 A in mode P's first 20 us. A
    limit that acts there changes every S75h row, so all of them run.
- Two identity rows that the screen leaves out, although their current crosses the level in every full-load period:
  p_N75_100k (2.2 nH, peaks 137-141 A) and p_N0_100k (2.933 nH).
- The other 35 rows are equal to their references by construction (no fire, no step split).
- Not tested: the overshoot on 2.933 / 3.813 nH; faster limit paths; four modules beyond the two rows.

## 2. Criteria
- p0: tests 721, cosim_regression quick + full PASS (logs tmp/logs/a253_fix2_*.log).
- p1: identity rows equal to the reference, no fires. Every other row without a fire equals its reference.
- p2: p_N75_1000k and p_S75h_1000k meet A240's q1 and q2 (whole-run peak <= 200 A, V_DS, time above).
- p3: stage-2 rows meet A253's o3: whole-run peak <= 200 A, NEW <= the reference's, post-event peak <= max(reference,
  200 A) + 2 A, |Vo extreme| <= the reference's + 2 mV. Skip rows: the valley range within 1 A.
- p4: stage-1 and position rows:
  - peak after 300 us <= max(reference, 200 A) + 2 A;
  - Vo minimum >= the reference's - 1 mV (- 2 mV on 1 MHz);
  - every q2 / q3 / q5 that passes in the reference passes.
- p5: start-ups: A245's g1-g3 hold where the reference holds them, peak <= reference + 2 A, end deviation <=
  reference + 0.2 V.

## 3. Predictions (not criteria)
- p2 passes: N75 1 MHz about 190-198 A (110 + 69 + 14 = 193 A at the worst measured rise).
- The limit fires in every S75h row's handover (20-70 times), on the trains at 1 MHz and on k_S75h. The N0 rows fire
  rarely or never; the four-module rows do not fire.
- Vo minima move by less than 1 mV outside 1 MHz.
- a_S75h_d2 / d20 come under 200 A, closing item 2's residual.
- Risk: truncated pulses in the handover leave the series capacitors short of charge (Abdelhamid 2020), which shows in
  the start-up ladder (p5) or the handover's Vo.

## 4. Decision rule
- **p0 or p1 fails:** wiring; trace it.
- **p2-p5 pass:** the user decides adoption (AskUserQuestion). Item 10 closes at 1 MHz; item 2 too if a_S75h_d2 / d20
  pass p3.
- **p2 fails with fires:** no fixed level reaches 200 A within the 11 ns path. Stop the level search; the open options
  are a faster limit path (no source gives its delay) or a short delay during trains (A252); report to the user.
- **p3-p5 fail:** name each row's cost; the user decides.
