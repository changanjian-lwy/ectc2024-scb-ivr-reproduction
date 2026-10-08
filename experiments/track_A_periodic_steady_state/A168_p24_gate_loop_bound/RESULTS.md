# A168 - the power-loop bound under the adopted gate drive (RESULTS)
Boundary: 168163a, amended df73fcc. Stage 1b (secant trims): 6819178. Records: release records-a168 (run_*.json,
start-up runs, logs). Analysis: a168_analyze.py -> a168_summary.json.

## 0. Verdict
- **The loop bound is 50 pH. 60 pH is marginal and 75 pH does not work with resistors.** As registered:
  - P60 misses criterion 1 only, by 0.3 V;
  - Q60 does not pass cleanly;
  - Q75 misses on timing and Vo.
  The spec's "~50-60 pH" becomes "<= 50 pH".
- **P60 (60 pH, 3.0 ohm):**
  - the fast corner reaches 40.3 V after +4.8 V / 1 us (predicted 40.0 V, 39.3-40.7);
  - nom, L x 0.7 (handover 196.7 A, post-step 199.3 A) and the slow corner (261 late, ref 260) pass.
- **Q60 (60 pH, 3.5 ohm):**
  - the fast corner holds at 38.1 V;
  - slow corner (4.2 ohm): s_p62 passes; l_p48_1us has 19 NEW one-period spikes (limit 11) and 376 late fires
    (ref 260);
  - L x 0.7 shot through at 152.5 us. With A171's interlock it completes, but its handover is 202.0 A and Vo
    11.5 mV / 35.6 us.
- **Q75 (75 pH, 4.0 ohm):**
  - V_DS holds (38.6 V);
  - nom's line step loses Vo (12.6 mV, 46.1 us back; ref 8.5 mV);
  - slow corner (4.8 ohm): 577 / 299 late fires and 68 / 39 NEW events;
  - L x 0.7 shot through; with A171's interlock its mode-S start-up reaches 212.9 A.
- Edge power per module rises with the resistor: nom 2.55 / 2.57 / 2.83 W at 50 / 60 / 75 pH; slow corner 4.72 /
  4.92 / 5.19 / 6.29 W (50 / P60 / Q60 / Q75).
- L x 0.7 shoot-throughs at Q60 / Q75 found the interlock gap that A169-A171 then closed. The bound itself does not
  rest on them.

## 1. Criteria (misses)
| run | 1 V_DS | 2 start / Vo | 3 post / late / NEW | 4 Vo |
|---|---|---|---|---|
| P60 ff / nom / L07 / ss | **40.3** / 35.3 / 34.3 / 31.2 V | ok | ok | ok |
| Q60 ff | 38.1 V | ok | ok | ok |
| Q60 ss l_p48_1us / s_p62 | 30.7 V | ok | **NEW 19** / ok | ok |
| Q60 L07 | - | (213.6 A) | **OVERLAP_STOP 152.5 us** | - |
| Q75 ff / nom | 38.6 / 33.5 V | ok | ok | ok / **12.6 mV, 46.1 us** |
| Q75 ss l_p48_1us / s_p62 | 31.4 V | ok | **late 577, NEW 68 / late 299, NEW 39** | ok |
| Q75 L07 | - | (217.9 A) | **OVERLAP_STOP 153.3 us** | - |

## 2. Limits
- The low sides keep ideal edges here (A168 was registered before A169). A171 / A172 carry the final plant.
- Four modules and the hot corner were not run at 60 / 75 pH.
- The slow corner's first start-up at 4.2 / 4.8 ohm fell below A163's ~0.99 V cliff (0.994 / 0.950 V). A second
  start-up and a secant trim brought it in (1.035-1.036 V); the slope was 0.028 V/ns.
