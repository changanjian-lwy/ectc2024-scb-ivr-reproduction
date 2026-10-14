# A219 - LSCB's resistor pre-charge on the P24 module: a live 48 V bus, then a soft start (RESULTS)
Boundary: 318881f. Records: release records-a219 (runs/*.json, run log); a219_summary.json. Plant: A180's open-loop
LTspice power stage of one P24 module (ideal switches, linear Coss, no package loop, no controller).

## 0. Verdict (2 of 5 as registered; criteria 4 and 5 missed by a bound set wrong, see Section 1)
- **P24 cannot sit on a live 48 V bus with its switches off:** SH1 settles at 48.0 V (Cs stay at 0, the switch nodes
  follow the 0 V output), above EPC2067's 40 V, for the whole 40 ms.
- **A switched 4 x 1 kOhm divider with diodes (LSCB's idea without the ladder):**
  - on a 20 ms bus ramp: SH1 23.7 V at most, Cs end 0.88-0.95 V below nominal; the divider lags the ramp by about
    tau x slope (tau ~5 ms), so 16 V would need a ~3x slower ramp or a smaller resistor;
  - on a 10 us edge: SH1 47.9 V, above 40 V for 1.2 ms. The divider alone does not protect a hot-plug edge.
- **With the capacitor ladder (4 x 20 uF) as well:** on the 10 us edge SH1 21.4 V at most (vs 48 V); the string
  divides the edge and the diodes share charge into Cs. Cs then sit 2.3-3.2 V low after 40 ms (slow rebalancing).
- **Soft start from the pre-charged state** (on-time 1 ns -> ton0 over 137 us at 48 V) against P24's own start (Vin
  ramps while switching, A180's su row): peak 147 vs 169 A, rails at the end 0.11 vs 0.56 V off, switch voltages the
  same (SH1 15.0 vs 14.9 V; SH2-SH4 24.9 vs 24.8 V).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| 1 | base pre_slow SH1 >= 40 V | PASS 47.96 V |
| 2 | rdiv_pc pre_slow: every switch <= 16 V and Cs within 1.0 V | FAIL 23.7 V (Cs 0.95 V: pass) |
| 3 | rdiv_pc pre_fast SH1 >= 40 V | PASS 47.94 V |
| 4 | lad_pc pre_fast every switch <= 20 V | FAIL 21.4 V |
| 5 | soft from rdiv: peak <= su + 10 A and every switch <= 16 V | FAIL on the switches: 24.9 V; peak 146.9 <= 179.3 A |
- 2: the predicted 12.5-15 V ignored the divider's lag behind the ramp.
- 4: missed by 1.4 V; the ladder still keeps SH1 at 45 % of the unprotected 48 V.
- 5: the bound was wrong. SH2-SH4 block up to 2 Vin / 4 = 24 V in normal SCB operation (the paper's Fig. 1), which
  P24's own start shows too (24.8 V). Like for like, the pre-charged start matches P24's switch voltages.

## 2. Limits
- No breakdown physics, no package loop (V_DS ringing), no gate-drive supply at start-up, no MLCC DC-bias derating.
- The 20 ms ramp and 1 kOhm are our choices; the lag scales with R x C x the ramp's slope.
- Open-loop soft start at full load; a controller and the cosim's mode S are not in this plant.
