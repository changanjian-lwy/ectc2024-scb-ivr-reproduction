# A159 - the adopted spec at the recommended loop bound (150 pH), on A152's robustness matrix (RESULTS)
Boundary: 1be4a9b. Records: release records-a159 (14 runs). Outputs: a159_summary.json (a159_analyze.py), a159_predictions.json.

## 0. Verdict
- **2/5 as registered (1, 2 pass; 3, 4, 5 fail). By the registered rule the recommended loop bound comes down from
  ~150 pH to 125 pH** (the largest L that passed voltage, start-up, Vo and four modules: A156; 100 pH: A152 S100).
- **Voltage is not the limit at 150 pH:** every row and four modules <= 38.0 V (x_on 1.8 V, turn-off 72 A/ns at x_off
  10.8 V). Start-up 155-165 A (L x 0.7 199 A, its ideal reference 200 A).
- **The slow turn-on starts to cost regulation.** To keep x_on 1.8 V at 150 pH the turn-on is 12 A/ns, and:
  - the +62.5 A load-step dip is -16.1 mV (ideal -11.9, S100 at 18 A/ns -14.9): criterion 4 misses by 0.2 mV;
  - +4.8 V over 10 us is back within 1 % after 46.2 us (ideal 43.1, S100 40.5): misses by 1.1 us;
  - late fires on -8 V / 10 us: 33 (predicted 20-45; 0 / 6 / 16 at 50 / 100 / 125 pH).
  So at large L two limits meet: the overshoot wants a slower turn-on (di/dt <= x / L), the transient response a faster
  one. 150 pH is where they start to collide.
- **Criteria 3 / 5's NEW events are the oracle's K4-window artefact again:** phase 1's post-step swing peak at
  +1.13 / +1.49 us after the ramp (single module) and +1.01-1.11 us (four modules, all four masters' phase 1), 168-176 A,
  each just outside the K4 window (ramp + 1 us); the slower turn-on delays the swing more (A154 / A158: +1.05-1.16 us).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | V_DS <= 40 V, 13 rows | PASS (<= 38.0 V) |
| 2 | start-up <= max(200, ref + 5) A | PASS (155-199 A) |
| 3 | post-step, 0 NEW, late <= ref + 2 | FAIL: l_m80_10us late 33; l_p48_1us / L13_l_p48_1us one K4-timing spike each |
| 4 | Vo extreme / back | FAIL: s_p62 -16.1 mV (ref -11.9 + 4); slew10 back 46.2 us (ref 43.1 + 2) |
| 5 | four modules, criteria 1-3 | FAIL: 4 K4-timing spikes (one per module at the step); 36.4 V, 157 / 176 A, late 0 |

## 2. Limits
- One point at 150 pH (x_on 1.8 V); a faster turn-on at 150 pH (x_on 3.0 V, 20 A/ns) was not run: it may restore the
  Vo criteria at the cost of V_DS near 39.5 V (A156's corner value at 125 pH).
- The oracle's K4 window (ramp + 1 us) is now the recurring source of NEW flags under slow turn-ons (A154, A158, A159).
