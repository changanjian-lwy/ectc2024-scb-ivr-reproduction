# A207 - the load range of the final configuration: where one module stops regulating (BOUNDARY)
Method: mixed. Mathematical model (D63, a207_predict.py) for the prediction; cosim with the frozen RTL (cfg only:
load_step) on plant V6 for the result. No RTL, plant or bridge change.
Track A, main line. Written and committed before the runs. Looked at beforehand: D63 at nine loads (the predictions
below) and a 14 us smoke run for the cfg plumbing (34 s).
Why now: LSCB (Tong et al., VLSI 2026) claims a wide load range through phase shedding with clamped flying
capacitors. Before trying that on P24 the baseline is needed, and there is none: of 2815 cosim cfgs none has less
than 75 % of the load on a module (load steps of at most 62.5 A per module).
Decision it changes: whether the specification must state a minimum load per module, and so whether a light-load
method (a lower Ton limit, a burst mode, shedding whole modules as LSCB sheds phases) is needed at all.
Cheaper check done first: D63 (Section 3). Budget: 8 runs of 450 us on V6 (4 run-equivalents), about 70 min at 8 jobs.

## 1. What and why
- The controller regulates Vo through Ton with the valley held at -15.6 A; the period follows (about 12 Ton). Less
  load means a shorter Ton and a higher frequency. The RTL limits Ton to [cfg_ton_min, cfg_ton_max], which the
  bridge sets to 0.5 and 2 times cfg ton_ns (bridge.py). The final configuration has ton_ns = 44.48 ns: Ton >= 22.24 ns.
- At that limit a module still delivers the current of that Ton (D63: about 134 A). A smaller load cannot be
  regulated: Vo rises until the 4 mOhm load takes the surplus.
- Rows: A206's E_N0_steady_ls0p3_t (board N0, 25 C, plant V6, switches at the datasheet maximum, low sides 0.3 ohm,
  A206's start-up trim) with -(1 - p) 250 A drawn from the output from 300 us on, p = 75, 60, 55, 50, 45, 40, 30,
  10 %; end 450 us. The step is instantaneous (a release of 62.5-225 A). The 4 mOhm load stays.
- Not tested: other boards and temperatures, four modules in cosim, a start-up into a light load, a slow load
  change, loads between the rows.
- Basis: none in the literature for the limit itself; it is this controller's Ton range. LSCB's own conditions:
  10-25 A, 500 kHz, 4 x 2.2 uH, silicon chips (180 nm BCD); its shedding turns off a whole N-stage column whose
  flying capacitors a shared capacitor ladder holds at their nominal voltages.

## 2. Criteria (every row)
 r1 COMPLETED, 0 shoot-throughs, 0 overlaps, 0 forced edges, whole-run peak <= 200 A, V_DS <= 40 V.
 r2 Vo within 1 V +- 10 mV over the last 20 us, and within +- 50 mV at all times after the step.
The result is the lowest row that passes both, with each row's loss books over its last 10 us.

## 3. Predictions (not criteria)
- D63 (a207_predictions.json; its Ton is the effective on-time, without gate delays): regulates at 75 / 60 / 55 %
  with Ton 30.0 / 24.9 / 23.2 ns, 2.45 / 2.86 / 3.03 MHz, peak 112 / 93 / 87 A. At the limit from 50 % down: Vo
  150 us after the step 1.022 / 1.069 / 1.116 / 1.210 / 1.398 V at 50 / 45 / 40 / 30 / 10 %.
- Cosim: its Ton command at full load is 2.3 ns longer than D63's on-time (40.85 against 38.59 ns: gate delays), so
  the limit binds at a lower load. 75, 60, 55 and 50 % pass r2; 45 % is at the edge (Vo 1.00-1.03 V); 40 / 30 /
  10 % fail with Vo 1.06-1.12 / 1.16-1.21 / 1.34-1.40 V. Lowest passing row: 50 % (45 % as likely as not).
- r1 passes on every row: peak after the step <= 150 A, V_DS <= 34 V. On the passing rows Vo's overshoot at the
  release is <= 35 mV (D63: 16.8-33.7 mV).
- Loss books, scaled from A206's 20.15 W at 250 A (conduction with the rms current, edges with frequency and peak):
  13-14.5 W at 75 %, 8-10 W at 50 %; Pout / (Pout + loss) 92.5-94 % on the passing rows.

## 4. Decision rule
- A lowest passing row above 10 %: the coverage file states one module's tested load range on this board and the
  specification gains a minimum-load line. The range and loss of four modules, all on or with whole modules shed,
  are composed from the passing rows (a207_analyze; a composition, not a run): LSCB's idea at the level where P24
  can use it. Any remedy (a lower Ton limit, a light-load mode, module shedding with an idle clamp) changes the
  controller or its configuration: a new experiment, and the user's decision, because the controller is frozen.
- Every row passes: light load is covered to 10 % on this board; nothing else follows.
- r1 fails on a row: reported with its record; it is then a safety finding and comes first.
