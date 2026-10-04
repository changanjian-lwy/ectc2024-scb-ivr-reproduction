# A136 - the relative phase-1 cap on Ton's low-pass (BOUNDARY)
Track A, single module, the adopted 2.5 MHz design (A129's g125). Written and committed before the runs. Looked at
beforehand: A135's records (all of them; RESULTS there) and D63 screens of the low-pass variant (below).
Decision it changes: whether a relative cap replaces A128's absolute one after A135's failed at L0, and the L tolerance.
Cheaper check done first: D63 (a136_predict.py) - it ranks, but under-predicted A135's rising rows by 16-17 A.
Budget: stage 1 15 runs (~10 min); stage 2 76 runs (~45 min) only if stage 1 passes; 1 identity rerun.

## 1. What and why
- A135 (rel 333 on the loop's ton): no lock at any L and the L x 1.3 transients of A134 are gone with the step at
  1000 us, but the rising rows are worse than the absolute cap: L0 +4.8 V / 1 us 203.1 A vs 183.0 A (f100). Trace:
  after ~5 us the slotted phases' valleys deepen, Vo dips 6-10 mV and the loop raises ton (37.8 -> 41.6 ns); the
  relative cap scales with that ton, and with rss / rail ~ 0.73 its margin 1.3 leaves phase 1 almost free (37.8 ns
  while the absolute cap held it at 34-36 ns), so phase 1's peak plus its positive valley (+28 A) reaches 203 A.
- Fix: the cap's numerator takes ton's low-pass tlp (Q8, tlp += (ton - tlp) >> sh20, the time constant of lp20), so
  the loop's transient rise does not move the cap; mu 0.25 (rel 320). At L0 and nominal load 1.25 x tlp x rss =
  1.25 x 1210 LSB x 555 codes = 839 k, within 1 % of A128's k = 844 800: the same cap as adopted. At other L and loads
  it scales with tlp (Ton ~ L), so it is A134's calibrated cap (arm c) calibrated by the loop itself. In steady state
  tlp = ton and the cap is 1.25 ton: zero action by construction, no lock. A +62.5 A step raises ton by ~22 % in
  ~10 us while tlp moves ~27 % of the way: 1.25 tlp stays ~8 % above ton (mu 0.2 would leave ~4 %).
- RTL (scb_vff, cfg vff "rel_lp" 1 via scb_ctrl cfg_vff_rel_lp, bridge, scb_multi regenerated): one register; rel_lp 0
  is A135's path. Unit tests 76 (1 new: ton 133 -> 200 LSB before a Vin rise, the cap takes tlp's 134).
- Rows and timing as A135 (steps at 1000 us). Stage 1: l_p48_1us, l_p48_5us, x_l_p80_10us, s_p62, n0 at L x 0.7 /
  1.0 / 1.3. Stage 2: A135's remaining rows (A124's 7 + n0 + matrix at L x 0.7 / 0.85 / 1.0 / 1.15 / 1.3; +8 V at 0.7 /
  1.0 / 1.3). References: A135's f100 (absolute cap, L0, same timing), A129's g125.
- Not tested: L spread between phases, the four-module design, Cs or Coss corners.

## 2. Criteria (definitions as A135: lock vs the same row at L0 + 0.5 points or Vo outside 1 %; peaks at t >= 1000 us)
1. Identity: A135's r100_l_p48_1us rerun (rel_lp absent) bit-identical to A135's record; unit tests 76/76.
2. Stage 1 gate: L0 rising rows within 7 A of f100's (183.0 / 174.7 A); every stage-1 run unlocked; rising
   rows <= 200 A at L x 0.7 / 1.0 / 1.3. Stage 2 runs only if this passes.
3. (Stage 2) A135's criteria 2-5 for arm q: L0 unchanged where the cap is idle (vs A129's g125 tails; post-step peaks
   within 7 A of f100 on the 7 step rows), no lock at any L, every A124 row <= 200 A and the matrix rule at every L,
   recovery (Vo back in 1 %, late <= 100, no overlap).
4. Reported, no pass / fail: +8 V / 10 us peaks (f100 at L0 as the reference), start-up peaks, back times.

## 3. Predictions (D63, a136_predictions.json; ranks only, see above)
- No lock and no binding before a step or at the end at any L; worst A124-row peak 186 / 186 / 187 / 192 / 195 A at
  L x 0.7 / 0.85 / 1.0 / 1.15 / 1.3; +8 V / 10 us 218 / 195 / 186 A at L x 0.7 / 1.0 / 1.3.
- Cosim at L0 should track f100 within a few A on every row (the two caps agree to 1 % there).

## 4. Decision rule
- 2 and 3 pass: the low-pass relative cap replaces A128's absolute cap in the adopted design (cfg vff rel_q8 320,
  rel_lp 1); the L tolerance is +-30 %.
- 2 passes, 3 fails at some L: adopted if no worse than f100 at L0 (criterion 3's L0 part); tolerance = the L range
  that passes; the failing mechanism is the next item.
- 2 fails: not adopted; the absolute cap stays and the design is quoted with A134's tolerance.
