# A113 - phase 1's turn-off following Ton in the 25% design (RESULTS)

Track A.

**Boundary:** `BOUNDARY.md`, committed (5c6528e) before any run.

**Records:** `cosim/run_*.json`; `a113_summary.json`
(`a113_analyze.py`).

**Physical model:** as A112 (Verilog RTL, A88 kernel2 plant, A105's I2
with `slot_lo`, 25% negative-current target, 25 C).

## 0. Verdict

| option | n0 efficiency, high side | −62.5 A load step | −4.8 V / 1 µs | −8 V / 10 µs |
|---|---|---|---|---|
| A112 p25 (timed, no feed-forward) | 90.14%, −0.16 to +0.86 V | −14.95 mV, 183 µs | −34.0 mV, 182 µs, 220 A | −17.1 mV, 162 µs |
| **ff** (dlo feed-forward k = 11) | 90.14%, −0.19 to +0.88 V | **+16.90 mV, 8.9 µs** | **−96.5 mV**, 47 µs, **234 A** | **−147.5 mV, not recovered**, 211 A |
| **cmp** (comparator turn-off, I1) | 90.15%, −0.13 to +0.88 V | **+16.89 mV, 8.9 µs** | **+15.84 mV, 2.8 µs**, 199 A | −24.9 mV, 175 µs |

1. **The feed-forward is falsified for line steps.**
   - When the input moves, the loop changes Ton to hold the current.
     The on-low interval the turn-off needs, (V_rail − Vo) Ton / Vo,
     then hardly changes.
   - A fixed 11 LSB per LSB of Ton drives dlo far off, and the
     valleys with it.
   - It fixes the load step, where the rail is constant.
2. **The comparator turn-off fixes the load step and the fast falling
   line step** without costing the steady state:
   - efficiency 90.15%;
   - the high side −0.13 to +0.88 V;
   - spread 0.12-0.19 A at 0 ps.
   - **Not fixed:** the −8 V / 10 µs step (to 40 V, −17%) still settles
     in 175 µs. A different mechanism, not phase 1's turn-off, as cmp
     tracks the crossing physically.
3. **The load-step overshoot is +16.9 mV in both:** +45% against the 5%
   design's +11.65 mV (registered ±30%: a miss), with recovery in
   8.9 µs.

## 1. Registered criteria (BOUNDARY Section 2)

| run | result |
|---|---|
| ff_n0, cmp_n0 | pass |
| ff_s_m62, cmp_s_m62 | back pass (8.9 µs); **overshoot +16.9 mV against ±30% of 11.65: miss** |
| ff_l_m48_1us | **miss:** back 47 µs, peak 234 A |
| ff_l_m80_10us | **miss:** not recovered, peak 211 A |
| cmp_l_m48_1us | pass (2.8 µs, 199 A) |
| cmp_l_m80_10us | **miss:** back 175 µs, peak 197.9 A against A112's 193.6 |

## 2. Next

**A114:** the 25% design with the comparator turn-off (and 20% for
comparison) through the whole standard matrix. Its jitter rows decide
the comparator's timing cost. A105 found I1 7-13% noisier than I2 at
30 ps.
