# D79 - the gate drive in resistors: EPC2067's gate in the plant, checked against LTspice with EPC's own model

2026-10-07. Code: `src/scb_ivr/p24_gate_model.py` (device), `src/scb_ivr/cosim/gate.py` (the plant's gate-driven
edges, cfg "gate"), `scripts/p24_ltspice.py` (LTspice in batch), `scripts/p24_gate_edges.py` →
`diagnostics/D79_gate_validation.json`, `D79_gate_sweep.json`, `D79_gate_candidates.json`, `D79_dvdt.json`,
`D79_mismatch_gate_loop.json`.
Vendor model: EPC GaN library (EPC2067 entry, 2021-10-18), kept **outside** the repository (`vendor_models/` next
to it, or `SCB_EPC_LIB`); `tests/test_p24_gate_model.py` skips without it. System test: A163.

## 1. Why

D68 and A151-A162 state the package drive as current ramps (turn-on di/dt ≤ 3.0-3.2 V / L, turn-off 72 A/ns) and
D69 turned them into resistors by estimate. A ramp has no gate: no delay before threshold, no Miller plateau, no
channel saturation, no common-source inductance, no threshold spread. Mihai's first question is what the driver
must do. This note puts EPC's device model into the plant's edges, checks it twice (datasheet, LTspice), and
restates the drive in resistances.

## 2. The device model

EPC's published form: channel A1·ln(1 + e^((v_gs − k2)/k3))·v_ds / (1 + (x0 + x1·v_gs)·v_ds) (mirrored for
v_ds < 0), charge-defined C_GS / C_GD / C_SD (softplus sums), R_G 0.3 Ω, series rd / rs, temperature factors.
Evaluated in Python on the datasheet's tests (typical, 25 °C):

| quantity | datasheet | model | | quantity | datasheet | model |
|---|---|---|---|---|---|---|
| C_ISS (20 V) | 2178 pF | 2179 pF | | Q_G (20 V, 37 A, 5 V) | 17.1 nC | 17.2 nC |
| C_RSS | 24 pF | 23.5 pF | | Q_GS | 5.3 nC | 5.26 nC |
| C_OSS | 1071 pF | 1071 pF | | Q_GD | 2.0 nC | 2.16 nC |
| Q_OSS (20 V) | 37 nC | 37.2 nC | | Q_G(TH) | 4.2 nC | 3.97 nC |
| R_DS(on) (5 V, 37 A) | 1.3 (max 1.55) mΩ | 1.28 mΩ | | plateau | ~2.3 V | 2.27 V |

Transfer at V_DS 3 V: 58 A at 2.4 V, 188 A at 3.0 V (Fig. 2's typical curve). Its V_GS(TH) at 18 mA is 1.51 V
against the datasheet's 0.7 / 1.0 / 2.5 V: the model is the typical transfer curve, so the spread below shifts it
by −0.3 / +1.5 V. Its C_OSS(V) equals the plant's digitised curve (A59) within 1 % from 0.5 to 40 V.

**LTspice pitfalls (for anyone rerunning EPC models):** with its default charge tolerance LTspice integrates the
charge-defined capacitances badly (the datasheet gate-charge test gives Q_G 14.4 nC; 10.2 nC with 0.1 ns steps);
reltol 1e-5 / chgtol 1e-17 gives 17.23 nC. Under `uic` it starts charge-defined capacitors uncharged whatever
`.ic` says (a node then jumps by volts at t = 0+); the edge netlists hold every node, the devices' internal
ones included, for 0.2 ns instead. The vendor subcircuit is flattened at run time so internal nodes can be held.

## 3. The plant's gate-driven edges (gate.py)

Each high-side device has its own resistor to a 5 V / 0 V driver (r_on / r_off, external plus driver) in series
with R_G; a common-source inductance L_cs per device couples the terminal current into the gate loop. A command
starts the gate moving and the switch follows it physically:
- hard turn-on: open while the gate charges, integrated after every plant step with the step's V_DS (the Miller
  charge counts); active once the channel carries 10 mA per device at max(V_DS, 0.2 V); conducting at V_DS ≤ 0.2 V;
- turn-off with forward current: conducting while the gate falls, until the channel needs 0.2 V to carry the current;
  then active; open when the channel carries < 10 mA;
- active switches are open in the matrix; channel current and gate charge are solved with the plant state by Newton
  per step (trapezoid, Euler after topology changes). Zero-voltage turn-ons and reverse-current turn-offs are
  instantaneous, as before. Off (`gate` absent): bit-identical (cosim_regression --quick 4/4; A152 s50_s_p62 rerun,
  388 sections equal).
- The bridge takes a hard turn-on's valley measurement when its channel starts to conduct (cfg "meas" "act", the
  instant a switch-node detector would see) instead of at the gate command ("cmd"); otherwise the controller learns
  to put the *command* on the valley and the physical turn-on lands a gate delay late.

**Check against LTspice** (A145's single-edge state; in LTspice every one of the 20 devices is EPC's model):

| edge | L pH | R Ω | state | delay ns | t50 ns | peak V | energy nJ |
|---|---|---|---|---|---|---|---|
| on | 50 | 4.5 | 3.8 V | 3.43 / 3.39 | 8.40 / 8.35 | 24.9 / 24.8 | 696 / 691 |
| on | 50 | 4.5 | 12 V | 3.72 / 3.72 | 7.98 / 7.99 | 24.5 / 24.5 | 850 / 851 |
| on | 125 | 10 | 12 V | 8.11 / 8.11 | 15.9 / 16.0 | 23.7 / 23.6 | 781 / 783 |
| on | 150 | 7 | 17 V (52.8 V in) | 5.58 / 5.58 | 11.4 / 11.5 | 29.3 / 29.1 | 1513 / 1516 |
| off | 50 | 1.2 | 143 A | 2.70 / 2.80 | 4.84 / 4.77 | 21.4 / 21.6 | 1257 / 1317 |
| off | 150 | 1.2 | 200 A | 2.25 / 2.32 | 4.46 / 4.39 | 42.2 / 42.1 | 3368 / 3423 |
| off | 100 | 0 | 143 A | 0.54 / 0.56 | 1.06 / 1.05 | 29.1 / 29.2 | 81 / 89 |

(plant / LTspice; peak = SH2 for turn-ons, SH1 for turn-offs; L_cs 20 pH rows in the JSON.) Within 0.1 ns,
0.2 V and 5-9 %. The plant's turn-off hands an ideal (0 V) switch to a channel at 0.2 V, so ~1 nC moves into C_OSS in
one step; peaks, times and energies are unaffected, only a "max di/dt" of the channel is not comparable there.

## 4. What the gate changes (single edges, 254 + 190 runs)

1. **Turn-on overshoot is gentler than a ramp of the same slope.** At the line-step state (V_DS 17 V) the gate edge
   peaks 3.5-5 V below a linear ramp with its 10-90 % slope (50 pH, 2 Ω: 37.4 vs 40.9 V; 100 pH, 4.5 Ω: 32.3 vs
   37.2 V; 150 pH, 4.5 Ω: 35.0 vs 38.7 V): the channel saturates and the Miller plateau limits dv/dt. D68's
   x-law in di/dt is conservative there.
2. **Turn-on loss is not small.** Per steady-state turn-on (V_DS 3.8 V at the valley): 94 / 213 / 386 / 696 /
   1055 / 2134 nJ at 1 / 2 / 3 / 4.5 / 6 / 10 Ω (50 pH), against 70-180 nJ for ramps of the same slopes. At
   ~7.9 million turn-ons per second per module that is 0.7 / 1.7 / 3.0 / 5.5 / 8.3 / 17 W. A151's "0.1-0.4 W" was
   a property of the ramp, not of a slow gate: the slower the turn-on, the longer the channel carries the node's
   discharge and the rising phase current at several volts.
3. **The turn-off resistor decides between a ZVS-like and an overlap turn-off.** With a strong sink (r_off 0,
   R_G only) the channel is off before V_DS rises and the current charges C_OSS: 76 nJ at 143 A (0.6 W per
   module). D69's ~1.2 Ω ("72 A/ns") leaves the channel conducting while V_DS rises: 1.26 µJ (~10 W); 2 Ω 2.7 µJ.
   With the strong sink the overshoot is the loop's energy bound (D65): at 200 A 26.8 / 34.9 / 41.7 V at 50 / 75 /
   100 pH; at 143 A 18.1 / 24.2 / 29.1 / 33.3 / 37.1 V from 50 to 150 pH. Slowing the turn-off to hold a larger
   loop costs watts (100 pH, 0.5 Ω: 37.4 V at 200 A, 0.6 µJ at 143 A ≈ 4.7 W).
4. **Common-source inductance** slows the turn-off (100 pH, 200 A, 1.2 Ω: 33.9 → 26.4 / 22.2 V at L_cs 25 / 50 pH)
   at more loss (2.9 → 4.4 / 5.9 µJ) and hardly touches the turn-on: a Kelvin gate return is wanted.
5. **Spread** (threshold −0.3 / +1.5 V, C_ISS × 1.5, 125 °C, driver resistance ± 30 %): on the line-step turn-on
   the driver at −30 % adds 4.3-4.7 V and the minimum threshold 1.8-1.9 V (50 pH, 2.5 Ω: 34.7 → 39.0 / 36.5 V);
   the slow side (maximum threshold, C_ISS max) doubles to quintuples the turn-on loss (294 → 566 / 1345 nJ) and
   speeds the turn-off (+1-4 V at 200-260 A).
6. **dv/dt immunity** (LTspice, low sides held off through 0.3 Ω): during SH1's 17 V turn-on SL1's internal gate
   rises to 0.39-0.47 V (threshold min 0.7 V), during its turn-off it dips to −1.05 V; SH2 ≤ 0.21 V. So the
   low-side sink must stay ≤ ~0.3 Ω.
7. **Threshold mismatch between parallel devices** (LTspice, 50 pH, 2.5 / 0.3 Ω, SH1's two devices 0.5 V apart): the
   lower-threshold device takes the edges: turn-on at 17 V 1741 vs 184 nJ (matched 940 each), turn-off at 200 A
   611 vs 80 nJ and 136 vs 99 A peak (matched 323 nJ, 104 A). The total hardly changes; the hottest die carries
   ~1.9x its share of the edge loss (~1 W at R_θJC 0.4 K/W: small), far below the 409 A pulsed rating.
8. **Gate-loop inductance** (per device, same point): turn-on unaffected (2 nH: +0.8 V at 17 V, +9 % energy at 3.8 V);
   at the strong-sink turn-off the gate rings to −0.31 / −1.07 / −2.09 V at 0.5 / 1 / 2 nH (limit −4 V) and back up
   to 0.06 / 0.26 / 0.72 V after the edge (0.40 V without L_g, the Miller bump of the drain ring): at 2 nH a
   minimum-threshold device would partly turn on again. So the gate loop must stay ≤ ~1 nH per device.

## 5. The drive in resistors (worst single edge over the spread)

| candidate | turn-on 17 V | turn-off 200 A | turn-off 260 A | energy on + off (steady, nominal) |
|---|---|---|---|---|
| 50 pH, r_on 2 Ω, r_off 0.3 Ω | 41.7 V (r − 30 %) | 25.9 V | 34.4 V | 213 + 286 nJ |
| **50 pH, r_on 2.5 Ω, r_off 0.3 Ω** | **39.0 V** | **25.9 V** | **34.4 V** | 294 + 286 nJ (~4.6 W) |
| 75 pH, r_on 3 Ω, r_off 0.3 Ω | 40.2 V | 33.9 V | 44.6 V | 347 + 336 nJ |
| 75 pH, r_on 3.5 Ω, r_off 0.3 Ω | 38.2 V | 33.9 V | 44.6 V | 448 + 336 nJ (~6.2 W) |
| 100 pH, r_on 3 Ω, r_off 0.5 Ω | 42.4 V | 39.5 V | 51.4 V | 314 + 599 nJ |

So in resistor terms: **turn-on as fast as the line-step overshoot allows (≈ 2.5 Ω per device at 50 pH,
3.5 Ω at 75 pH), turn-off as fast as possible (a ~0.3 Ω sink), low-side sink ≤ 0.3 Ω, Kelvin source, loop
≤ 75 pH for the 200 A budget and ≤ 50 pH if 260 A excursions (C13's falling ramps) must also stay ≤ 40 V.**
Gate loop ≤ ~1 nH per device (Section 4.8). This reverses D69's "name a slow turn-off" and lowers the ramp model's
125-150 pH bound. Start-up on-time
(cosim to the handover, A155's 0.0283 V/ns): Vo(143.5 µs) at ton 36.5 ns is 0.998 / 0.950 / 0.962 V for
2 / 3 Ω (75 pH) / 4.5 Ω; the A163 configurations add (1.015 − Vo) / 0.0283 ns.

## 6. Limits

- The plant's devices are identical (mismatch and gate-loop inductance are LTspice single edges, Sections 4.7-4.8);
  the driver is an ideal source behind a resistor (no supply droop, no propagation-delay spread beyond the bridge's
  t_drv); the damper is the ideal Q 7 resistor.
- The plant's low sides keep instantaneous (ZVS) edges; their dv/dt immunity is checked in LTspice only.
- Single edges are snapshots of A145's state; the system (frozen controller, deferred measurement, start-up) is A163.
