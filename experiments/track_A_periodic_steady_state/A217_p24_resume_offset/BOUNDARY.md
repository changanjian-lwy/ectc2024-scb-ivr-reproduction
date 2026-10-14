# A217 - a resume that ends at the valley target (BOUNDARY)
Method: RTL (one output) + bridge (the front end's threshold during a resume) + cosim.
Track A. Written after A216's first four V6 rows and two ideal-plant runs, committed before A217's runs.
Decision it changes: whether skipping (A216) is adopted, which A216's s3 blocked.
Cheaper check done first: ideal plant (A143's cfg, 5 % load, ton_lat 16): with a 3.75 A offset phase 1's first
valley after a resume moved from -18.3 to -14.6 A, all valleys of the last 20 us from -22.4..-12.6 to -18.8..-13.0 A,
and the two-period alternation was no longer started.
Budget: 6 runs, about 3 run-equivalents of 900 us.

## 1. What and why
- A216 (V6, records z_N0_25_10, z_N75_25_10, z_N0_25_0): s1, s2 and s4 passed, s3 missed by up to 20 A. Every burst
  starts the same way: phase 1's resume interval ends about 8 ns after its comparator crosses the target (front end
  and driver), so its first valley is 2.7 A (N0) to 4.0 A (N75) too deep; phases 2-4 take that interval's length
  and add the different currents they were ringing at (-21..-27 A on N75); the error then alternates and decays
  over about eight rounds (phase 3 on N75: -26.9, -7.5, -20.6, -13.6, -17.8, -14.9, -16.6, -15.0 A). The last round
  before a pause is back at -15 A. On N0 the ladder also sits 1.8 V uneven while skipping (rails 11.2-12.9 V), and
  phases 3 and 4 settle at -13.3 / -11.9 A.
- Change: during a resume's interval (res1, a new output of scb_ctrl) the front end's threshold is raised by
  "res_ofs_a" = 8 ns x Vo / L of the board (N0 2.73 A, N75 and S75 3.64 A). Nothing else changes.
- Rows: A216's six skipping rows (N0 at 10 % and no load, N75 and S75 25 C at 10 %, S75 125 C at 10 %, N0 5 % with
  +62.5 A) with the offset; A216's records of the same rows are the references.
- Not addressed: the ringing currents the phases resume from, and the ladder's drift on N0.

## 2. Criteria
1. j1: offset and skip absent, the cosim is the old one (unit tests, regression quick and full).
2. A216's s1, s2, s3 on the six rows and s4 on the +62.5 A row, by a216_analyze.one, unchanged in definition.

## 3. Predictions (not criteria)
- Phase 1's first valley after a resume within 1.5 A of -15.6 A on N0 and N75. The alternation's first swing
  shrinks by half or more. s3 passes on N75; on N0 phases 3-4 still sit near -12 A (the ladder) and may miss by up
  to 1 A; the no-load row's phase 4 (-39.7 A in A216) comes inside -25 A but not inside the band.
- The slow board: open (A216's S75 rows have not finished when this is written).
- s1, s2, s4 as in A216; loss within 5 % of A216's.

## 4. Decision rule
- s3 passes on N0 and N75 (or misses by at most 1 A on N0's phases 3-4, the ladder's share): skipping is adopted
  with the offset; the ladder's drift stays as an open item with its number.
- s3 still misses by more than 1 A on a nominal board: not adopted; the next step resumes each phase from its own
  comparator.
