# D79 - the gate drive in resistors: EPC2067's gate in the plant, checked against LTspice with EPC's own model

2026-10-07. Code: `src/scb_ivr/p24_gate_model.py` (device), `src/scb_ivr/cosim/gate.py` (the plant's gate-driven
edges, cfg "gate"), `scripts/p24_ltspice.py` (LTspice in batch), `scripts/p24_gate_edges.py` →
`diagnostics/D79_gate_validation.json`, `D79_gate_sweep.json`, `D79_gate_candidates.json`, `D79_dvdt.json`,
`D79_mismatch_gate_loop.json`.
Vendor model: EPC GaN library (EPC2067 entry, 2021-10-18), kept **outside** the repository (`vendor_models/` next
to it, or `SCB_EPC_LIB`); `tests/test_p24_gate_model.py` skips without it. System tests: A163-A165 (Section 6).

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
5. **Spread** (threshold −0.3 / +1.5 V, C_ISS × 1.5, 125 °C, driver resistance ± 30 %; the +1.5 V and × 1.5 corners are
   outside the datasheet, see Section 6): on the line-step turn-on
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
Gate loop ≤ ~1 nH per device (Section 4.8). (In the system this table's 2.5 Ω fails the spread; Section 6 gives the
spec that holds: 3.0 Ω ± 20 % with a turn-on lead, a per-board start-up trim and a threshold-form driver interlock,
loop ≤ 50 pH.) This reverses D69's "name a slow turn-off" and lowers the ramp model's
125-150 pH bound. Start-up on-time
(cosim to the handover, A155's 0.0283 V/ns): Vo(143.5 µs) at ton 36.5 ns is 0.998 / 0.950 / 0.962 V for
2 / 3 Ω (75 pH) / 4.5 Ω; the A163 configurations add (1.015 − Vo) / 0.0283 ns.

## 6. In the system: A163-A172 (cosim with the frozen controller)

**Correction to Section 4.5.** The spread used here was +1.5 V of threshold and C_ISS x 1.5, with a driver
tolerance of +-30 %. The first two are outside the datasheet: EPC's typical curve already sits at V_GS(TH) 1.51 V
(18 mA), so +1.5 V gives 2.99 V and R_DS(on) 1.81 mOhm, against the 2.5 V / 1.55 mOhm maxima, and x 1.5 gives Q_G
25.8 nC against 22.3 nC max. The consistent corners are +1.0 V (2.49 V, 1.53 mOhm) and charge x 1.29
(tests/test_p24_gate_model.py). The +-30 % driver tolerance was an assumption, and A164's pre runs show no single
resistor survives it (below). A163 RESULTS records the original verdict.

**A163** (2.5 / 0.3 ohm, 29 runs). With nominal devices the gate-driven edges hold:
- V_DS <= 36.4 V, physical peaks within +-2 A of the ramp model's;
- edge power 2.4 W per module (the ramps gave 3.9 W);
- the channel starts on the valley (0.11 ns), because the valley is measured when the channel starts.
Over the spread, three mechanisms fail the frozen controller:
1. **Start-up on-time.** Mode S is open loop, and the gate delay eats its on-time. Vo(143.5 us) falls 0.054 V per
   0.5 V of threshold (0.903 V at +1.0 V, 376 A at the handover). The handover has a cliff below ~0.99 V and is
   benign up to 1.17 V. Fix: trim each board's start-up ton from one start-up run.
2. **The valley-timing limit.** The RTL cannot command a predictive turn-on before the low side's turn-off command
   plus about one 4 ns clock (dt_pred >= 0). The valley comes 9.5 ns after that command on phase 4 (11.1 ns on
   phases 1-3). So the turn-on gate delay (command to channel start) must stay below ~5.5 ns on phase 4. Nominal is
   2.4 ns; +1.0 V gives 6.0 ns and late fires. Fix: a lead on predictive high-side turn-ons.
3. **Driver -30 %** gives 40.6 V on the line step, 1.6 V above this note's single-edge harness. Fix: r_on margin.

**A164 pre runs.** At +-30 % the slow corner (+1.0 V, Q_G x 1.29, 3.5 ohm x 1.3 = 4.55 ohm) has turn-on delays of
9-20 ns and transitions up to 32 ns, close to the whole on-time. Without a lead every period fires late. With an
8-9.5 ns lead the steady state holds, but the handover reaches 216-228 A. Any resistor fast enough for that corner
breaks 40 V at the fast corner (-0.3 V, x 0.7). The turn-on resistance is mostly the external resistor, so the
spec takes +-20 %. Single edges then put the fast corner at 37.0 V (cosim 38.5 V) for r_on 3.0 ohm.

**A164-A167** (50 pH, 3.0 / 0.3 ohm +-20 %, per-board trim; see their RESULTS). Peaks and V_DS hold at every
corner: fast 38.5 V, <= 195 A after steps. The form of the lead decides the rest.
- **A164, 8 ns on the turn-on only.** No timing faults at nominal, hot or fast, four modules included. Without a
  lead, +4.8 V gives 48 late fires. But in mode P every pulse is 8 ns wider than in mode S, an on-time step at the
  handover: 218.6 A at L x 0.7.
- **A165, the same lead as a pulse shift.** The handover is smooth, but L x 0.7 reaches 211 A after the line step.
  The bridge moves plant edges, not the RTL's phase-1 timeline.
- **A166, interlock-safe per-board lead** (shortest delay - 1 ns, 1.3 ns nominal). Late fires after the rising steps,
  and 208 A at L x 0.7.
- **A167, A164's lead ramped in over 20 us after the handover.** L x 0.7's handover is 191.5 A and its post-step
  195.3 A. Only mode S's 202.5 A remains: the frozen design's open-loop start.
- **The slow corner** (+1.0 V, Q_G x 1.29, 3.6 ohm) fires late after the handover and after rising steps with every
  form, without peak or voltage consequence. Its hard turn-ons take up to 16.6 ns.
- A fixed lead removes the dt_pred >= 0 interlock. Pre runs shot through when dt_pred collapsed after a disturbed
  handover (hot corner, lead 8; slow corner, lead 8 at +-10 % or 12 ns). A controller needs a bound on the lead, or a
  lead that is low during the handover, as A167's is.

**Loop bound under this drive (A168).** The turn-on delay does not depend on the loop; the overshoot does.
- Single edges (fast corner, 17 V turn-on, 3.0 ohm): 37.0 / 38.5 / 40.4 V at 50 / 60 / 75 pH. The closed loop adds
  ~1.5 V.
- 60 pH at 3.0 ohm: the fast corner reaches 40.3 V after +4.8 V / 1 us.
- 60 pH at 3.5 ohm holds 38.1 V, but the slow corner (4.2 ohm) gains NEW spikes and +45 % late fires, and L x 0.7's
  handover reaches 202 A.
- 75 pH at 4.0 ohm holds 38.6 V but loses the line step's Vo (12.6 mV, 46 us) and the slow corner's timing (577 late
  fires).
- **The loop bound is 50 pH.** Edge power rises with the resistor: +0.3 W per module nominal at 75 pH, +1.6 W at
  the slow corner.

**Gate-driven low sides and the interlock (A169-A172).**
- **A169.** With the low sides gate-driven too, the turn-off takes <= 2.2-2.9 ns delay plus <= 1.2-1.8 ns edge, and
  the adopted drive shoots through where dt_pred collapses: L x 0.7 at 152 us, slow corner at 161 us. Phase 4's
  valley goes to -43..-65 A after the handover, the node swings within ~2 ns of the low side's turn-off, and the
  error-based dt_pred falls below the ramped lead. A lead bound cannot fix it: at dt_pred = 0 a safe lead needs lead
  <= fast high-side delay (~1.5 ns) - low-side turn-off (~2.5 ns) < 0.
- **A170, interlock in gate form** (a turn-on's gate waits at 0 V until the complement stops). Every shoot-through
  goes, but the low side's turn-off and the high side's whole gate delay are now in series:
  - post-step delay p90 rises from 4.3 to 9.4 ns;
  - nom 187.6 A and Vo 12.6 mV / 45.5 us; L x 0.7 214.3 A; slow corner 4906 late fires.
- **A171, interlock in threshold form** (the gate charges as usual; a channel about to start while the complement
  conducts waits at that level, then starts t_il = 0.5 ns after the complement stops). It blocks only real overlaps:
  - nom / ff / hot: 0 holds, equal to A169;
  - L x 0.7: 10 holds <= 1.6 ns, phase-4 dt_pred stays at 11.3 ns;
  - slow corner: 84 holds <= 2.6 ns, 194 late fires (A167 260).
  - t_il 1.0 ns changes nothing that matters.
  Integrated GaN drivers reach 0.03-1 ns adaptive dead times (workspace papers), so the form is plausible. It is
  not shown to be buildable: the plant senses the complement's channel ideally and holds the gate exactly at its
  own channel start. Zero shoot-throughs are imposed by the rule wherever it acted (L x 0.7, slow corner); on nom /
  ff / hot and four modules it never acted (0 holds). A173 sets t_il to two realisable forms.
- **A172, final plant**, the L x 0.7 board re-trimmed under it (ton 35.769 ns): start-up 200.2 A, handover 190.2 A,
  post-step 199.7 A (0.3 A margin), 2 late fires. Four modules: post-step 184.2 A, 0 late fires, 0 holds.

**Spec (2026-10-08):**
- loop <= 50 pH;
- 3.0 ohm +-20 % turn-on and <= 0.3 ohm turn-off per device;
- Kelvin source, gate loop <= 1 nH;
- low-side sink <= 0.3 ohm;
- an 8 ns turn-on lead ramped in over ~20 us after the handover;
- a per-board start-up trim measured on the board;
- a threshold-form driver interlock (a channel waits until its complement's gate is below threshold, <= 0.5 ns).

**Coverage and limits of the spec (A173-A176, after an external review; table: reports/FINAL_SPEC_COVERAGE.md).**
- The final plant has run A152's 13-row matrix at nominal devices; the corners on +4.8 V / 1 us, the load step and
  falling ramps; four modules at nominal, ss, a ±5 % inductor spread (196.5 A) and a load step. No run exceeds
  38.4 V.
- L x 0.7 after +4.8 V / 1 us: 199.5-201.5 A over five step phases (A174), at the 200 A edge; L x 0.75 / 0.8 stay
  <= 198.3 / 194.7 A at five phases (A178): the inductor tolerance for the 200 A budget is -25 %.
- Falling steps restart the valley prediction on phases 2-4 (10-20 A spikes). Only the lead and the gate-driven low
  sides together do this (A176).
- At the slow corner the post-ramp Vo dips 3-5 mV deeper than with ideal low sides (A173).
- A realisable interlock releases later than the ideal 0.5 ns: ~1.4 ns with a per-board comparator reference
  (V_th - 0.2 V), up to 8.3 ns with a fixed 1.0 V reference at the slow corner. No delay up to 8.3 ns changed a
  peak or V_DS (A173 / A174 / A177), so the release time is a timing spec. The slow corner's late fires grow with
  it (four modules 803 / 792 / 1608 at 0.5 / 1.4 / 8.3 ns). A179 repeated the slow-corner rows at three step
  positions per delay: after the -8 V ramp the late fires stay <= 32 up to 1.0 ns and reach ~50 at 1.4 ns at 2 of 4
  positions, so the release should be within 1.0 ns (adaptive dead-time drivers reach 0.03-1 ns). Four modules pass
  at 1.4 ns; the load step's one-period spike count scatters 7-27 at >= 1.0 ns without a trend (open).

## 7. Limits

- The plant's devices are identical (mismatch and gate-loop inductance are LTspice single edges, Sections 4.7-4.8);
  the driver is an ideal source behind a resistor (no supply droop, no propagation-delay spread beyond the bridge's
  t_drv); the damper is the ideal Q 7 resistor.
- Since A169 the low sides can be gate-driven (cfg gate switches "all"; A171 / A172 use it). They take the high
  sides' resistors, so their start-up hard turn-ons go through 3.0 ohm. A ZVS turn-on still conducts at once (its
  reverse conduction is not delayed), and dv/dt immunity is checked in LTspice only.
- The interlock senses channel current and its own activation level ideally, then adds a fixed t_il. A real driver
  compares gate voltages with references whose margin is not modelled.
- Single edges are snapshots of A145's state; the system (frozen controller, deferred measurement, start-up) is A163.
