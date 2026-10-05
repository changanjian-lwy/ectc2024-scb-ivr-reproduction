# C14 - D66's sharing cost checked in co-simulation (BOUNDARY)
Method: RTL (cfg only: per-module inductance on the frozen four-module controller; no code change)
Track C. Written and committed before the runs. Looked at beforehand: D66 (its table and limits), A143 g5 / C12 cfgs.
Decision it changes: the inductor-matching specification given to Mihai ("200 A at about ±5 % worst-case spread",
Mihai summary item 5 and Section 4).  Cheaper check done first: D66 (math, calibrated on C12 ls_p5 / ls_p10, C07).
Budget: 13 four-module runs x ~22 min, --jobs 6 (EEK5101 VM up), ~1 h wall.

## 1. What and why
- D66 builds the heavy (smaller-L) module from the measured nominal module and adds a fixed +45 A transient
  increment (C10's worst row, l_m48_1us 189 A over the 144 A steady peak). It was never run with a spread through a
  transient on the frozen design. Its own limits name this run.
- Design: the frozen four-module design (C12 + lo_learn 4, as A143 g5 / C13). Module 2 (slave 1) is the heavy one
  (a slave's phase 1 is slot-timed; D66: a heavy master would be regulated). Spreads, D66's cases: w5 = one at -5 %,
  three at +5 %; o10 = one at -10 %, three nominal; w10 = one at -10 %, three at +10 %.
- Rows: n0 (steady share), s_p62, l_p48_1us, l_m48_1us (steps at 800 us, end 1200 us). References: A143's g5 records
  (n0, s_p62, l_p48_1us at nominal L) and nom_l_m48_1us (run here).
- Not tested: a heavy master; ±20 %; Cs / R spread with it (C04, C07); module 3 or 4 heavy.

## 2. Criteria
1. Integrity, every run: COMPLETED, 0 overlaps, no NEW / FF duplicate events (A142 oracles), Vo back within 1 %
   after the step (matrix.step_stats finite).
2. Steady share (n0, last 200 periods): the heavy module's current over the four-module mean, minus 1, inside D66's
   band widened by 1.5 points: w5 +7.1..+9.6 %, o10 +7.7..+10.2 %, w10 +14.5..+19.8 %.
3. Steady peak (n0, heavy module, mean high-side turn-off current over the last 200 periods) inside D66's band
   +-4 A: w5 154-156 A, o10 156-157 A, w10 165-169 A.
4. Transient peak (max over the three step rows, any module) within +-7 A (A129's step-position noise) of D66:
   w5 199-201 A, o10 201-202 A, w10 210-214 A.
5. Spec: the largest tested spread with every row <= 200 A.

## 3. Predictions (not criteria)
- D66's numbers above; the heaviest peak on l_m48_1us; module 2 carries it. Spec (5): none of the three spreads
  stays <= 200 A on every row (w5 and o10 sit at the limit), so the summary's "about ±5 %" stands.

## 4. Decision rule
- 2-4 hold: D66 and the summary's ±5 % stand. 4 misses by more than 7 A: replace D66's +45 A with the measured
  transient increment and correct the summary's spec number (tighter or looser as measured). 1 fails: the spread
  breaks the controller itself; report it as a new limit, not a sharing cost.
