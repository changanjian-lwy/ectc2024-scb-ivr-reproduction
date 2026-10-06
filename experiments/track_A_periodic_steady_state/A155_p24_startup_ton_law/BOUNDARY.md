# A155 - the start-up ton law with loop and turn-off terms, tested to 300 pH (BOUNDARY)
Method: mixed (math: a least-squares law on 27 package runs; RTL cosim cfg only, frozen design)
Track A, package layer. Written and committed before the runs, after A153 / A154's results (their records are in the fit).
Decision it changes: whether the start-up part of the package spec is a formula valid to 300 pH (A154: D68's ton,
which has no L term, let the handover Vo fall to 0.984-1.000 V and the start-up peak rise to 166-190 A).
Cheaper check done first: the fit itself (a155_fit.py, leave-one-out over the 27 runs). Budget: 5 start-up runs of
300 us, ~15 min.

## 1. What and why
- Mode S is open loop (fixed 400 ns period), so the Vo it reaches before the handover is set by the effective on-time.
  The fit over every package run (A145, A151-A154; L 50-300 pH, turn-on 6-72, turn-off 24-72 A/ns, ton 35.5-39.5):
  Vo = c0 + s (ton - 35.5) - a d_on^-1/2 - b L + c d_off^-1/2, with s 0.0283 V/ns (= A152's calibration, fitted
  independently), K = a / s 15.8 ns (A/ns)^1/2 (= D68's 15.6), L term 6.0 ns per nH (new: the loop delays the
  on-time), turn-off term 9.8 ns (A/ns)^1/2 (a slower turn-off keeps the node up longer). rms 3.3 mV, leave-one-out
  4.4 mV, max 10 mV.
- ton_S for V_T = 1.015 V (start-up peaks ~150 A in A152 / A153) at combinations never run:
  s175 (175 pH, on 18, off 56 A/ns) 37.793 ns; s200 (200, 16, 50) 38.092; s250 (250, 12.8, 36) 38.611;
  s300 (300, 10, 30) 39.334. Control c300: s300 with D68's ton 38.595 ns (no L / turn-off term).
- Base: A151's on18_l100_n0 cfg, t_end 300 us. Not tested: line or load steps at these points (A154 covers the
  turn-off side at similar x), corners.

## 2. Criteria
1. Vo(section nearest 143.5 us) within 1.015 +- 0.010 V on s175 / s200 / s250 / s300.
2. Start-up peak (high-side turn-off current, t < 300 us) <= 165 A on the same four.
3. c300's Vo within +-0.010 V of its prediction (0.994) and below 1.005 V: the L / turn-off terms are needed.
4. Start-up V_DS (vds_win, t < 300 us) <= 40 V on all five (x_on 3.0-3.2 V, x_off 9-10 V).

## 3. Predictions (a155_predictions.json)
Vo 1.015 on the four law rows, 0.994 on c300; start-up peaks ~150-160 A on the four, higher on c300.

## 4. Decision rule
- 1-3 pass: the start-up ton formula with L and turn-off terms replaces D68's in the spec (D68 Section 7).
- 1 or 2 fails: keep D68's term plus a margin, and report the residual against L.
