# A172 - the final gate-level plant: L x 0.7 re-trimmed and four modules (RESULTS)
Boundary: 41e0b51. Records: release records-a172 (run_*.json, run log). Analysis: a172_analyze.py -> a172_summary.json.

## 0. Verdict
- **PASS, 2 of 2.** The package spec is A167's drive with gate-driven low sides and a threshold-form driver
  interlock:
  - 50 pH; 3.0 / 0.3 ohm per device +-20 %;
  - 8 ns lead ramped over 20 us after the handover;
  - per-board start-up trim;
  - low-side sink <= 0.3 ohm;
  - a turn-on's channel waits until the complement stops, <= 0.5 ns.
  The interlock item closes without an RTL change.
- L x 0.7, re-trimmed under this plant (ton 34.813 -> 35.769 ns):
  - Vo(143.5 us) 1.041 V;
  - mode S start-up 200.2 A (ref 202.5 A); handover 190.2 A;
  - post-step 199.7 A, 2 late fires, Vo -8.6 mV; 2 holds <= 0.6 ns.
  - The post-step peak is 0.3 A under the 200 A budget. It is the thinnest margin in the spec.
- Four modules, nominal +4.8 V / 1 us: 33.8 V; start-up 162.1 A, handover 149.7 A, post-step 184.2 A (A164 182.6 A);
  0 late fires, 0 holds, edge power 2.87 W per module.
- Mode S's predicted 202-206 A came out at 200.2 A: the longer trim is offset by the low-side gates.

## 1. Criteria
| row | 1 V_DS | 2 start / Vo | 3 post / late / shoot | 4 Vo |
|---|---|---|---|---|
| nom L07_l_p48_1us | 32.4 V | 200.2 A (<= 205.5) / 1.041 V | 199.7 A, 2, 0 | -8.6 mV |
| m4 nom l_p48_1us | 33.8 V | 162.1 A / 1.032 V | 184.2 A, 0, 0 | (not applied) |

## 2. Limits
- One row each. The four-module system was run at the nominal corner only. Its corners (slow, L x 0.7) rest on the
  single-module rows of A171 / A172.
- The interlock is ideal sensing plus a fixed 0.5 ns, as in A171.
