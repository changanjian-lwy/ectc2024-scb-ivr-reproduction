# A171 - the driver interlock in threshold form (RESULTS)
Boundary: 497a21a (interlock 0c60feb). Records: release records-a171 (run_*.json, run log).
Analysis: a171_analyze.py -> a171_summary.json (A170's run of the same name alongside).

## 0. Verdict
- **S50: 4 of 5 rows pass. L x 0.7 misses only Vo(143.5 us), 1.010 V.** That is a trim artefact: A164's trim was
  set with ideal low sides. With 0.5 and 1.0 ns, every peak, late-fire and Vo-regulation criterion holds there.
  A172 re-trims that board under this plant and adds four modules.
- The threshold form blocks only what it must:
  - nom / ff / hot have 0 holds and equal A169 (no interlock). nom: post-step 182.5 A, Vo 8.4 mV; A170's gate form
    had 187.6 A and 12.6 mV / 45.5 us.
  - L x 0.7: 10 holds <= 1.6 ns. Handover 187.3 A, post-step 199.2 A, late 4, Vo -9.9 mV (A170: 214.3 A, late 64).
  - Slow corner: 84 holds <= 2.6 ns, 194 late fires (A167 260, A170 4906), post-step 178.7 A.
- 0 shoot-throughs in all eight runs. Phase-4 dt_pred no longer collapses after the L x 0.7 handover: 11.3 ns at
  165 us, against 1.5 ns in A170 and 2.5 ns in A169.
- t_il 1.0 ns: as 0.5 ns within 0.1 A, holds <= 2.1 ns.
- Q60 / Q75 L x 0.7 (A168's configurations) no longer shoot through. They miss as A168 found:
  - Q60: handover 202.0 A, Vo 11.5 mV / 35.6 us;
  - Q75: start-up 212.9 A, NEW 48, late 15.
  Both also miss the Vo(143.5) trim check (1.006 / 1.011 V).

## 1. Criteria (misses)
| run | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| S50 nom / ff / hot / ss | 33.7 / 38.4 / 32.6 / 31.2 V | ok | ok | ok |
| S50 L07, S50t1 L07 | 32.3 / 33.1 V | **Vo 1.010 V** | ok (199.2 / 199.3 A, late 4) | ok |
| Q60 L07 | 32.4 V | **Vo 1.006 V, handover 202.0 A** | ok | **11.5 mV, 35.6 us** |
| Q75 L07 | 33.7 V | **Vo 1.011 V, start 212.9 A** | **NEW 48, late 15** | ok |

## 2. Limits
- The interlock senses the complement's channel current and its own activation level ideally, then adds t_il. A
  real driver compares gate voltages to references; the reference margin is not modelled.
- The low side's turn-on uses the high side's 3.0 ohm. Start-up hard low-side turn-ons only.
