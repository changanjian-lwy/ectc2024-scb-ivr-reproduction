# A192 - the 9.5 ns lead on the slow corner's other rows (BOUNDARY)
Method: mixed (cosim, plant V5, code cfe581f; cfg: the adopted start-up (A188), driver hs_on_lead_ns 9.5 on slow
boards, t_il 1.0 ns)
Track A, package layer. Written and committed before the runs.
Decision it changes: whether slow boards (read from the 25 C trim) get a 9.5 ns lead, which closes A187's 125 C
post-step miss (A191), without harming their other rows.
Cheaper check done first: A191 (+4.8 V / 1 us at 125 C, 12 runs). A179's t_il 1.0 ns runs of the slow L0 board at the
same step positions are the 8 ns references (they also used the 400 ns start-up; the post-step behaviour is mode
P's). Budget: 13 single-module runs + four modules, --jobs 6, ~4 h.

## 1. What and why
- A191 cut the post-step late fires on phases 3-4 by ~90 % and removed the > 200 A excursions. The lead also moves
  every predictive turn-on 1.5 ns earlier on rows A191 did not run, and the interlock holds any turn-on that would
  overlap its complement.
- Runs (steps at 500 us + k T / 3, end + 400 us):
  - S0 (slow L0) 25 C: -8 V / 10 us and the +62.5 A load step at k = 0, 1, 2; -4.8 V / 1 us and +4.8 V / 1 us at
    k = 0.
  - S0 125 C: +4.8 V / 1 us and -8 V / 10 us.
  - S75 (slow L x 0.75) 25 C: +4.8 V / 1 us at k = 0, 1, 2.
  - Four slow modules 25 C: +4.8 V / 1 us.
- Not tested: nominal / ff boards with 9.5 ns (they keep 8 ns); slow L x 0.8 on these rows.

## 2. Criteria (per run, every module)
 c1 start-up / handover <= 200 A;  c2 post-step <= 200 A;  c3 V_DS <= 40 V, COMPLETED, 0 shoot-throughs / overlaps;
 c7 Vo <= 1.05 V over 0-300 us;  c10 -8 V / 10 us: post-step late fires <= 36.5 (A179's limit).
Diagnostic against A179 (lead 8 ns): late fires, NEW events, Vo extreme and recovery.

## 3. Predictions (not criteria)
- Every run passes c1-c3, c7, c10. Post-step late fires on -8 V / 10 us fall below A179's 12-32. Load-step NEW
  events at or below A179's 7-27. Vo extremes within +-1 mV of A179.

## 4. Decision rule
- All pass: adopted. The lead is 9.5 ns on slow boards (25 C trim in the slow class) and 8 ns elsewhere. FINAL_SPEC
  states that slow devices hold 200 A with L x 0.75 / 0.8 at 125 C after +4.8 V / 1 us (A191, tested points).
- A row fails c1-c3 / c10 only with the lead: not adopted; A187's limit stands, with the lead's side effect named.
