# A199 - the plant against LTspice over whole periods (BOUNDARY)
Method: mixed (cosim, plant V5, final configuration, to record states and gate commands; then LTspice with EPC's
EPC2067 model on all 20 switches replaying those commands open loop; scripts/p24_replay.py)
Track A, package layer. Written and committed before any replay. No replay of any snapshot has been run or seen:
the replay tool is new and will be debugged on these same snapshots (Section 4, last point).
Decision it changes: whether the plant's numbers can be quoted as checked by an independent simulator over whole
switching periods, and to what tolerance. If not, the plant is corrected before any further experiment.
Cheaper check done first: D79 compared seven single edges (40 ns each) and agreed within 0.1 ns, 0.2 V and 5-9 %.
Nothing between two edges, and no sequence of edges, has been compared.
Budget: 3 cosim runs (1.5 run-equivalents of 900 us, about 40 min) and 23 LTspice replays of about 1 us each.

## 1. What and why
- Every result since A163 comes from one plant written here. It is a hybrid: gate-driven edges use EPC's device
  equations, but a conducting switch is an ideal short, a zero-voltage turn-on is instantaneous, reverse conduction
  is a straight-line fit, C_OSS is the datasheet curve, and the switches' resistance is one resistor per phase
  (0.54 mOhm, the duty-weighted maximum R_DS(on), D62). LTspice with the vendor model has none of these shortcuts.
- Method. The bridge records the plant's full state at each phase-1 high-side turn-off command (cfg snap_us; new,
  read-only, regression 4 / 4) and every gate command it applies (debug_edges_us). A replay starts LTspice from one
  snapshot, applies the same commands for two periods and is compared with the plant at the next snapshots and
  at each edge in between. Short replays from many snapshots, not one long one: open loop, a small difference per
  period would otherwise pile up and hide where it comes from.
- LTspice circuit: the plant's passive network (2.933 nH phases, 50 pH loops with 0.82 ohm across, 6 uF flying
  capacitors, output capacitor, load), 2 + 3 vendor devices per switch, 3.0 ohm to +5 V while a command is high and
  0.3 ohm to the source while low. Phase resistance "match": 0.54 mOhm minus the vendor devices' own duty-weighted
  typical R_DS(on) (1.28 mOhm per device), so both circuits lose the same on average; "zero" as a second variant.
- Runs (nominal devices, 25 C, a194 make_cfgs.board): N0 without an event (snapshots in mode S at 141.0-142.3 us,
  where every turn-on is hard, and settled at 292.0-296.5 us); N0 and N75 (L x 0.75) with +4.8 V / 1 us at 500 us.
- Replays, fixed by rule (a199_analyze.plan): N0 steady: 4 in mode S, 6 settled, the first 3 settled again with
  "zero". Step runs: the last snapshot before the step and the next one, and the three ending at the plant's
  largest peak (starting two periods, one period and no period before it). 23 in all.
- Not tested: slow or fast devices, other temperatures, interlock holds (the replay refuses records with holds),
  four modules, anything longer than two periods.

## 2. Criteria (per replay, LTspice minus plant; a199_analyze.judge)
 c0 the start state arrives: node voltages within 5 mV, phase currents within 0.05 A (a check of the tool).
 c1 every high-side turn-off peak within 2.0 A (1 % of the 200 A budget; the slow corner's margin is 2.2 A).
 c2 one period later: phase currents within 1.5 A, flying-capacitor voltages within 20 mV, Vo within 0.5 mV.
 c3 every switch's largest V_DS over the section interval within 1.5 V.
 c4 every hard high-side turn-on: channel start within 0.3 ns, V_DS there within 1.0 V.
Diagnostics: the phase current at each low-side turn-off command, the state two periods later, the "zero" variant.
Identity: the two N0 records' sections equal A194 r20's (made before the snapshot code) up to 296.9 / 499.9 us.

## 3. Predictions (not criteria)
- c0 passes. c3 and c4 pass in settled operation (D79's edges); in mode S, with every turn-on hard, likely too.
- **c2 fails, with LTspice below the plant by 2-5 A per phase after one period.** The plant makes a low side conduct
  the instant it is commanded on at V_DS <= 0. In LTspice the gate needs a few ns through 3.0 ohm to reach
  threshold, and until then the device conducts in reverse at about 2.3 V: 2.3 V x 4-8 ns over 2.93 nH.
- c1: the first peak of each replay (phase 1, at the snapshot itself) within 0.5 A; the later ones low by the c2
  amount, so c1 fails on some replays.
- "zero" against "match": less than 1 A apart after one period.

## 4. Decision rule
- All criteria pass: the coverage file states the agreement with its tolerances and conditions; the slow corner
  (interlock holds, shifted threshold) follows under its own number.
- c1 or c2 misses with a traced cause: the missing effect goes into the plant (cfg-gated, off = bit-identical) and
  the headline rows (peak, efficiency) are rerun with it before any other new experiment. What a closed loop would
  do with the difference (a longer on-time, more loss) is estimated first from the replays.
- c3 or c4 misses: the same, on the edge model.
- c0 miss, an LTspice failure or a netlist error is a fault of the tool: fixed, rerun, and listed in RESULTS. The
  criteria and the replay rule do not change.
