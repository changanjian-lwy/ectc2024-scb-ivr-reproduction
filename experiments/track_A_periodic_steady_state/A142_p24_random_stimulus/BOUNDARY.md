# A142 - random-stimulus test of the adopted single-module RTL (BOUNDARY)
Method: RTL (cosim of random stimuli; event-level oracles on the records, no model fitted)
Track A (one module). Written and committed before any run. Looked at beforehand: the oracles of `a142_oracles.py` on
the 1342 local records of A132-A141 and C01-C12 (no new runs), to fix the oracles and the known classes below.
Decision it changes: freeze the adopted single-module controller (A141 arm F) as final, or open A143 for a new RTL
arbitration fix before the four-module random test (C13).
Cheaper check done first: the oracle scan of existing records (Section 1). D63 has no RTL arbitration, so it cannot
predict these events.  Budget: 121 runs, 130.5 ms simulated, ~75 min at 10 jobs.

## 1. What and why
- The matrix and A138-A141 change one input at a time at fixed instants. A141's defect (a floor turn-on in the window
  before the committed timed edge, ignored two windows later) was found only by A140's slow-ramp rows. Random
  combinations (L, Cs, driver mismatch / jitter, step instant within a period, line + load together, steps during the
  mode-P comparator phase) can reach other arbitration windows.
- Design under test: A141 arm F = C10 template (g125 + vff rel_q8 320, rel_lp 1, seed 2) + floor_late 1; template
  A141 `cfg_F_s100_l_p48_1us.json`. Generator `make_cfgs.py` (numpy default_rng(142), inputs in `a142_inputs.json`):
  L x U(0.7, 1.3), Cs x U(0.7, 1.3), driver mismatch U(-3.4, 3.4) ns, jitter U(0, 100) ps on low-side edges
  only (high-side jitter moves turn-ons off the LSB grid the duplicate classes rest on; rows j30 / j100 cover it). Strata: L line step only
  (48), B line + load (24, load at t_line + U(-10, 60) us), D load only (24), all at U(1000, 1010) us (latest timed
  entry over A138 / A139's corners: 814 us); S one line or load step at U(160, 900) us (24). Line dv U(+-1, +-8) V,
  slew log-U(1, 50) us; load U(+-10, +-62.5) A. t_end = last event end + 150 us. I0 = the template verbatim.
- Oracles (window: overlap of the turn-on / high-off lists, from mode P + 20 us): duplicate turn-ons (same phase
  < 20 ns), turn-on order 1-2-3-4, on / high-off alternation, one-period spikes (> 10 A above both neighbours of the
  phase), non-predictive turn-ons (how != 0), record overlaps; end state (last 100 sections).
- Scan of existing records fixed the known classes (not defects):
  K1 race duplicate: clocked turn-on, then the floor's front-end turn-on < 1 ns later on a gate already on (V_DS 0);
     next peaks normal (C12 l120_l_p48_1us / s_m25, A141 F_L070_p4.8_s20.0_q3: 4 events).
  K2 order swap 3 -> 1 -> 4 -> 2 inside a fast falling ramp (A138 / A139: 19 runs, all dv <= -6.0 V at >= 4.4 V/us;
     outside A139's certified table). Rule: dv < -5.5 V, |dv| / slew >= 4 V/us, within the ramp + 2 us.
  K3 restart (how 3) after a positive valley of that phase (A138 tf06: low-off at +11.7 A, peaks 133 A).
  K4 one-period spike inside a line ramp + 1 us or within 1 us of a load step (A141 F_s130_l_p48_1us phase 1 at
     +0.76 us, 14.7 A; C12 l120_l_p48_1us: 11.6 / 13.7 A; fast-ramp physics, no duplicate).
  Classification check (`a142_analyze.py --files`): A141 F 18 / C12 22 records -> K1 4, K4 3, NEW 0; A140 B (no
  floor_late) floor-first 84; A138 / A139 (no floor_late, 654) order all K2 (66), restarts all K3 (2), NEW spikes 59 of
  which 54 follow an other-type duplicate (none in floor_late records) and 5 have no duplicate (10.1-15.4 A excess,
  133-196 A, falling rows 2.4-14 us after the step).
  Dropped: a period-ratio oracle (it flags the smooth period change of fast falling steps); a skipped or extra turn-on
  shows as an order hit.
- Not tested: four modules (C13), start-up before mode P + 20 us, peaks against a spec (A139 owns the peak map).

## 2. Criteria (all 121 runs)
1. Floor-first duplicate turn-ons: 0 (and no spike after one).
2. Record overlaps 0; alternation hits 0.
3. NEW hits 0: any duplicate other than K1 / floor-first, order hit outside K2, spike outside K4, non-predictive
   turn-on outside K3.
4. Settling: every run COMPLETED from unmodified sources; |Vo_end - 1 V| <= 1 %; ladder deviation at the end <= 0.03
   (A138 / A139 runs: <= 0.016; A134 lock ~0.09).
5. I0 replays A141's run_F_s100_l_p48_1us bit for bit (turn-on and high-off lists, ipk).

## 3. Predictions (not criteria)
- K1 in 5-20 % of runs, next peak within 2 A of its neighbours. K2 only in z117 (the one draw in its region), if at
  all. K3 in <= 2 runs (1 of 654 before). K4 in some of the six rising draws >= 4 V/us (z004 z021 z026 z047 z054 z060).
- Post-disturbance peak <= 200 A in >= 85 % of the L / B / D runs (A139 map); S runs: no prediction.
- 0 NEW duplicates / order / how hits. NEW spikes without a duplicate: ~1 (5 in 654 before), 10-16 A, in falling
  rows. With 0 NEW in 121 runs, a defect class hit by this input distribution has a per-run rate < 2.5 % (95 %).

## 4. Decision rule
- 1-5 pass: the single-module controller (A141 arm F) is frozen; next C13 = the same generator on four modules.
- 1-3 fail: every NEW / floor-first event traced to its RTL window (event trace as A141). Criterion 3 stays failed
  either way; the trace decides the decision: an arbitration defect (a turn-on / turn-off decided in the wrong window)
  -> A143 fix with the failing draws as regression rows, C13 waits; a plant transient with every edge in its intended
  window -> named as a new known class with its evidence, controller frozen, C13 next.
- 4 fails: lock / settling diagnosis (A134 method) before anything else. 5 fails: the toolchain changed - stop.
