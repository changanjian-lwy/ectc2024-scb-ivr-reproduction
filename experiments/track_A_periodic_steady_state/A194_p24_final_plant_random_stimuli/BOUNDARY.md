# A194 - random stimuli on the final plant (BOUNDARY)
Method: mixed (cosim, plant V5, code e8b1442; cfg only: the adopted start-up of A188 / A190, lead 9.5 ns on slow
boards and 8 ns elsewhere (A192), t_il 1.0 ns)
Track A, package layer, one module. Written and committed before the runs. No run of these cfgs was looked at.
Decision it changes: whether the final specification may be called frozen on the final plant in the way the V0
controller was after A142 / C13. The registered rows cover what we thought of; random stimuli on V0 found the last
real controller defect (A142, 245-388 A). On V5 they were never run (FINAL_SPEC_COVERAGE Section 3, "only on earlier
plants").
Cheaper check done first: none. The mathematical valley model (D63) has no gate delay, lead or interlock, so it cannot
stand in for V5. make_cfgs.py checks that its cold cfgs equal A190's own.
Budget: 36 runs = 31.6 run-equivalents of 900 us, --jobs 6, about 6 h.

## 1. What and why
- Every V5 result so far steps at 500 or 800 us, on a registered row. Not run on V5: stimuli between the rows
  (other amplitudes and slews), a step shortly after the handover (A142's defect was exactly there on V0), unloading,
  and most board x temperature x row combinations.
- 36 draws, numpy default_rng(194), all inside the stated windows:
  - board: N0, N75, N13 (nominal devices, L x 1 / 0.75 / 1.3), F0 (fast), S0, S75, S80 (slow, L x 1 / 0.75 / 0.8);
    each with its factory trim and seed (A183 / A185 / A187);
  - temperature: -40, 0, 25, 125 C; trims locked above 25 C, A190's table below; F0 only at 25 / 125 C;
  - stimulus: rising line step 1-4.8 V over 1-40 us; falling 1-4.8 V over 1-40 us; falling 4.8-8 V over 10-40 us;
    load step of +-(20-62.5) A; one event per run;
  - instant: 14 early draws at 146-300 us (2 us after the 144 us handover onwards: the 20 us lead ramp and the
    settling), 22 settled draws at 500 us plus a uniform fraction of one period; end 400 us after the event.
- Not tested: L x 0.7 (outside the stated -25 %), four modules, two events in one run, +8 V steps (A139: not
  guaranteed at any slew), fast devices below 25 C (no trim table), device mismatch inside a board.

## 2. Criteria (per draw; engineering layer of FINAL_SPEC_COVERAGE Section 5)
 c1 COMPLETED, 0 shoot-throughs, 0 overlaps.
 c2 physical peak current <= 200 A over the whole run (start-up, handover and after the event reported separately).
 c3 every switch V_DS <= 40 V over the whole run.
 c4 Vo within 1 V +- 50 mV from 20 us after the handover to the end. (50 mV is the overshoot Intel's VRD 11.1
    guideline allows above the set point for 25 us; it is stated for motherboard processor regulators and is used
    here only as the level. Largest V5 value so far: 31.8 mV, ff board, -8 V / 10 us, A174.)
 c5 Vo back within 1 % of 1 V at most 60 us after the event ends (line: step instant + slew) and inside 1 % from
    there to the end. (Largest V5 value so far: 37.9 us, L x 0.7, A174.)
Diagnostic layer, reported and not judged: late fires before / after the event, oracle events (a142_oracles through
the A174 chain), interlock holds, one-period spikes. Known on V5: restarts and 10-20 A spikes after falling steps
(A175 / A176), more spikes cold (A193).

## 3. Predictions (not criteria)
- c1 and c3 pass on all 36.
- c2: 0-3 misses. Most exposed: S75 / S80 after rising steps near 4.8 V (2.2 A margin at +4.8 V / 1 us, A193); small-L
  boards after falling steps of 2-4 us (V0: 192 A at 2.3 us, A139; physical peaks are 5-8 A above command-time ones);
  early draws inside the lead ramp, which no run has covered.
- c4 passes on all; c5: 0-2 misses, on slow boards after ramps (A173: dips 3-5 mV deeper than V2).

## 4. Decision rule
- No c1-c3 miss: the coverage file states "36 random draws inside the stated windows pass on V5, one module", and
  the line "random stimuli only on V0" is changed accordingly. c4 / c5 misses are listed as regulation rows.
- A c1-c3 miss: first read the record (phase, event, step phase, which mechanism of A147 / A163 / A187 it matches),
  then rerun that draw with neighbouring instants and amplitudes (at most 6 runs) to tell a point from a region.
  Then either a driver-side or cfg-side remedy within the authorised means, or a narrower window in the
  specification. The frozen RTL does not change here.
- The draws are not extended after seeing results; a follow-up gets its own number.
