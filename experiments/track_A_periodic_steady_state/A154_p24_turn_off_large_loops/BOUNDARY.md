# A154 - the turn-off side for loops above 150 pH: voltage and its loss price (BOUNDARY)
Method: mixed (math: single-edge harness law and predictions; RTL cosim cfg only, frozen design)
Track A, package layer. Written and committed before the runs, while A153 runs (no A153 result used here except D68's
registered law).
Decision it changes: whether loops above 150 pH (published embedded GaN 230-320 pH) can be handled by the drive at all,
and at what efficiency; if the price is several percent, the package spec must bound the loop instead.
Cheaper check done first: A145's harness, turn-off of SH1 at 143 / 185 A over L 50-300 pH x 144-18 A/ns (72 edges,
~2 min). It matched the co-simulated steady peak within +1.2 / +1.6 V at 150 / 300 pH (72 A/ns).
Budget: 5 runs x 1400 us, ~1-1.5 h at 10 jobs (alongside A153's last runs).

## 1. What and why
- Above ~150 pH the 72 A/ns turn-off ring passes 40 V on its own (A152: 300 pH 48.8 V steady, 57.8-63.3 V after the
  line step), so D68's turn-on rule is not enough.
- Harness law: for a turn-off ramp longer than half the ring period the peak is ~ V_rail + 2 L di/dt_off (a current
  ramp into an LC); for faster ramps the energy 1/2 L I^2 sets it. With the post-step rail, <= 40 V needs
  x_off = L * di/dt_off <= ~10 V: ~33 A/ns at 300 pH, ~40 at 250, ~50 at 200; 72 A/ns at 150 pH is the edge.
- A slower turn-off costs channel loss (V-I overlap while the current ramps): harness +13 / +19 / +27 / +36 W per
  250 W module at 200 / 48, 250 / 40, 300 / 32, 300 / 24 (pH / A/ns), against 5.3 W at 50 pH / 72.
- Rows (A152's s100_l_p48_1us cfg: frozen design, +4.8 V / 1 us at 1000 us, Q 7, vds_win), turn-on d_on = 2.4 V / L
  (D68's x_on with margin), start-up ton by D68's law:
  f200_off48 (x_off 9.6 V, on 12 A/ns), f250_off40 (10.0, 9.6), f300_off32 (9.6, 8), f300_off24 (7.2, 8),
  f300_off48 (14.4, 8; the control that should fail).
- Not tested: other rows, corners, four modules, a gate model. D68's start-up law is referred to a 72 A/ns turn-off; a
  slower turn-off adds on-time (unmodelled), so the handover Vo may sit higher than D68 says.

## 2. Criteria
1. Whole-run max V_DS (vds_win, all switches) within +-1.5 V of the prediction on all 5 rows.
2. The 40 V side as predicted on all 5 rows (<= 40 V on the four x_off <= 10 V rows, > 40 V on f300_off48).
3. Loss: the channel edge power in the steady window (900-1000 us, sections' edge_energy_j) within +-30 % of the
   harness edge prediction on all 5 rows.
4. Controller: COMPLETED, post-step peak <= 190 A, 0 NEW oracle events (a142_oracles), start-up peak (t < 300 us)
   <= 180 A, on all 5 rows.

## 3. Predictions (a154_predictions.json; not criteria)
- Max V_DS 37.6 V on the four passing rows (set by the turn-on side at x_on 2.4 V; turn-off parts 35.7 / 37.1 / 36.6 /
  31.1 V); f300_off48 47.4 V (turn-off part).
- Channel edge power 12.7 / 18.1 / 26.8 / 38.2 / 14.0 W per module (harness; A145 found the harness ~20 % above the
  records).
- Turn-on at 8-12 A/ns is at A151's "too slow" edge (9 A/ns: one NEW event at 100 pH, Vo outside 1 % for 44 us at
  150 pH): expect Vo recovery after the line step well above the frozen 8 us.

## 4. Decision rule
- 1-2 pass: the turn-off rule (x_off <= ~10 V) joins D68 and the spec map covers 150-300 pH, priced by criterion 3.
- 3 shows >= 10 W extra per module at 300 pH: the Mihai summary states that loops above ~200 pH cost several percent by
  drive alone, so the loop must be bounded by layout (or clamped).
- 4 fails on a row: that drive is not adopted whatever its V_DS.
