# A191 - a 9.5 ns high-side lead against the slow corner's post-step valley loss (RESULTS)
Boundary: cc43732. Records: release records-a191 (12 runs, log). Analysis: a191_analyze.py -> a191_summary.json
(A187 alongside). Code cfe581f, plant V5, t_il 1.0 ns, A186's start-up; only the lead differs from A187.

## 0. Verdict
- **PASS: both boards hold 200 A at 125 C at all six step positions.**
  - S75 (L x 0.75): post-step 194.1-196.9 A (A187: 194.9-207.2 A).
  - S80 (L x 0.8): 190.6-192.8 A (A187: 190.8-217.1 A).
  - The step phases spread over the whole period (S75 0.09-0.93, S80 0.16-0.99).
  - c1 / c3 / c7 pass everywhere: start-up 134-138 A, handover 185.4-188.5 A, V_DS <= 33.6 V, 0 shoot-throughs.
- **The lead removes the late fires, and with them the excursion.** Late fires on phases 3-4 in the first 30 us after
  the step fell from 28-65 to 1-10 (-90 %). The post-step Vo minimum is unchanged (0.982-0.986 V against 0.980-0.987
  V), so the dip is the step's normal response. What pushed the peak over 200 A was the valley loss: phase 4 at
  -80..-90 A, then a recovering valley meeting the raised Ton (A187).
- Why 1.5 ns matters: the predictive turn-on is late once the gate delay beyond the lead exceeds ~5.5 ns (A163). The
  slow corner's delay sits just above that with 8 ns and just below it with 9.5 ns. The bridge allows leads up to
  t_drv = 10 ns, so there is ~0.5 ns of room left.
- Predictions: late fires -50 % or more: right (-90 %). Post-step <= 200 A everywhere: right. Vo minima >= 0.988 V:
  wrong (0.982-0.986; the dip does not come from the late fires).

## 1. Criteria
| board | step phases | c1 start / hand | c2 post-step (A187) | c3 | c7 |
|---|---|---|---|---|---|
| S75 | 0.60 / 0.76 / 0.93 / 0.09 / 0.26 / 0.42 | 137.5 / 188.5 | 196.9 / 194.2 / 196.1 / 194.1 / 195.4 / 194.1 (max 207.2) | <= 33.6 V | PASS |
| S80 | 0.83 / 0.99 / 0.16 / 0.32 / 0.49 / 0.66 | 134.3 / 185.4 | 190.6 / 192.8 / 191.7 / 190.8 / 191.5 / 190.7 (max 217.1) | <= 32.1 V | PASS |

## 2. Limits
- One row (+4.8 V / 1 us) at 125 C. The slow corner's other rows (-8 V / 10 us, the load step, falling steps), 25 C,
  four modules and the nominal / ff corners were not run with 9.5 ns.
- The lead is a controller-side timing (bridge-modelled faster turn-on path). Its hardware form must reach the
  plant 9.5 ns ahead of the other edges.

## 3. Decision (BOUNDARY Section 4)
Both boards hold, so a 9.5 ns lead for slow boards (read from the 25 C trim) is the candidate. A192 checks the slow
corner's other rows and 25 C with it before adoption.
