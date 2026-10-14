# A218 - LSCB's idle state on the P24 module: stage shedding and restart after idle (RESULTS)
Boundary: 318881f. Records: release records-a218 (runs/*.json, run log); a218_summary.json. Plant: A180's open-loop
LTspice power stage of one P24 module (48 V, fixed ton0, ideal switches, no controller, no package).

## 0. Verdict (5 of 5)
- **A stage cannot be shed, with or without the ladder.** Phase 4 stopped at full load:
  - P24 as is: rail 4 (Cs3) 12.0 -> 22.3 V and rails 1-3 down to 8.0-9.1 V within 20 us; Vo 1.00 -> 0.61 V; the
    three running phases end at 48.7 / 39.6 / 21.2 A.
  - With the ladder switched in every LS interval: the rails move less (rail 4 15.5 V at 20 us, rail_dev_max 5.1 V
    against 14.2 V), but the drift moves into the ladder: node d1 12.0 -> 15.4 V in 20 us (ladder_dev_max 5.0 V).
  - So LSCB's "phase shedding" has to mean whole columns of stacked cells, i.e. our modules, not SCB phases.
- **Restart after idle (25 % load):** a module whose Cs drifted delta below nominal restarts with
  - P24 as is: peak 151 / 160 / 188 / 257 A at delta 0 / 1.0 / 2 / 4 V, rails settled after 0 / 2.6 / 4.7 / 6.0 us;
  - 0.7 V diode clamp (drift stopped at 1.70 V): 170 A at delta 4, but the diode then pumps the dead-time current:
    phase-current spread 33.5 % at the end (P24 5 %);
  - switched clamp closed through the idle (Cs held at ladder - Vout = 1.0 V low) and in LS intervals for 20 us:
    157 A, rails within 0.35 V, no settling, spread 5.5 %. It behaves as if the module had not drifted (151 A).
  - Price: the correction at the first LS intervals is a clamp pulse of 190 / 157 / 98 A (resistance-limited, 5 mOhm).
- delta is an assumption: the model has no leakage or driver draw, so it says what a drift costs, not how fast it comes.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | base shed4 rail_dev_max >= 3 V | PASS 14.20 V |
| 2 | actall_c20 shed4 ladder_dev_max >= 1.5 V | PASS 5.03 V |
| 3 | base rs2 peak >= base rs0 + 15 A | PASS +37.3 A (187.9 vs 150.6 A) |
| 4 | act_c20 rs4 rail_dev <= base rs0 + 0.5 V and peak <= base rsv + 5 A | PASS 0.36 <= 0.66 V; 156.8 <= 164.7 A |
| 5 | d07_c20 rs4 peak <= base rs4 - 15 A | PASS 169.8 vs 257.1 A |

Predictions: shedding right in direction and size (rail_dev 14.2 V in the 4-12 V band's upper side, ladder 5.0 V in
2-6 V); restart rs0 151 A (140-170), rsv +9 A (predicted +12-22), rs2 +37 A (25-45), rs4 +107 A (50-90: more than
predicted), d07 87 A below rs4 (30-60: more). Not predicted: the diode's 33.5 % spread at light load.

## 2. Limits
- Open loop, ideal switches, linear Coss, no package or clamp loop inductance; one module; no closed-loop restart.
- The idle clamp's 1.0 V offset (ladder - Vout) is a property of clamping the top node while the switch node rests at
  Vout; LSCB's own extra node does the same.
- The restart starts with every inductor at 0 A into 25 % load; a closed-loop restart would ramp in more gently.
