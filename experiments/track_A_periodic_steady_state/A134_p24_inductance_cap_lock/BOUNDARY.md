# A134 - L tolerance and the L+ ladder lock: the feed-forward's phase-1 cap (BOUNDARY)
Track A, single module, the adopted 2.5 MHz design (A129's g125). Written and committed before the runs. Looked at
beforehand: the event traces of A133's fl12_s_p62 and A129's g125_s_p62, and D63 with the RTL-exact cap (a134_predict.py).
Decision it changes: the L tolerance the design is quoted with, and whether the fix is in the feed-forward's cap (A135)
or in the slotted phases (A133's hypothesis). Cheaper check done first: D63 (below). Budget: 96 runs, ~45 min at 10 jobs.

## 1. What and why
- Trace of fl12_s_p62 (L x 1.2, +62.5 A at 800 us): after the step phase 1's Ton stays at 48.0 ns while phases 2-4
  follow the loop to its clamp, 71.0 ns (2 x ton_ns), by ~870 us. 48.0 ns = scb_vff's phase-1 cap k / rail =
  844 800 / 550 codes = 1536 LSB (A128: k = L0 x 180 A, rail estimated from Vin as Vin/4 - Vo). Then rail 1 climbs
  12.4 -> 16.5 V, rails 2-4 fall to 10.5 V, the period stretches 605 -> 861 ns, the slots of phases 2-4 come late on
  their current (valleys -30 to -48 A, turn-on with -25 to -40 A through the high-side diode), Vo 0.91 V, phase 1
  peaks 208 A (the cap assumes rail 1 = Vin/4). The diode conducts 0-1.6 ns per period and phase 4 counts 16 late
  fires: neither starts it. Nominal L (g125_s_p62): every phase settles at Ton 46.2 ns, 1.8 ns (4 %) under the cap.
- Mechanism (hypothesis): the cap is an absolute ripple limit set for L0. At L > L0 the steady Ton a load needs
  scales with L and crosses it (n0 at L x 1.3: 50.2 ns; s_p62 at L x 1.05: ~48.5 ns). A Ton limit on one phase of
  the SCB breaks the equal-charge condition, the ladder tilts toward rail 1 and the slotted phases saturate the loop:
  a locked state, not an oscillation. A133's floors cannot change it.
- D63 + the RTL-exact cap reproduces it: f (k as adopted) locks on s_p62 at every L x >= 1.05 and on all 8 rows at
  L x 1.3; z (k = 0) and c (k x L/L0) never lock. Without the cap A133's D63 saw nothing.
- Method: the arm sets vff.k only (no RTL change). T: f at L x 0.85 / 0.9 / 1.05 / 1.1 on A124's 7 step rows + n0 and
  A129's matrix (8), f at L x 0.7 on the matrix (its step rows = A133's fl07). M: z and c at L x 1.1 / 1.2 / 1.3 on
  n0, s_p62, l_p48_5us, l_p48_1us. Steps at 800 us. Reference rows: A129's g125 (nominal), A133's fl12 / fl13.
- Not tested: a fix that keeps the cap's job (A135), L spread between phases, the four-module design.

## 2. Criteria (end = last 200 periods; post-step peak = max high-side turn-off current at t >= 800 us)
Lock (a run's end state): A106's ladder deviation max |Vc_k / Vin - (N - k) / N| > 1 % in any end period, or the
end's mean Vo outside 1 V +- 1 %. Start-up peaks (t < 800 us) are reported, never judged.
1. Mechanism: no z or c run locks at L x 1.1 / 1.2 / 1.3 (12 n0 / s_p62 runs), where f locks (A133's fl12_s_p62,
   fl13_n0). Fails if any z / c n0 or s_p62 run locks.
2. f's s_p62 locks at L x 1.1 (D63: lock from 1.05).
3. Tolerance (f), per L: step rows - no overlap, no runaway (A133's rule), Vo back within 1 %, no lock, post-step
   peak <= 200 A; n0 - A133's balanced(); matrix - A129's rule with its run peak replaced by the peak at t >= 800 us
   (m / j rows: steady; s rows: the step). Functional tolerance: the L range around 1 where every row passes except
   the 200 A peak; spec tolerance: all of it. Reported with the start-up peaks separately.
4. z / c rising-line peaks: reported against 200 A (no pass / fail; they price the fix in A135).

## 3. Predictions (D63, a134_predictions.json; peak bands A125 x 0.875-1.125, cosim post-step noise 2-7 A)
- f: s_p62 lock at L x 1.05 and 1.1 (D63 peak 254 / 243 A); every other row ok at L x 0.85-1.1; L x 0.85 / 0.9 worst
  peak 211 / 202 A (rising line rows).
- z: no lock; rising-line peaks 209-215 A at every L. c: no lock; worst peak 182-195 A.
- The cosim headroom at L0 is larger (1.8 vs 0.8 ns), so L x 1.05 may not lock in cosim; L x 1.1 should.

## 4. Decision rule
- 1 passes: the phase-1 cap is the cause; A133's "limit cycle" is renamed the cap lock (scorecard T16) and A135
  designs a cap that cannot lock (calibrated k with margin, a rail-ratio form, or a cap on every phase), D63 first.
- 1 fails: the cap is not the only cause; the slotted phases' timing goes back to diagnosis.
- 3 gives the quoted L tolerance of the adopted design (scorecard, CURRENT_STATUS).
