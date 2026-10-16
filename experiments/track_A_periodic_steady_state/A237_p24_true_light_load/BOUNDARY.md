# A237 - light load as a true current: releases to 0 / 2 / 10 % without the 4 mOhm base (BOUNDARY)
Method: cosim + a bridge cfg option (t_load_off_us; absent = bit-identical). Code and cfgs committed before the runs.
Track A. Looked at beforehand: A229's z / w records and their cfgs, circuit.py's load model, A230's true no-load rows.
Decision it changes: whether FINAL_SPEC_COVERAGE's light-load statements hold for a load that does not sink: "no
minimum load on nominal boards" and "N0 with no load regulates at 1.0017-1.0049 V" (A221 / A222), and with them item
6b's scope (start-up only, or every event that leaves Vo high at a near-zero load).
Cheaper check done first: the records and a hand estimate (below). Budget: 8 runs, about 50 min at 8 jobs.

## 1. What and why
- Every light-load row since A216 (skipping, item 9's re-applications, the "no load" rows) kept the full-load 4 mOhm
  resistor and added a current step: 10 % = 250 A x Vo - 225 A, "no load" = 250 A x (Vo - 1 V). That load has the full
  load's 250 A/V at every load: above 1 V it sinks current. A resistive 10 % load has 25 A/V, a processor's current
  about none. Within the skipping band (+-5 mV) the difference is <= 1.25 A, but an overshoot is pulled down by it:
  A229 z_N0_0 releases from full load to "no load" peak at +52.5 mV and are back within 1 % 35 us later.
- With a true current load nothing but the load discharges 4.67 mF while the module pauses (no sink, A230's item 6b):
  hand estimate +52 -> +10 mV takes ~40 us at 5 A, ~8 us at 25 A, and does not happen at 0 A.
- Option (A237): cfg "t_load_off_us": the resistive load disconnects at that time; the load steps alone remain. Rows
  (one module, plant V7, A229's adopted cfgs, release at 300 us): N0 and N75 to 0 A and 25 A constant current; N0 to
  5 A; re-applications from 12.5 A constant current to 250 A at 380 us (N0, N75; A229 w5); S75 at 125 C from 75 A to
  250 A at 380 us (A229 w30_S75h). References: the same releases on the 4 mOhm base (A229 records).
- Basis: Intel VRD 11.1 guidelines (2009): overshoot at most 50 mV above the set point, for at most 25 us (regulators
  for processors on the motherboard; default soft-start 500 us). That a processor load is a current, not a resistor,
  is our assumption; no source in the basis states a test load's conductance.
- Not tested: start-ups into these loads (A230 did 1 kOhm), four modules, other temperatures for N0 / N75.

## 2. Criteria
- g0 (0 A rows): Vo within 1 % over the last 20 us (the question; the hand estimate says it misses).
- g1 (every row): completes, whole-run gate-level peak <= 200 A, V_DS <= 40 V, no overlap or shoot-through.
- g2 (rows with current > 0): Vo within 1 % over the last 20 us.
- g3 (25 A rows): A229's skipping run test (q1) and the true valleys within A228's band (-20..-12 A).
- g4 (re-applications): post-step peak <= 200 A and <= the 4 mOhm reference + 10 A.
- Identity: cosim_regression quick and full PASS on fresh outputs with the option absent.

## 3. Predictions (not criteria)
- 0 A: Vo peaks +45-55 mV after the release and ends above 1.03 V (g0 misses, VRD 11.1's 25 us exceeded).
- 5 A: back within 1 % 30-60 us after the release. 25 A: within 15 us, valleys as the reference within 1 A.
- Re-applications: peaks within 5 A of the reference, the dip after them 0-5 mV deeper (a current load does not ease
  as Vo falls).

## 4. Decision rule
- g0 misses: the coverage's "no load" statement is corrected (it holds only for a load that sinks above 1 V), and item
  6b becomes "no sink at a near-zero load after any overshoot"; its fix (a sink mode or a minimum load) is the next step.
- g1-g4 pass: the 2-100 % light-load statements stand for a current load; a miss is traced before any statement moves.
