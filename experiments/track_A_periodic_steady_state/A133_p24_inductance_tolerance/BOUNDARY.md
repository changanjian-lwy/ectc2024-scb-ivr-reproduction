# A133 - L tolerance and floors on phases 2-4 (BOUNDARY)
Track A, single module, the adopted 2.5 MHz design (A129's g125). Written and committed before the runs. Looked at
beforehand: four n0 pilots (`make_cfgs.py pilot` -> tmp/pilot_a133/) and A132's D63 corners (a132_d63.json).
Decision it changes: whether the design gets floors on phases 2-4 (cfg `ph_floor`) and the L tolerance it is quoted
with. Cheaper check done first: the pilots and D63 (below). Budget: 96 cosim runs + 2 identity reruns, ~30 min at 10 jobs.

## 1. What and why
- A132: L +30% leaves the ladder in a limit cycle. Pilots (n0, C nominal): mode S ends balanced at every k_L (144 us:
  12.1 / 11.9 / 12.0 / 12.0 V); after the handover rail 1 swings to 14.0 / 16.5 / 17.2 V at k_L 1.1 / 1.2 / 1.3.
  k_L <= 1.2 is balanced again by 300 us (tail as nominal); k_L 1.3 stays in the limit cycle to 2000 us (rails
  13.5 / 11.6 / 11.4 / 11.4 V, phases 2-4 valleys -23 to -24 A mean / -44 A min, turn-on V_DS -2.2 V: the high-side
  diode conducts first, Vo pp 12.9 mV). Starting the loop at Ton x 1.3 (`ton_ns` x 1.3) gives the same cycle, so it is
  not the loop's start value. D63 from the balanced state stays balanced at L x 1.3 -> a co-simulation-only mechanism.
- Hypothesis: phases 2-4 have no correction from their own current (scorecard T16); a too-deep valley lets the
  high-side diode conduct before the turn-on, which adds on-time to that phase, moves the ladder towards rail 1 and
  deepens the valleys further. A floor cuts the loop at its start.
- Method: C06's slot floor on phases 2-4. RTL: `scb_ctrl` cfg_ph_floor -> `scb_phase` cfg_slot_floor for k >= 1 (C06's
  code path), output arm_n, inputs fa_valid / fa_tlo. Bridge: a front end per phase 2..N at phase 1's floor threshold
  (i_target + trim - lo_floor_a 2 A; phase 1's trim: same slope -Vo / L and delays), SL off and SH on after dt_pred as
  `latch_fire`; record `ph_floor_fires`, `ph_floor_log`. Plant kernel: up to 4 extra latches (RUN_XLATCH). All gated
  (off = unchanged); unit tests 73/73 (3 new: off never arms, arms in LOW, a report is the slot).
- Rows: A124's 7 step rows + n0, A129's standard matrix (8). Corners (k_C, k_L): nom, l07, l12, l13, c07l13. Arm p
  (floors on): nom / l07 / l12 / l13 x 16 rows, c07l13 x 8 step rows. Arm f (off): l07 / l12 / l13 x 8 step rows
  (nom f = A129's g125 records). Steps at 800 us, end 1000 us.
- Not tested: the multi-module design (C08 if adopted), L spread between phases, the depth loop (A134).

## 2. Criteria (tail = last 200 periods)
1. Identity: off reruns of A129's g125_n0 and g125_l_p48_1us bit-identical (sections, turnons / lowoffs / highoffs).
2. Nominal steady state: pnom_n0 tail valleys and peaks within +-0.2 A, rails within +-0.02 V of A129's g125_n0; no
   floor fire after 600 us.
3. Nominal disturbances (p): no overlap; A129's matrix rule on the 8 matrix rows; post-step peak of each step row
   <= A129's g125 peak + 7 A (A129 noise floor).
4. L x 1.3 (pl13_n0) balanced: tail rails within +-0.3 V of pnom_n0's; phases 2-4 tail valley means in [-19, -14] A;
   turn-on V_DS > 0 V on every phase in the tail; Vo pp <= 2 mV; rails at 600 us within +-0.3 V of the tail.
5. Criterion 4 for pl07_n0, pl12_n0 and pc07l13_n0.
6. Corners l07 / l12 / l13 (p): no overlap; A129's matrix rule on the matrix rows; step rows not runaway (scb-map
   rule) with Vo back within 1 % before the end.
7. pc07l13 step rows: as 6.
Not criteria (the tolerance map): every row's post-step peak against 200 A per corner and arm; floor fires per row.

## 3. Predictions
- Floored steady state at L x 1.3: balanced, Ton ~49 ns, period ~650 ns (linear in k_L through the pilots' 37.8 /
  41.5 / 45.3 ns and 505 / 555 / 604 ns at 1.0 / 1.1 / 1.2); no floor fire in the tail at any corner.
- Step-row peaks with floors = A129's g125 peak + (D63(corner) - D63(nom)) (a133_predictions.json; D63 without the
  feed-forward, so only its change is used; A125 80 % band x 0.875-1.125 on D63's own peaks):
  l_p48_5us / l_p48_1us / l_m48_1us / l_m48_5us / l_m80_10us / s_p62 / s_m62 [A]
  l07 173.9 / 177.0 / 169.9 / 168.4 / 165.9 / 178.9 / 144.3;  l12 177.5 / 185.8 / 181.7 / 177.5 / 173.8 / 177.5 / 143.6
  l13 179.3 / 184.5 / 176.8 / 179.1 / 174.8 / 177.2 / 143.6;  c07l13 181.6 / 186.6 / 184.9 / 180.4 / 175.4 / 177.0 / 143.2
- Off arm: l13 in the limit cycle with +4.8 V peaks > 200 A (A132: 251 A at c07l13); l07 and l12 balanced.

## 4. Decision rule
- 1-5 pass, 6-7 no failure -> adopt `ph_floor` 1 on top of g125 (single module); T16 closed for phases 2-4 of one
  module; quote the L range over which every row is <= 200 A; C08 = the same floors on the multi-module design.
- 2 or 3 fails -> the floors change the nominal design: not adopted as default; report what they cost.
- 4 fails -> the floors do not remove the limit cycle: hypothesis wrong; report and stop A133 there.
