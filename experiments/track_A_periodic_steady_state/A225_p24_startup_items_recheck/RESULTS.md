# A225 - controller items 2, 5 and 6 on the candidate configuration (RESULTS)
Boundary: 3341c47. Records: release records-a225 (14 cosim records, logs). Analysis: a225_analyze.py ->
a225_summary.json. Runs from 3341c47, cosim_sources_modified False. Candidate = plant V7, A222's trims, vff rel_gate 25,
kd 355 ns/V (dead band 2, held at the lower limit), skipping; one module. A227 did not adopt the candidate, so the
a and u rows are stated for the candidate; the s rows do not depend on it (gate and kd are inert in steady state).

## 0. Verdict
- **Item 5 closes on V7**: the slow board's two-cycle orbit is gone - mean |valley change| per period 0.04 A at 100 %
  and 0.04-0.25 A at 50 % (V6, A211: 4.2-5.1 and 5.1-7.7 A), and with half the core's damping (rc2) 0.27-0.38 /
  0.05-0.10 A. The orbit belonged to plants V2-V6, which had no damping in the core (records cosim/run_s_S75_*.json).
  Seen on the way, not traced: at 50 % phases 3 and 4 settle with valleys of -33.9 / -33.1 A (rc2: -31.0 / -15.7 A)
  against -15.6 A on phases 1-2.
- **Item 2 stays on the hot slow board**: +4.8 V / 1 us 2 / 10 / 20 us after the entry gives 211.2 / 210.3 / 207.8 A
  on S75 at 125 C (A198 on V5: 202.8 / 214.4 / 217.3 A); at 25 C 199.6 / 197.0 / 190.3 A (195.5 / 197.6 / 206.1) and
  N0 at 2 us 182.8 A (193.7) pass. The 40 us hold-off stays for slow boards.
- **Item 6 narrows**: N0 into 30 % reaches 1.0510 V (A214 on V6: 1.0528 V; limit 1.05 V), 1.0 mV over; S75 into 30 %
  at 25 / 125 C passes (1.0483 / 1.0491 V, handover requested at 99.4 / 95.6 us with Vin at 34.8 / 33.4 V).

## 1. Criteria
| row | result |
|---|---|
| a_S75h_d2 / d10 / d20 (f2) | **211.2 / 210.3 / 207.8 A - miss** |
| a_S75_d2 / d10 / d20 (f2) | 199.6 / 197.0 / 190.3 A - pass |
| a_N0_d2 (f2) | 182.8 A - pass |
| u_N0_30 (f6) | **Vo 1.0510 V - miss**; peaks 81.1 / 109.0 A |
| u_S75_30 / u_S75h_30 (f6) | Vo 1.0483 / 1.0491 V, peaks <= 115.0 A - pass |
| s_S75_100 / _50 / _100_rc2 / _50_rc2 (f5) | 0.04 / 0.25 / 0.38 / 0.10 A worst phase - pass |
- No overlap or shoot-through; late fires after the hot steps 4-102.

## 2. Limits
- One module, A198's instants only, 25 / 125 C; the a and u rows ran on the candidate, not the final configuration.
