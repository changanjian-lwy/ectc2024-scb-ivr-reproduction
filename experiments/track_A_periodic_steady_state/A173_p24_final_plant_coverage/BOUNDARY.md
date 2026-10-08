# A173 - the final gate-level plant on the rest of the matrix, four-module cases and realisable interlock delays (BOUNDARY)
Method: mixed (EPC2067 gate model on all eight switches, threshold-form driver interlock; frozen RTL controller;
cfg only)
Track A, package layer. Written and committed before the runs. Prompted by an external review of D70-D79 / A163-A172
(2026-10-08), which found that the summary's "every corner, four modules" ran on two plant versions.
Looked at beforehand:
- Final plant = A172 (A167's drive, every switch gate-driven, threshold interlock t_il 0.5 ns). On it only
  +4.8 V / 1 us ran: A171 nom / ff / hot / ss / L x 0.7, A172 L x 0.7 re-trimmed and four modules nominal.
  Load steps, falling ramps, slew4, L x 1.3 and every other four-module case ran with ideal low sides and no
  interlock (A164 / A167; C14 with ideal switches).
- Interlock holds: 0 on A171 nom / ff / hot and A172 four modules (the rule never acted), 10 / 2 on L x 0.7, 84 on
  ss. Zero shoot-throughs there are imposed by the ideal rule.
- Realisable release delay (EPC model, D79 resistances; comparator 0.5 ns + complement's gate falling from its
  channel-off level to the reference + the held gate charging from the reference to its own channel start):
  reference per board (V_th - 0.2 V) 0.95-1.36 ns at every corner; fixed 1.0 V reference nom 2.04 ns, ss 8.29 ns.
  A171 ran t_il 1.0 ns on L x 0.7 only.
Decision it changes: whether "the final spec holds on the matrix, at four modules and with a buildable interlock"
can be reported, and whether the interlock needs a per-board reference. Cheaper check done first: the delay
estimate above (single edges cannot show the system's timing). Budget: 17 runs + 1 start-up run, --jobs 10,
~5 h wall (single ~1.5-2 h, four modules ~3-4 h).

## 1. What and why
- Coverage (t_il 0.5 ns, A164's trims; A171 shows them at Vo(143.5) 1.029-1.032 V on this plant):
  nom s_p62 / l_m80_10us / slew4, ff s_p62 / l_m80_10us, hot s_p62, ss s_p62 / l_m80_10us / slew4;
  L x 0.7 s_p62 (A172's trim 35.769 ns); L x 1.3 l_p48_1us, re-trimmed from a 150 us start-up on this plant
  (one shot, A164's slope).
- Four modules: ss l_p48_1us (A164 ss trim), nom s_p62, nom l_p48_1us with C14's w5 spread (module 2 at L -5 %,
  the others +5 %).
- Interlock release: ss l_p48_1us at t_il 1.4 (per-board reference) and 8.3 ns (fixed reference); L x 0.7
  l_p48_1us at 2.0 ns (fixed reference, nominal devices).
- Not tested: mixed corners inside one board, comparator offset that releases early (a reference above the lowest
  channel-off level is excluded by the spec, not modelled), ss with an inductor spread.

## 2. Criteria
Rows with a 50 pH gate-level reference (the same row in A167, else A164; the comparator rows against it too):
A168's criteria (a168_analyze.judge), as A171 / A172:
1. Whole-run max V_DS <= 40.0 V.
2. Vo(143.5 us) 1.035 +- 0.02 V; physical start-up and handover <= 200 A (<= ref + 3 A where ref > 197 A).
3. Post-step physical peak <= min(200, ref + 5) A; 0 overlaps, 0 shoot-throughs, COMPLETED; late <= 1.5 ref + 5;
   NEW 0 where ref has none, else <= 1.5 ref + 5.
4. |Vo extreme| <= |ref| + 2 mV; where > 11 mV, back within 1 % <= ref + 2 us.
Rows without one (L x 0.7 s_p62, the three four-module rows): 1 and 2 as above (L x 0.7 start-up against A167's
L x 0.7 board, 202.5 A); 3 with post <= 200 A, NEW 0 and late <= 1.5 x (ideal-switch record of the row) + 5 on
nominal devices (A143 g4_s070_s_p62 2, g5_s_p62 0; C14 w5_l_p48_1us 9; m4 ss late reported only); 4 not applied
to four modules (as A164), L x 0.7 s_p62 back within 1 % at the end.

## 3. Predictions (not criteria)
- nom / ff / hot rows: 0 holds; peaks within +-3 A of the reference; late 0.
- ss rows: tens of holds; late below the reference; peaks within +-5 A.
- L x 0.7 s_p62: start-up 200.2 / 190.2 A as A172 (same start-up); post 176-184 A.
- L x 1.3: trim moves by < 1 ns; post within +-3 A of A164's 185.4 A.
- m4 ss: start / handover ~189 A (as A171 ss); post 178-188 A. m4 nom s_p62 174-182 A (A143 177.7).
  m4 w5: 192-200 A (C14 194.4 A with ideal switches) - may cross 200 A.
- t_il 1.4 ns: as A171 ss. t_il 8.3 ns: late fires several times A171's 194, misses criterion 3.
  L x 0.7 at 2.0 ns: post 198-202 A (A172 199.7 A; A129's step-position noise is 2-7 A).

## 4. Decision rule
- Coverage rows pass: the final plant is reported as checked on A164's matrix, L x 1.3 and these four-module cases;
  any miss is named as open on the final plant, with its mechanism.
- t_il 1.4 passes, 8.3 fails: the spec adds a per-board (or per-device) interlock reference within ~0.2 V of the
  channel-off level. 8.3 passes: a fixed reference suffices. 1.4 fails: the interlock needs < 1.4 ns, beyond the
  estimate for the forms above (open).
- m4 w5 > 200 A: the inductor-matching spec (±5 %, C14 with ideal switches) tightens under the gate plant.
