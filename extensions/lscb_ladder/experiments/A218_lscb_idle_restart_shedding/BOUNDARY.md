# A218 - LSCB's idle state on the P24 module: stage shedding and restart after idle (BOUNDARY)
Method: math (open-loop LTspice power stage, `scb_ivr.extensions.lscb_ladder`; plant = A180's, no controller).
Extension lscb_ladder. Written and committed before any run. Looked at beforehand: the paper (Sec. 2, Figs. 3, 4, 9) only.
Decision it changes: what the EEK5101 video and the extension README may say about LSCB's "phase shedding" on our
design - which kind of shedding is possible, and whether the ladder's idle clamp helps a shed module restart.
Cheaper check done first: charge balance (Section 1) predicts the shedding answer; the runs measure how fast it fails.
Budget: 8 runs, ~15 min at 2 jobs (three other lines hold most of the CPU).

## 1. What and why
- LSCB: the ladder "maintains the flying-capacitor voltages during idle operation ... enabling phase shedding"
  (Fig. 4 right, Fig. 9). In LSCB's 2D structure a "phase" is a parallel column of four stacked cells; in an SCB the four
  interleaved "phases" are the stacked cells. Our P24 module is one column; the four-module system has four, and
  A207 / A210 named module shedding as the light-load candidate.
- Charge balance: Cs_k is charged by phase k and discharged by phase k+1. Stop one stage and its neighbour's capacitor
  is charged one way only, so the rails drift (P24). With the ladder clamped in every LS interval, the stopped stage's
  ladder domain is no longer discharged while the series string still charges it: the drift moves into the ladder.
  So neither design can shed a stage; LSCB's shedding has to be whole columns (our modules).
- Rows (48 V, fixed ton0, no feed-forward):
  - shed4: full load (4 mOhm), steady start; phase 4 stops after its last whole period before t_shed = 10 us; base and
    actall_c20 (switch closed in every LS interval of the running phases); to 40 us.
  - restart: 25 % load (16 mOhm); idle start (every switch off, inductors 0 A, Vout 1.0035 V, ladder nominal);
    switching resumes at 0.5 us with ton0; to 30 us. Cs after the idle (an assumption - the model has no drift source):
    - base: delta = 0 / Vout / 2 / 4 V below nominal on all three (a uniform discharge, e.g. drivers fed from them);
    - d07_c20: the 0.7 V diode stops the drift at vf + Vout = 1.70 V below the ladder (delta 4 -> 1.70);
    - act_c20: the switch, closed through the idle, holds Cs at ladder - Vout (1.0035 V below nominal, the switch node
      rests at Vout), then closes in LS intervals for 20 us after the restart.
- Not tested: drift rates (no leakage or driver model), closed loop, modules in parallel, package, losses.

## 2. Criteria
1. base shed4: rail_dev_max (period-averaged |rail - 12 V| after t_shed) >= 3 V.
2. actall_c20 shed4: ladder_dev_max (period-averaged |ladder node - nominal| after t_shed) >= 1.5 V.
3. restart: base rs2 peak (max over phases) >= base rs0 peak + 15 A.
4. restart: act_c20 rs4 rail_dev_max <= base rs0 rail_dev_max + 0.5 V and its peak <= base rsv peak + 5 A.
5. restart: d07_c20 rs4 peak <= base rs4 peak - 15 A.

## 3. Predictions (not criteria)
- shed4 base: Cs3 gains about I_L3 x ton per period (~5 A average, ~0.9 V/us at first); rail 4 up, rail 3 down;
  rail_dev_max 4-12 V. actall: ladder node d1 up ~0.2 V/us; ladder_dev_max 2-6 V; rail_dev_max 2-6 V.
- restart: base rs0 peak 140-170 A (the first on-time from 0 A adds ~145 A); rsv +12-22 A; rs2 +25-45 A; rs4 +50-90 A.
  d07 rs4 (1.70 V) 30-60 A below base rs4. act rs4: first pulse like rsv, rails nominal after the first LS intervals.

## 4. Decision rule
- 1 and 2 pass: the video says LSCB's "phase shedding" means whole columns (our modules); stage shedding fails in both.
- 3 passes and 4 or 5 passes: the idle clamp is useful for restarting a shed module, stated with delta as an assumption.
- 3 fails: a 2 V drift does not matter at restart, so the idle clamp brings nothing here; said as such.
- Extension only: no change to the reproduction or the controller.
