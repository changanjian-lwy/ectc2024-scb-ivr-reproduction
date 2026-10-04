# A135 - a relative phase-1 cap that cannot lock the ladder (BOUNDARY)
Track A, single module, the adopted 2.5 MHz design (A129's g125). Written and committed before the runs. Looked at
beforehand: A134's records (BOUNDARY Section 1 there) and D63 screens of cap forms (summarised below).
Decision it changes: whether scb_vff's absolute phase-1 cap (A128) is replaced by the relative one, and the L tolerance
quoted for the design. Cheaper check done first: D63 (a135_predict.py). Budget: 91 runs + 2 identity, ~50 min at 10 jobs.

## 1. What and why
- A134: the absolute cap k / rail (k = L0 x 180 A) is a ripple limit fixed at L0. When the steady Ton a load needs
  crosses it (s_p62 at L x >= 1.05 in D63, x 1.2 in cosim; n0 at x 1.3), the SCB ladder locks: phase 1 at the cap,
  rail 1 16.5 V, the slotted phases saturate the loop, Vo -90 mV. With k = 0 or k x L/L0 there is no lock.
- Why not those: no cap (z) brings back 211-219 A on the rising rows; k x L needs the part's L and has an asymmetric
  window (D63: under-estimating L by ~2 % locks s_p62, over-estimating by 15 % gives 211 A); in cosim at L x 1.3 the
  calibrated cap also slows the ladder after +4.8 V / 5 us (285 A, 129 late fires, Vo back in 113 us) - but see below.
- Timing (found in A134's records): phase 1 learns its turn-off for lo_learn = 1024 comparator periods after the
  handover (144 us), so it goes timed at 662 us at L0, 712 / 762 us at L x 1.1 / 1.2 and 812-818 us at L x 1.3. A129's
  step at 800 us therefore hits L x 1.3 in the comparator phase: phase 1's valley is held at -15.6 A, its period
  stretches 653 -> 878 ns, the slotted phases integrate (rail 1 - rail k) Ton / L ~ 64 A per period into their valleys
  (-135 A) and Vo falls 60 mV; A134's L x 1.3 rising-row results (z 272 A, c 285 A) and A133's fl13 rows are of that
  phase, not of the operating mode. A135 moves every step to 1000 us.
- A rail-ratio form with no margin (Ton1 x rss / rail) blocks the ladder's rebalancing: after a rising step C1 charges
  through phase 1's extra current; holding phase 1 at its steady ripple keeps rail 1 at 17.5 V until the low-pass
  catches up, then 210 A (D63, L x 0.7).
- Method: cap = ton x ((rss x rel) >> 8) / rail, rel = 1 + mu in Q8, rss = lp20 - 3/4 lp20 - vo (the rail with Vin at
  its low-pass). In steady state rail = rss, so the cap is (1 + mu) ton: zero action by construction at any L or load.
  On a rising step phase 1 may carry (1 + mu) times its steady ripple, which is what charges C1. D63 screen of rel
  307 / 333 / 358 / 384 (mu 0.2-0.5): 333 gives the lowest worst peak over L x 0.7-1.3 (187-195 A on A124's rows).
- RTL (scb_vff, cfg vff.rel_q8 via scb_ctrl cfg_vff_rel, bridge; gen_multi regenerated): one multiplier into A128's
  divider; rel = 0 is A128's path bit for bit. Unit tests 75 (2 new: steady Vin never caps even with a binding k;
  2400 -> 2640 codes gives 92 LSB on phase 1 only).
- Rows: A124's 7 step rows + n0, A129's matrix (8), at L x 0.7 / 0.85 / 1.0 / 1.15 / 1.3 (arm r, rel 333); plus
  +8 V / 10 us (x_l_p80_10us) at L x 0.7 / 1.0 / 1.3 (r); arm f (the adopted cap) at L0 on the 7 step rows + the +8 V
  row, the reference at this timing. Steps at 1000 us, end 1400 us (m / j rows: no step, end 1200 us; n0 1400 us).
- Not tested: L spread between phases, the four-module design, Cs or Coss corners.

## 2. Criteria (end = last 200 periods; post-step peak = max high-side turn-off current at t >= 800 us)
Lock: the end's ladder deviation (A106) more than 0.5 points above the same row at L0 (A129's g125; f100 for the line
rows' end Vin), or the end's mean Vo outside 1 V +- 1 % (A134's 1 % absolute threshold sits on s_p62's own 0.94 % at
L0). Start-up peaks (t < 1000 us) are reported, not judged.
1. Identity: rel-off reruns of g125_n0 and g125_l_p48_1us bit-identical to A129's records; unit tests 75/75.
2. L0 unchanged where the cap is idle: r100's end valleys / peaks within +-0.2 A and rails within +-0.02 V of A129's
   g125 on n0, s_p62, s_m62 and the 8 matrix rows; r100's post-step peaks within 7 A of f100's on the 7 step rows.
3. No lock at any L (every row of r at L x 0.7-1.3).
4. Peaks: every A124 row's post-step peak (t >= 1000 us) <= 200 A at every L; the matrix rule (A134's: A129's with
   the peak after the start-up, here t >= 1000 us for s rows and t >= 800 us for m / j rows) at every L, with n0 at
   the same L as its reference.
5. Recovery: every step row's Vo back within 1 % (finite), late fires <= 100, no overlap.
6. Reported, no pass / fail: +8 V / 10 us peaks (A130: 198.3 A at L0 with the adopted cap); back-in-1 % times.

## 3. Predictions (D63, a135_predictions.json; A125 band x 0.875-1.125; cosim post-step noise 2-7 A)
- r: no lock at any L; worst A124-row peak 192 / 190 / 187 / 192 / 195 A at L x 0.7 / 0.85 / 1.0 / 1.15 / 1.3 (the
  rising rows); +8 V / 10 us 218 / 199 / 190 A at L x 0.7 / 1.0 / 1.3. The cap never binds before a step or at the end.
- D63 does not model the slotted phases' valley swing A134 saw at L x 1.3 (c arm), so L x 1.3's rising rows are the
  weakest prediction.

## 4. Decision rule
- 3, 4, 5 pass at every L: the relative cap replaces the absolute one in the adopted design; L tolerance +-30 %.
- 3 passes but 4 or 5 fail at an L: the cap is still adopted if it is at least as good as the absolute cap at L0
  (criterion 2 and the rising rows within 7 A of A129's); the tolerance is the L range that passes, and the failing
  mechanism (A134's slotted-phase swing) becomes the next item.
- 3 fails: back to diagnosis.
