# A259 - a latched fault trip: under-voltage, a fault level that never suspends, and the average current (RESULTS)
Boundary: e41ee26 (plant cfg "short" bdac50e). Plant V7, one module, 25 C (S75h: slow devices at 125 C). Records:
cosim/run_f_*.json (10 runs) and the arm-d records cosim/run_d_*.json (6 runs, bdac50e), all with
cosim_sources_modified False; release records-a259. Analysis: a259_analyze.py -> a259_summary.json. Figure:
a259_figure.py -> a259_fault_trip.png. Peaks are gate-record turn-off currents (gate_offs_last i_max_a).

## 0. Verdict
- **f1-f4 pass as registered, so the latched fault trip joins the final configuration** (decision rule, Section 4).
  The trip's settings are fault {i_a 220, n 3, uv_v 0.9, uv_ns 400, uv_mask_us 0, iavg_a 350, avg_us 10}.
- **Shorts (0.25 / 1 mOhm from 400 us):** under-voltage trips 0.52 / 0.91 / 0.52 us in (sh025_N75 / sh1_N75 /
  sh025_S75h). That is before the limit would have suspended (2.4-2.5 us), so every short stays under 200 A:
  174.2-175.2 A and V_DS 27.9-30.9 V. Without the trip the same shorts reached 444.8-668.1 A and 53.6-82.0 V.
- **200 % (N75):** Vo never falls below 0.905 V. After the limit suspends at 2.39 us, the fault level cuts nine pulses
  at 264-273 A (283.3 A gate-record), and phase 3's third cut trips at 3.38 us. V_DS is 35.4 V. Without the trip the
  row reached 559.4 A and 58.3 V.
- **150 % (N75 / S75h):** the average trips at 8.79 / 8.78 us. Until then the peaks are what the final configuration
  gives, 227.7 / 258.6 A.
- **After the shutdown:** every phase current falls below 5 A within 0.10-0.20 us through the low sides' reverse
  conduction, and V_DS stays at or below 22.5 V. With every switch off, the ladder holds where the trip left it:
  0.39-0.64 V off on five rows and 2.76 V after 200 %.
- **The legit rows closest to each detector never trip and equal the final configuration bit for bit:**
  a_S75h_d2 (211.8 A), p_N75_60k (Vo 0.958 V), o125_S75h (125 %) and pr_N75.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| f0 | tests 706, regression quick + full | pass (tmp/logs/a259_{tests,reg_quick,reg_full}.log) |
| f1 | every FAULT row trips; the shorts by under-voltage before the limit suspends | pass: uv / uv / uv, peak, avg, avg; no suspension on the shorts |
| f2 | V_DS <= 40 V and peak <= 300 A; the shorts <= 200 A | pass: <= 35.4 V; 283.3 A; shorts 174.2-175.2 A |
| f3 | from 2 us after the shutdown, every phase current within +-5 A | pass (<= 0.0014 A) |
| f4 | IDENT rows never trip and equal their records | pass, bit for bit |

## 2. Predictions against the records
- **Shorts:** under-voltage at 0.6 / 1.0 / 0.9 us was predicted; it tripped at 0.52 / 0.91 / 0.52 us. The prediction
  read Vo at phase 1's sections, which come every 0.4 us. The detector sees every 4 ns window, so on S75h it saw the
  crossing 0.35 us earlier. Peaks were predicted at 176-179 A and came in at 174.2-175.2 A.
- **ov200_N75:** the prediction was cuts at 275-290 A and a trip about 1 us after the suspension. The records show
  264-273 A at the cut, 283.3 A gate-record, and the trip at 3.38 us. Yes on both counts.
- **ov150: the prediction was wrong.** It said the count would trip about 1 us after the first pulse over 220 A. In
  fact the pulses over 220 A (2 on N75, 7 on S75h, at most 3 per phase) alternate with clean ones, so the up/down
  count never reaches 3, and the average trips at 8.8 us. The peaks stayed under the predicted 260 A (227.7 /
  258.6 A).
- **After the trip:** the currents were predicted to fall within about 0.2 us, and they fell in 0.10-0.20 us. The
  ladder was predicted to hold within about 1 V of its state at the trip. The current's decay moves it by -0.15 to
  +0.07 V. From 0.5 us after the shutdown it is constant to 0.001 V over the remaining 21-29 us. After 200 %, though,
  it was already 2.68 V off at the trip (the cut pulses had moved it).

## 3. Limits
- **The trip is latched; nothing restarts.** In this plant the flying capacitors hold their voltages indefinitely,
  because it has no leakage and no bleed. A real off time of milliseconds drifts them, so a restart would need them
  pre-charged first (TPS54A20 charges Ct to Vin / 2 before every start). That restart is stage 2 and was not run.
- **Between the rating and the trip, peaks pass 200 A.** From about 136 % to the trip the converter runs at
  200-259 A: on 150 % for up to 8.8 us, and on 200 % for 1 us at 283 A. The 200 A budget stands for inductor
  saturation, so these are excursions over it before the shutdown.
- **What was run:** one module, the N75 / S75h boards, faults starting from steady full load at 400 us. Not run: N0
  and N13, four modules, faults during the start-up or a transient, shorts between 1 mOhm and 4 mOhm, faults that
  clear, and the 136-150 % band itself.
