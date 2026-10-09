# A178 - where the final plant's 200 A budget holds in inductance (RESULTS)
Boundary: 1a4b4d1 (stage-2 cfgs and trims 0788914). Records: release records-a178 (run_*.json, run logs).
Analysis: a178_analyze.py -> a178_summary.json. All runs from committed code.

## 0. Verdict
- **Inductance ≥ 0.75 L0 keeps the final plant ≤ 200 A at every tested step phase.** After +4.8 V / 1 us:
  - L × 0.75: 195.4-198.3 A over five phases (max 198.3 A);
  - L × 0.8: 191.9-194.7 A;
  - L × 0.7 (A172 / A174): 199.5-201.5 A.
  The spec states: −25 % holds with 1.7 A to spare at the worst sampled phase; −30 % reaches 201.5 A.
- All 10 runs pass every criterion. V_DS <= 33.5 V. Start-up / handover 191.1 / 182.1 A (L × 0.75) and 183.7 /
  167.8 A (L × 0.8). Late <= 1, 0 NEW, 0 shoot-throughs, interlock holds <= 3 per run.
- One-shot trims under the final plant: 36.379 / 37.158 ns (first guesses 36.410 / 37.051; Vo(143.5 us) 1.036 /
  1.032 V at the guesses).
- The phase spread is 2.9 A (L × 0.75) and 2.8 A (L × 0.8), against 2.0 A at L × 0.7. It sits at the low end of
  A129's 2-7 A.

## 1. Criteria
| board | 1 V_DS | 2 Vo(143.5) / start / hand | 3 post (5 phases) / late / NEW | 4 Vo back | result |
|---|---|---|---|---|---|
| L × 0.75 (ton 36.379) | 32.4-33.1 V | 1.035 / 191.1 / 182.1 | 195.4, 198.0, 197.4, 198.3, 198.0 A / <= 1 / 0 | within 1 % throughout (|Vo| <= 9.6 mV) | PASS (5 / 5) |
| L × 0.8 (ton 37.158) | 32.5-33.5 V | 1.035 / 183.7 / 167.8 | 194.7, 192.9, 194.0, 194.6, 191.9 A / 0 / 0 | back (10.4 / 10.1 mV at sh0 / sh2) | PASS (5 / 5) |

Predictions: L × 0.75 max 196-200 A, L × 0.8 192-197 A, start-up 180-195 A, trims within 0.5 ns of the guess - all
right.
Analysis note: a first pass flagged criterion 4 on runs whose Vo never left 1 %. Their recovery time is 0.0, and
`x or inf` read it as missing. The check now tests for None; A173's analysis had the same expression, and its
summary regenerates unchanged.

## 2. Limits
- Five phases per board; the maximum over all phases may be higher.
- Nominal devices and one row (+4.8 V / 1 us, the worst post-step row at L × 0.7). Other corners combined with an
  inductance spread are not run.
