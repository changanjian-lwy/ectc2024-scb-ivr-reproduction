# A187 - the slow corner's inductance at 125 C after +4.8 V / 1 us, six step positions (BOUNDARY)
Method: mixed (cosim, plant V5, code cfe581f; the start-up of A186: mode S at 200 ns with its own trim (cfg_ton_s),
bumpless loop seed, handover requested at Vo 1.03 V; cfg only)
Track A, package layer. Written and committed before the runs.
Decision it changes: FINAL_SPEC's inductance tolerance for slow devices. A181 left it open ("~0.8 L0, an estimate");
A184 / A186 show L x 0.75 at 125 C exceeds 200 A after the step at some step positions.
Cheaper check done first: records. S75 at 125 C post-step: 194.7 / 202.8 / 199.1 A at step phases 0.48 / 0.81 / 0.15
(A181), 206.7 A at 0.86 (A184), 193.8 A (A185), 197.2 A (A186). The miss depends on where in the period the step
lands. Its peak comes on phases 2-3 at +23-28 us. Budget: 3 trim start-ups + 12 runs, --jobs 6, ~3.5 h.

## 1. What and why
- After the start-up fix (A183-A186), the only 200 A miss left at L x 0.75 with slow devices is post-step at 125 C,
  in mode P. That is a tolerance question: which L keeps it at every step position?
- Boards: S75 (L x 0.75: trim 35.451 ns, seed 45.355 ns) and S80 (L x 0.8: trim from three 25 C start-ups at
  35.0 / 35.5 / 36.0 ns interpolated to Vo(143.5) 1.035 V; seed T_ss + (kp + ki)(1.032 V - 1 V), T_ss interpolated
  linearly in L between S75 32.306 and S0 40.984 ns, an estimate, not a measured seed). 125 C, both trims locked
  at 25 C. Steps at 500 us + k T / 6, k = 0..5, T = 0.5048 us x L scale; the phase after phase 1's last low-side
  turn-off is read, not imposed.
- Not tested: L between 0.8 and 1.0; other rows; four modules; 25 C at these positions (S75 at 25 C stayed
  <= 198.7 A at phases 0.12-0.88, A181 / A184).

## 2. Criteria (engineering, per run)
 c1 start-up / handover (entry .. + 25 us) <= 200 A;  c2 post-step <= 200 A;  c3 V_DS <= 40 V, COMPLETED, 0
 shoot-throughs / overlaps;  c7 Vo <= 1.05 V over 0-300 us.
Per board: holds 200 A at 125 C if c1-c3 pass at all six positions.
Diagnostic: step phase, the post-step peak's phase and time, handover Vo minimum.

## 3. Predictions (not criteria)
- S75: post-step 192-208 A, > 200 A at the positions whose phase falls in ~0.75-0.95 (1-2 of 6).
- S80: post-step worst 193-201 A (the ripple part falls ~6 % with L). Uncertain whether it clears 200 A.
- S80 trim ~35.5 ns (all-hard trims are nearly L-independent: S75 35.451, S0 35.795).

## 4. Decision rule
- S80 holds and S75 does not: slow devices need L >= 0.8 L0 for +4.8 V / 1 us at 125 C (tested points). FINAL_SPEC
  states it per device corner (nominal: 0.75 L0 at 25 C, A178).
- Both hold: L x 0.75 holds at 125 C with the A186 start-up (the earlier misses were positions). State the tested
  positions.
- S80 fails too: the limit is above 0.8 L0; named, with the next point (0.85) not run here.
- c3 fails anywhere: reported first.
