# C06 - Slave slot floor for the four-module final design (BOUNDARY)
Track C. Written and committed before the C06 matrix runs. Code: 7b6dad7 (RTL scb_phase/scb_ctrl/scb_multi, bridge, unit tests 64/64).
Looked at beforehand (smoke, tmp/, 260 us, not part of the record): slave_floor off reproduces C05's m1n bit for bit (all four modules' sections); with the floor, m1n late 2/6/6/5, peak 166-184 A, slave phase-1 valleys >= -21 A and back to -15.6 A by 220 us; j100 completes, no overlap, peak 163-164 A.
Decision it changes: whether the four-module final design passes the standard matrix (then the multi-module summary is restated for the final design) with the slave floor as the one RTL addition.
Cheaper check done first: the smoke above. Budget: 18 runs x ~15 min at --jobs 6, ~45 min.

## 1. What and why
- C05 (ea6b82c, RESULTS 0b): m1n, m3n, j100 fail in the post-handover transient because a slave's slotted phase 1 has no current-decided turn-off; its valley runs to -96/-130 A, the master's Ton rises to its cap, positive feedback.
- Fix: A118's floor on the slave's phase 1 (cfg "slave_floor" 1): its front end armed in LOW (mode P) at i_target + trim - lo_floor_a (2 A); a report before the slot is the turn-off. Off = C05 bit for bit.
- Rows: C05's 18 (make_cfgs.py: C05 cfg + slave_floor 1). References: A129's single-module g125_<row>; ls_* against C06's n0; every row also against C05's run.
- Not tested: a floor on slotted phases 2..N; module spread; other seeds.

## 2. Criteria (C05's, on the C06 runs)
1. No overlap; peak <= 200 A (step rows: after the step).
2. Locked; 16 gaps T/16 +- 0.1 ns at m = 0, sigma = 0.
3. Per module like the single module (n0, m, j): valleys +-0.5 A, HS on +-0.2 V, LS max <= single + 0.3 V, sd band.
4. Steps: Vo extreme +-10%, back within single + 2 us, ladder peak <= single + 0.01.
5. ls_p5 / ls_p10: slave 1 current -4.6 +- 1.5% / -9 +- 3%, LS turn-on V_DS <= 0, valleys <= -2.5 A.
6. Late fires <= single module's (+6 in jitter rows).
7. (new) A row in which no slave floor fired is identical to C05's run (all modules, every section).

## 3. Predictions (not criteria)
- m1n, m3n, j100 pass criteria 1, 2 and 6; m1n peak 165-190 A (smoke 184 A), j100 163-165 A.
- The floor fires only in the post-handover transient (and in line / load steps if a slave valley gets 2 A below target); rows where it never fires are identical to C05 (criterion 7), so the rows that passed in C05 keep their numbers.
- C05's minor misses (Vo +-10% in l_p48_5us and l_m80_10us, single late fires in line rows, j30 LS V_DS) are unchanged by the floor and stay as recorded.

## 4. Decision rule
Criteria 1, 2, 6 pass in all 18 rows -> adopt slave_floor for the multi-module final design; restate the multi-module summary (addendum), scorecard, CURRENT_STATUS once. A hard-constraint miss -> report with its numbers; next candidate: a floor on slotted phases 2..N.
