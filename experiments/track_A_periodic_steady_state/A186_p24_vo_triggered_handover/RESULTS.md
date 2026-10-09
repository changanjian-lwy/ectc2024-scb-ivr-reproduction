# A186 - the handover requested on Vo at 1.03 V (RESULTS)
Boundary: 59c3f07, decision rule amended before any result 0e03bd9. Code 352828c for the 11 single-module runs. The
four-module run failed at t = 0 on a bridge defect (the shared latch was read before ModuleSim.start() created it),
was fixed in cfe581f and rerun; with cfe581f, A185's four-module cfg reproduces A185 up to 150 us in all four modules.
Records: release records-a186. Analysis: a186_analyze.py -> a186_summary.json.

## 0. Verdict
- **FAIL as registered; not adopted at 1.03 V** (amended rule: harm at 25 C).
  - N13's 25 C minimum fell 18 mV below A185's (0.982 vs 1.000 V), and its Vo(143.5 us) = 0.982 V fails c4.
  - S75 25 C settles 2.34 A off its t0 = 400 record (c5).
- **Hot, the request does what it is for.** The start-up overshoot is gone: Vo maximum 1.031-1.035 V everywhere
  (A185 hot: 1.126-1.130 V on the slow boards). Hot handover minima 0.992-0.999 V (A185: S75 0.977, S0 0.991). S0 /
  S75 hand over at 130.0 / 129.6 us at Vin 45.6 / 45.4 V. Handover <= 187.5 A, post-step S75 197.2 A, V_DS <= 33.7
  V, 0 shoot-throughs.
- **At 25 C, 1.03 V is too low.** The trimmed boards reach it at 139.6-141.4 us, while Vo is still rising (N13:
  +5.3 mV/us, valleys 57 / 52 / 44 / 41 A against 41-45 A at 144 us). Mode P then has a larger current gap to
  close, and N13 dips to 0.982 V. The request level has to sit above the 25 C start-up: A188 (1.045 V).
- **c5 at S75 25 C is the controller's learned valley, not the start-up.** Steady peaks at 300-495 us are flat in
  every run, but settle at 145.1 / 145.3 / 146.3 / 147.3 A in A181 / A184 / A185 / A186, with valleys -13.5 /
  -13.8 / -15.1 / -16.3 A. Vo is 1.000 V and Ton 32.3-32.5 ns in all four. A143 records the floor's
  history-dependent 2-4.5 A valley spread. +-2 A was tighter than that.
- Other c6 misses (by <= 2 mV): four modules 0.993 V (ref 0.998), N0 125 C 0.992 V (ref 0.999), F0 0.993 V (ref 0.998).

## 1. Criteria
| run | g0 | c1 start / hand | c2 | c3 V_DS | c4 | c5 dev | c6 min (ref) | c7 Vo max |
|---|---|---|---|---|---|---|---|---|
| S75 25 C | = | 135.7 / 158.8 | 192.4 | 33.1 | 1.015 | **2.34** | 1.000 (0.961) | 1.031 |
| N0 / N75 / N07 / S0 25 C | = | <= 139.9 / <= 178.6 | N0 181.1 | <= 33.7 | 0.998-1.015 | <= 0.25 | 0.997 / 1.000 / 1.000 / 0.997 | <= 1.031 |
| N13 25 C | = | 116.5 / 176.4 | - | 30.8 | **0.982** | 0.07 | 0.982 (0.984; **A185 1.000**) | 1.035 |
| F0 25 C | = | 125.0 / 164.7 | - | 32.3 | 1.000 | 0.09 | **0.993** (0.998) | 1.031 |
| four modules 25 C | = | 124.7 / <= 167.6 | - | <= 30.5 | 0.999-1.000 | <= 0.30 | **0.993** (0.998) | 1.031 |
| S75 / S0 / N0 / F0 125 C | = / = / = / - | <= 137.5 / <= 187.5 | S75 197.2 | <= 33.1 | 1.001-1.007 | <= 0.17 | 0.996 / 0.999 / **0.992** / 0.992 | <= 1.033 |

## 2. Predictions
- Requests "25 C at 142-144 us": earlier (139.6-141.4 us). "S0 / S75 hot ~125 us at 43.5-44 V": 130 us at 45.5 V.
- c7 everywhere: right. Hot minima >= 0.99 V: right. Handover <= 190 A: right (187.5). "25 C within +-3 mV of
  A185": wrong for N13 (-18 mV) and N0 (+6 mV).

## 3. Limits
One row (+4.8 V / 1 us) on three boards. The 1.03 V level was not varied here (A188).

## 4. Decision
Not adopted at 1.03 V. A188 places the request above the 25 C start-up (1.045 V) and keeps the hot fix.
