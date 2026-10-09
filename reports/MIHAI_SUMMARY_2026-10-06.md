# SCB-IVR reproduction: progress since 14 September

Changan Jian · 9 October 2026 ·
[github.com/changanjian-lwy/ectc2024-scb-ivr-reproduction](https://github.com/changanjian-lwy/ectc2024-scb-ivr-reproduction)

Since our meeting the work has moved from checking one module's switching
sequence to a closed-loop design of the full 48 V → 1 V, 1 kW system of the
ECTC 2024 paper (P24):

- one four-phase module and the four-module, 16-phase system both run in
  co-simulation: a Verilog controller against a circuit model with the
  datasheet's nonlinear Coss and reverse conduction, cross-checked against
  analytical models;
- both controller designs are frozen after randomised testing;
- at the package level (P24 Figs. 5-6), the switch overshoot caused by the
  commutation loop is solved by the gate drive, which gives a loop and
  driver specification (Section 3). It holds on the tested rows of a
  gate-level model with an idealised driver interlock; its limits are listed
  with it.

The sections below separate what agrees with P24, what does not, and which
unpublished values the remaining conclusions rest on.

## 0. How far the two papers are reproduced

Item by item in `reports/PAPER_REPRODUCTION_MAP.md`.

- **P24** (analytical and conceptual, no measurement): of ten checkable items,
  five agree (topology, Eqs. (1)-(3), Fig. 4's interval sequence, the series
  capacitors' balance, Table 3's devices); two give other numbers at this
  design point (inductor count, module footprint); three do not hold as
  printed: 1-2 % negative current for full ZVS, a frequency free of switching
  loss, and Table I's L_crit against its own Eq. (4). The controller,
  start-up, multi-module operation, losses, package parasitics, gate drive and
  thermal are this work's.
- **P25** (12 V prototype): ZVS at a small negative current and one current
  sensor per module are consistent with its own operating point: the ZVS
  criterion needs 1.5-2 % (A67), and one sensor gives a near-closed ZVS orbit
  (D41; the strict return check passes only at 4 mΩ per phase) that an
  independent circuit simulation reproduces (A69). Table II's duty is a typo (0.26 % for 0.25), and the 22 nH /
  50 A operating point does not close with Eq. (20) (~32 nH). Its hardware and
  the three-module closed loop were not reproduced.
- **The link:** the negative current ZVS needs scales as √(L·C_node) / Ton:
  1.5-2 % at P25's point, 22-26 % at P24's 48 V / 5 MHz point.

## 1. The design that runs

| | |
|---|---|
| module | 4 phases, 250 W; 2 + 3 EPC2067 per phase (P24 Table 3); 2.5 MHz, L = 2.933 nH (P24 Eq. (4)), Cs = 6 µF; negative current 12.5 % of the 125 A peak |
| control | boundary mode; the high side turns on at its predicted valley; phase 1's low-side turn-off timed, phases 2-4 on interleaved slots; PI voltage loop at 100 kHz; Vin feed-forward; soft start over the series-capacitor ladder |
| system | four modules on one output, one shared voltage loop, master-slave interleave at T/16, current sharing through the common on-time |

Results (co-simulation, 25 °C):

- **Estimated efficiency 86.6-87.7 % before core loss** per module (loss model on
  the simulated waveforms, 29-40 current-rated HBS1-class units per phase). HBS1's
  own loss metric (R_acx, P24's ref. [10]) adds 7.5-30 W per module (small to large
  signal): **78-85 %**; at Choi, Khorasani et al.'s 85 °C (TCPMT 2025), with the package, ~73-82 %.
  Gate-driven edges (Section 3) add 1.7 W per module with nominal devices and 3.9 W at
  the slow corner: about −0.5 and −1.0 to −1.2 points of efficiency (thermal model rerun
  with these losses: D80).
- **±62.5 A load step:** +15.3 / −11.9 mV, back within 1 % in 6.2 / 3.6 µs.
- **Peak switch current ≤ 196 A** (ideal switches, no package; with the package
  and gate model see Section 3) on every registered test of one module
  (limit 200 A: this work's budget, 1.6 × P24's 125 A nominal peak; it
  stands for the inductor's saturation current and the turn-off energy,
  not the switch rating, 409 A pulsed per EPC2067): driver mismatch, 30-100 ps jitter, load steps, ±10 % line
  steps from 1 µs, inductance × 0.7-1.3. Four modules: ≤ 188 A on 22 tests.
- **16-phase output ripple** 6.9 A rms on 1 kA.
- **Randomised tests** (120 draws on one module, 30 on four) found one real
  defect: a rising line step in the first ~0.5 ms after start-up oscillated
  to 254 A. It is fixed (≤ 196 A). The remaining > 200 A cases are falling
  ramps outside the slew window in Section 4.
- **Not claimed:** all-switch ZVS. The low sides switch at zero voltage; the
  high sides turn on at their valley, 3.3-3.9 V of the 12 V rail.

## 2. Findings, and where they differ from P24

1. **1-2 % negative current does not give high-side ZVS with P24's own
   values.** The current needed scales as V_rail·√(C_node / L). With
   Eq. (4)'s 1.47 nH and the 2 + 3 EPC2067 node it is ~27 % of the peak, and
   at least 5.3 % for any inductance in P24 Table I. The circuit
   simulations agree: zero voltage first appears at 25 %; at 2 % the high side turns on
   at ~9.9 V.
2. **One quantity links efficiency and robustness: the valley margin**
   I_th − i_neg. Raising i_neg toward the ZVS threshold I_th removes the high
   side's hard turn-on loss (8.9 W → 0.7 W per module). But when a transient
   pushes a valley past I_th, the node clamps at the rail and the predicted
   turn-on loses its target. Every design with a margin ≤ 2.5 A failed a
   transient (runaways above 500 A); 8 A passed all but the fastest line
   steps. The chosen 12.5 % keeps 7.9 A.
3. **The inductor sets the frequency, not the switching loss.** From 5 to
   1 MHz the switching loss falls from 16.8 to 1.6 W, but the inductor's
   copper loss rises from 2.6 to 13.8 W (L ∝ 1/f). With an MPC-class
   inductor resistance (79 µΩ/nH, the core family of P24's package),
   2.5 MHz is best: 90.6 % against 90.2 % at 5 MHz and 89.0 % at 1 MHz,
   with three times the 1 MHz valley margin. But 79 µΩ/nH is the 500 nH
   unit's: 170 of them per phase. With units sized for the current (≥ 5 A
   each, 29-40 per phase), smaller units at higher frequency carry a higher
   R/L, and the three come within 0.9 points (2.5 MHz 86.6-87.7 %, 5 MHz
   86.4-87.1 %, 1 MHz 85.7-87.1 %): 2.5 MHz stays, narrowly. With an air-core stripline
   inside Fig. 5's footprint (0.25-0.63 cm² per phase) the optimum moves to
   5 MHz, 2-9 points above 2.5 MHz. The 2.5 MHz design therefore assumes a
   magnetic inductor; at 144 A per phase that is about 29 HBS1-class units
   in parallel (P24: 12 at 62.5 A), 40 for the 200 A transient budget; their fit is
   open, and their core loss (R_acx ∝ f^1.55) removes the efficiency lead: 5 MHz falls
   1.4-4.5 points behind, 1 MHz ties within ~1 point. P24's Table I (2.68 nH at 5 MHz) and
   Eq. (4) (1.47 nH) disagree; this work follows Eq. (4).
4. **Interleave errors grow with the phase count.** A 9.4 ns slot offset,
   invisible on one module (N·D = 0.31), gave 45.9 A rms of 16-phase output
   ripple instead of 6.75 A rms (N·D = 1.22). Referencing every slot to
   phase 1's low-side turn-off removed it.
5. **Current sharing,** which P24 names as the primary challenge without a
   method. In boundary mode the period does not depend on L, so trimming a
   module's on-time to equalise its current pulls it out of interleave. The
   design keeps one common on-time and the modules share by their
   inductance. The module with the smaller L binds: in co-simulation it
   stays at 194 A through transients with ±5 % worst-case inductor spread
   and reaches 208 A at ±10 % (the limit is near ±7 %), carrying 12-16 %
   more loss at ±5 %. Trimming each module's negative current cannot fix this,
   because it uses up that module's ZVS and transient margin. In this
   architecture, current sharing is an inductor-matching specification.
6. **Fast input steps need a feed-forward.** ±4.8 V steps over 1 µs peaked
   at 216-218 A. A Vin feed-forward found with reinforcement learning, then
   reduced to a six-parameter rule and built in Verilog, brings them to
   ≤ 182 A at no steady-state cost. Learning was used only as a search
   tool; an earlier policy that exploited its reward was rejected.

P24 does not describe the controller, start-up or module synchronisation;
these are this work's choices, taken from the critical-mode PFC
interleaving literature.

## 3. Package level (5-8 October)

P24 Figs. 5-6 give the layout but no copper, via or loop values, so these
are budgets over plausible ranges:

- **Lateral output copper dominates.** Fig. 5 routes each phase sideways to
  a central Vo / GND strip. With one 35 µm layer each way this costs 30.7 W
  per 250 W module (12.3 %), more than the converter's own 25.9 W. 5 % needs
  86 µm of copper per stack, 1 % needs 429 µm. Vias, the strip and the
  series-capacitor ESR (≤ 0.5 mΩ) together stay below ~1 %. This copper is
  in the loss budget only: at 35 µm its 12 % drop would move the converter's
  operating point, so the estimate holds for thick copper (≲ 2 % drop, ≳ 107 µm
  on the 10 × 20 mm a 250 W module needs for its 20 dies). Package-inclusive with
  the buildable array: ~83-87 % for 86-429 µm and 50-150 pH, 75-85 % with core loss.
- **The loop inductance sets loss; hard turn-ons set the device voltage.**
  With the loop in the circuit model (ring Q 7) and 1-2 ns switching edges,
  the steady high-side peak stays ≤ 34 V up to 150 pH. The loop costs
  1.4 / 3.8 / 6.4 W per module at 50 / 100 / 150 pH, so 1 % allows about
  70 pH. The binding overshoot comes after transients: a rising line step
  makes phase 1 lose ZVS (for ~13 µs its low side turns off at +12..+15 A
  instead of −15.6 A), its high side turns on hard at 17-19 V, and the ring puts the
  next high side, already blocking two rails (24 V), at 42-51 V
  (50-100 pH).
- **Control cannot remove it at an acceptable cost.** Rail 1 takes the
  whole step, so phase 1 needs ~22 % more volt-seconds. Holding its valley
  stretches the common period and stops the ladder until phases 2-4 dig
  deeper valleys, which is an output-charge deficit: every law that kept
  ZVS needed ~42 µs for Vo to return within 1 % (8 µs now). A constrained
  Bayesian search over the law's two gains found a narrow band that holds
  40 V at 50 pH, but there the loop oscillates on neighbouring line slews
  (203-275 A). The same law does fix load steps.
- **The gate drive removes it.** Slowing only the hard turn-on, with a fast
  turn-off, holds every switch ≤ 40 V, start-up included. Dymond et al. (2018)
  report the same on a 40 V GaN bridge leg.
    - First shown with current-ramp edges: 37.1 V at 50 pH with 36 A/ns.
    - With EPC's own EPC2067 model in the circuit (checked against the datasheet,
      and against LTspice on all 20 devices), it means ~3 Ω turn-on and ≤ 0.3 Ω
      turn-off per device.
    - A real gate overshoots 3.5-5 V less than a linear ramp of the same slope, so
      the ramp formulas below are conservative.
    - The edges cost 2.3-2.9 W per module at 50 pH (fast / nominal / 125 °C
      devices) and 4.6 W at the slow corner: 1.4-3.6 W more than the loss model's
      ideal edges, 0.4-1.1 points of efficiency at ~87 %. Rerun in the thermal model,
      they change no thermal conclusion. The ramp model's "0.1-0.4 W" was an
      artefact of linear ramps.
- **Both effects follow from the node charge** (2 + 3 EPC2067 swung by 12 V,
  Q ≈ 162 nC). The turn-on ramp lasts √(2Q / (di/dt)) and ends when the node
  swing plus L·di/dt reaches the rail; what it leaves undone, the LC ring
  does. So the overshoot depends on **L × di/dt only**: ≤ 40 V for
  L·di/dt_on ≤ 3.2 V (a quarter of the rail). The lost start-up on-time goes
  as (di/dt)^-½ plus 6 ns per nH of loop. Both laws were registered and then
  tested at loops and rates never run before (75-300 pH, 6-40 A/ns): peak
  V_DS within −0.1..+0.6 V, the 40 V side right on every point, start-up
  151-155 A. The whole robustness matrix and four modules stay ≤ 39.5 V
  at L·di/dt 3.0 V (125 and 150 pH).
- **The datasheet spread decides the drive, through timing.** EPC2067's limits
  allow a threshold up to 2.5 V and Q_G up to 22.3 nC. With those and the gate
  resistor's tolerance, the high-side turn-on delay (command to channel start)
  runs from ~1.5 ns to ~16 ns. Two parts of the controller depend on it.
    - **Open-loop start-up.** Its on-time moves by up to ~4 ns, which sets the
      peak when the loop takes over: 157 A nominal, 376 A at the threshold maximum.
      A one-shot trim per board fixes it: set the start-up on-time so that Vo is
      1.035 V at the handover. That held on every board tested.
    - **Valley timing.** Our controller commands the high side no earlier than one
      clock after the low side's turn-off command, and the valley comes 9.5-11 ns
      after that command. So it absorbs only ~5.5 ns of gate delay, and the high
      side needs a lead.
        - With an 8 ns lead, nominal, hot and fast-corner boards run without timing
          faults, four modules included. The lead is enabled over ~20 µs after the
          handover; switched on at once it is an on-time step there (219 A at
          inductance × 0.7).
        - The lead removes the implicit interlock. When the learned timing collapsed
          in two corner runs, the high side shot through.
        - Bounding the lead by each board's shortest delay minus 1 ns is safe: no
          shoot-through in 13 runs. But it is too small for the hard turn-ons after
          a rising line step: 19-85 late turn-ons, and 208 A at inductance × 0.7.
        - At the slow corner (threshold and Q_G at their maxima, resistance +20 %),
          peaks and voltages hold, but the controller fires late during the handover
          and after rising line steps whatever the lead.
        - Once the low sides' own turn-off is modelled too (≤ 2.9 ns delay +
          1.8 ns edge), the 8 ns lead shoots through after the inductance × 0.7
          handover and at the slow corner. A bound on the lead cannot help: it
          would have to be negative.
        - **A driver interlock closes it in the model, without touching the
          controller.** A turn-on's gate charges as usual, but its channel waits
          at the threshold until the complementary switch has stopped conducting
          (0.5 ns; integrated GaN drivers reach 0.03-1 ns adaptive dead times).
          Holding the gate at 0 V instead puts the two delays in series: 214 A at
          inductance × 0.7.
        - In the model this interlock is an idealised function: it senses the
          complement's channel exactly. It acted only on the inductance × 0.7
          board and at the slow corner; there its zero shoot-throughs are imposed
          by the rule. A buildable comparator releases later: ~1.4 ns with a
          reference set per board, up to 8.3 ns with a fixed 1.0 V reference
          at the slow corner. No delay up to 8.3 ns changed a peak or a
          voltage, so the release time is a timing specification. Repeated at
          three step positions per delay, the slow corner's late turn-ons
          after a −8 V ramp stay at 9-32 up to 1.0 ns and reach ~50 at
          1.4 ns at two of four positions: the release should be within
          1.0 ns. The per-board reference (~1.4 ns) is just above that, a
          fixed one far above.
    - With ±30 % on the gate resistance no single resistor meets both the fast
      corner's 40 V and the slow corner's timing; ±20 % does.
- **The turn-off wants a strong sink.** With ≤ 0.3 Ω the channel is off before
  V_DS rises, and the overshoot is the loop's energy bound: 27 / 35 / 42 V at 50 /
  75 / 100 pH and 200 A. A ~1.2 Ω sink (~72 A/ns) instead costs ~10 W per module
  in V-I overlap. In the ramp model above ~150 pH the turn-off binds: it needs
  L·di/dt_off ≤ ~10 V, at +7 to +28 W per module (200-300 pH).
- **Resulting specification.** Checked on the final model (all eight switches
  gate-driven, the interlock as above):
    - nominal devices: the whole 13-row transient matrix (line steps and ramps,
      load steps, inductance × 0.7 / 1.3);
    - fast, slow and 125 °C corners: +4.8 V / 1 µs and the load step; the
      −8 V / 10 µs ramp at fast and slow; the 4 µs ramp at slow;
    - four modules: nominal, slow corner, a ±5 % inductor spread, a load step.
  The table is in the repository (reports/FINAL_SPEC_COVERAGE.md).
    - Loop ≤ 50 pH, for this drive and controller (not a package limit in
      general). At 60 pH the fast corner reaches 40.3 V with 3.0 Ω; 3.5 Ω
      holds it but costs the slow corner's timing. 75 pH with 4.0 Ω loses the
      line step's regulation (12.6 mV, 46 µs) and the slow corner's timing.
    - Per device: 3.0 Ω ± 20 % turn-on, ≤ 0.3 Ω turn-off, a Kelvin source and a
      gate loop ≤ 1 nH. Low-side sink ≤ 0.3 Ω (dv/dt immunity).
    - An 8 ns high-side turn-on lead, enabled over ~20 µs after the handover
      so the loop takes over without an on-time step, plus the threshold-form
      driver interlock (see above). The controller stays as frozen.
    - A per-board start-up trim.
    - Results: switch ≤ 38.4 V on every run. Peaks ≤ 198.3 A on every run
      with the inductance at ≥ 0.75 × nominal (the 0.75 × and 0.8 × boards
      at five step phases each). At 0.7 × the board reaches
      199.5-201.5 A after +4.8 V / 1 µs, and its open-loop start-up 200 A, so
      the inductor tolerance for the 200 A budget is −25 %. Four modules:
      184 A; 196.5 A with a ±5 % inductor spread.
    - Open, with no current or voltage consequence:
        - Falling line steps make the controller restart its valley prediction
          on phases 2-4, with 10-20 A spikes. This needs both the lead and the
          gate-driven low sides; each alone gives none. A lead held off while a
          valley is lost would remove it, but that is an RTL change.
        - At the slow corner, Vo dips 3-5 mV deeper after line ramps (up to
          −25 mV).
    - The ramp model's 125-150 pH bound does not survive the device spread.
    - Peak currents in this section are physical, after the gate delays. The ramp
      runs reported the current at the turn-off command, 5-8 A lower.
    - Published embedded-GaN loops are 230-320 pH, which this design can drive
      only at several percent of efficiency.
- **Rating used:** EPC2067's 40 V continuous rating, not the datasheet's
  48 V transient or EPC Phase 16's 120 % for ≤ 1 % of life (100 V parts);
  under that rule 50 pH would pass without the slow turn-on, 100 pH not.

## 4. Open values, with the cases run

| value (not published) | cases | what it decides |
|---|---|---|
| input-bus slew, load-step specification | steps ≤ 4.8 V at any tested slew from 1 µs: ≤ 200 A, inductance × 0.7-1.3 included. 8 V steps need ≥ 6 µs falling, ≥ 10 µs rising (≥ 50 µs at inductance × 0.7). Faster falling ramps: 218-260 A | the valley margin to keep, so how close to high-side ZVS the design may run |
| output routing and copper | lateral at 35 / 86 / 429 µm: 12.3 / 5 / 1 % loss; a vertical output removes most of it | module efficiency |
| inductor matching across modules | ±5 / 10 / 20 % spread: heaviest module +12-16 / +25-34 / +57-79 % loss; co-simulated peak 194 / 208 A at ±5 / 10 % worst case (200 A near ±7 %); with the gate-level package model ±5 % gives 196.5 A | whether passive sharing suffices |
| inductor technology, footprint per phase | 29-40 current-rated HBS1-class units per phase: 86.6-87.7 %, 2.5 MHz best by 0.2-0.6 points before core loss, 1 MHz ties once it is counted; air-core in 0.25-0.63 cm²: 5 MHz; saturation must cover the 200 A transient peak | the switching frequency; the efficiency; the peak-current budget |
| QH / QL placement, loop inductance | 50-300 pH: loop loss 1.4 / 3.8 / 6.4 W at 50 / 100 / 150 pH; ramp edges hold 40 V to 150 pH, but with EPC's gate model and the datasheet spread the drive and the controller's timing hold only to 50 pH (60 pH at the edge) | loss; whether the resistor drive holds |
| gate drive, turn-on vs turn-off | equal fast edges: 42-51 V after a 4.8 V / 1 µs step (50-100 pH); 3.0 Ω ± 20 % turn-on / ≤ 0.3 Ω turn-off per device holds the corners tested (Section 3; ±30 % has no single-resistor window); the turn-on delay (1.5-16 ns) needs a high-side lead and a per-board start-up trim | the driver's resistances and tolerance; whether the controller can lead the high side |
| derating rule | 40 V continuous used; a 120 % / 1 %-of-life rule would admit 50 pH without the slow turn-on | how much drive slowing is needed |
| loop damping | ring Q 7-30 at 50-100 pH: no change; Q 100, 300 or undamped: valley detection lost from start-up (2400-9000 late edges) even with the slow turn-on | a damping requirement, Q ≤ 30 with an ideal parallel damper; at the ring frequency that is ≳ 4-8 mΩ series-equivalent (Q 7: 19-32 mΩ); the physical source is open |
| series-capacitor technology | ESR ≤ 0.5 mΩ: < 1 %; ESL not yet modelled | ladder ringing |
| thermal path, coolant temperature | 85 °C fixed point: ≤ 0.8-1.0 K·cm²/W per module to a 25 °C coolant (0.5-0.7 at 45 °C); inductor array hottest (3D); 2-4 % via copper in glass 1 and ≥ 0.4-1.1 g/s of coolant per module hold 85 °C (computed with a 150 pH loop; with the 50 pH spec and the gate-level losses 3-19 % less, D80) | hot efficiency; vias; coolant flow |
| output-capacitor placement, processor-side decoupling | the lateral Vo path is 63-628 pH per module (Fig. 5 geometry); with the capacitors at the modules a 1 kA/µs load slew drops 16-157 mV at the processor, faster than the loop (module-to-module ringing ≤ 1 mV) | load-side decoupling or load slew; Vo sensed at the common strip |

Five answers would narrow the package specification most:

1. How do P24's driver and controller handle the high-side turn-on delay?
    - The resistances that hold 40 V are ~3 Ω turn-on and ≤ 0.3 Ω turn-off per
      device. With EPC2067's datasheet spread, the delay from command to channel
      start then runs from ~1.5 to ~16 ns.
    - Our controller commands the high side only after the low side's turn-off
      command, so it absorbs ≤ ~5.5 ns. It needs a lead, and the lead is safe
      only with a driver interlock that holds a channel at its threshold until
      the complementary switch is off. Its release time decides the slow
      corner's timing (not its peaks): within 1.0 ns.
    - What gate resistance and tolerance does the driver have, does the
      controller lead the high side, and does the driver have such an interlock
      (or adaptive dead time), with what reference?
2. Which derating rule do you apply to repetitive ns-scale drain overshoot
   on 40 V GaN: the continuous rating, or a transient allowance such as
   EPC's 120 % for ≤ 1 % of life?
3. What is the prototype's commutation-loop inductance? A double-pulse
   V_DS capture would do: a CNN trained on simulated captures, followed by a
   circuit fit, recovers L, Q and di/dt within 1-6 % (probe ≥ 0.7 GHz). The same capture gives the
   ring's Q, which must stay ≤ ~30. With L known, the drive spec follows
   from the gate-level results above (≤ 50 pH for the resistor drive).
4. How was the start-up on-time set? With real gates the threshold spread
   moves the open-loop on-time by up to ~4 ns. That decides the peak at the
   handover (157 A nominal, 376 A at the threshold maximum), so we trim it once
   per board.
5. Which face of the IVR is cooled, at what coolant temperature? Thermal vias in
   glass 1? The core's large-signal loss at ~5 A per unit? Without vias our 3D
   model has the inductor array 54 K above the dies; the core costs 2-8 points.

Otherwise I will continue across the ranges above.

## 5. How the results are checked

- Every experiment registers its pass criteria before it runs; results are
  reported against them, misses included. Two independent models check each
  other (an analytical event map and averaged model; the co-simulation), and
  every controller option reproduces the previous design bit for bit when off.
- Learned models propose or flag; the co-simulation decides. About 180
  experiments and over 60 derivation notes; status in
  `reports/CURRENT_STATUS.md`, trade-offs in `reports/TRADEOFF_SCORECARD.md`.
