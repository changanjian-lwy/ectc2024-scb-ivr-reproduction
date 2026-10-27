# A255 - a 125 % load step on the 2.2 nH boards, with and without the peak limit (BOUNDARY)
Method: cosim, cfg only (code 63ea98d; bridge option "ocp" as in A254). Track A. Written and committed before the runs.
Looked at beforehand:
- A254: on N0 a +62.5 A step (125 % load) makes the 125 A limit act in almost every period. The ladder collapses: rails
  3.8 / 26.6 / 3.6 / 14.0 V, Vo 756.9 mV, 241.5 A. Four modules collapse the same way.
- The 125 % step was run on N0 only. A229's k rows are N0 and S75h, and k_S75h is a +4.8 V line step. So the final
  configuration itself has never taken a 125 % load on a 2.2 nH board.

Decision it changes: the overload response's scope (user decision 2026-10-27: the limit is not adopted yet; an
overload response that keeps the ladder comes first).
- If the 2.2 nH boards collapse too, the response is needed on every board.
- If they do not, N0's collapse comes from its level, and the response can be designed on N0's rows.

The arm without the limit also fills a gap in the final configuration's coverage.
Cheaper check first: none. D63 does not carry the limit or the driver path (A253). Budget: 4 runs at 4 jobs, about
80 min, beside the literature survey of overload responses.

## 1. What and why
- Rows o125_N75 / o125_S75h are A246's k_N0 built on the 2.2 nH boards. Take p_<board>_10k, remove its train
  (load_pulse, t_load_off_us, skip, hand_lead_us), and add load_step +62.5 A at 500 us, ending at 620 us.
  make_cfgs.py checks that the same change to p_N0_10k gives k_N0 exactly.
- Arms: h = the final configuration; l = + A254's limit (110 A, t_ns 1).
- Not tested: S75 at 25 C, other overloads (only +25 %), four modules on 2.2 nH, longer than 120 us after the step.

## 2. Criteria
- c1 (arm h, the final configuration at 125 % load), on both boards:
  - peak <= 200 A;
  - ladder deviation max |rail - Vin / 4| <= 1 V in the last 20 us;
  - Vo within 1 % in the last 20 us;
  - V_DS <= 40 V.
- c2 (arm l, no collapse), on both boards:
  - ladder deviation <= 1 V throughout after the step;
  - Vo minimum >= arm h's - 2 mV;
  - peak <= max(arm h, 200 A).
- Reported: the limit's fires, late fires, and N0's pair (A246 k_N0 / A254 run_l_k_N0) for comparison.

## 3. Predictions (not criteria)
- c1 passes: peaks about 175-190 A (full-load peaks 137-142 A, x 1.25, plus the step's overshoot).
- c2 fails on both boards. Full-load peaks are 137-142 A, so at 125 % about 170-178 A. 110 A + 49-69 A in the 11 ns
  path reaches that, and the limit acts in every period from the first tens of us after the step.

## 4. Decision rule
- **c1 fails:** a gap in the final configuration at 125 % load on 2.2 nH. Report it to the user before the response
  design.
- **c2 fails on a 2.2 nH board:** the overload response is needed on every board. Design it with the survey's results
  on k_N0 and o125_*.
- **c2 passes on both:** the collapse is N0's level (125 A). The response is still needed (any larger overload); design
  it on k_N0 and m4_s_p250 first.
