# SCB-IVR reproduction: progress since 14 September

Changan Jian · 6 October 2026 ·
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
  driver specification (Section 3).

The sections below separate what agrees with P24, what does not, and which
unpublished values the remaining conclusions rest on.

## 1. The design that runs

| | |
|---|---|
| module | 4 phases, 250 W; 2 + 3 EPC2067 per phase (P24 Table 3); 2.5 MHz, L = 2.933 nH (P24 Eq. (4)), Cs = 6 µF; negative current 12.5 % of the 125 A peak |
| control | boundary mode; the high side turns on at its predicted valley; phase 1's low-side turn-off timed, phases 2-4 on interleaved slots; PI voltage loop at 100 kHz; Vin feed-forward; soft start over the series-capacitor ladder |
| system | four modules on one output, one shared voltage loop, master-slave interleave at T/16, current sharing through the common on-time |

Results (co-simulation, 25 °C):

- **Estimated efficiency 86.6-87.7 %** per module with a buildable inductor
  array (loss model on the simulated waveforms; 29-40 current-rated HBS1-class
  units per phase). The often-quoted 90.6 % uses the largest HBS1 unit's
  R/L, which would take ~170 units per phase; 92.5 % with an ideal inductor. Hot, to first order: about
  2.5 points lower with the switches at an assumed 125 °C, 3 with the
  inductor copper 100 K hotter too (no thermal model).
- **±62.5 A load step:** +15.3 / −11.9 mV, back within 1 % in 6.2 / 3.6 µs.
- **Peak switch current ≤ 196 A** on every registered test of one module
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
   in parallel (P24: 12 at 62.5 A), 40 for the 200 A transient budget;
   whether they fit, and their core loss, are open. P24's Table I (2.68 nH at 5 MHz) and
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

## 3. Package level (5-6 October)

P24 Figs. 5-6 give the layout but no copper, via or loop values, so these
are budgets over plausible ranges:

- **Lateral output copper dominates.** Fig. 5 routes each phase sideways to
  a central Vo / GND strip. With one 35 µm layer each way this costs 30.7 W
  per 250 W module (12.3 %), more than the converter's own 25.9 W. 5 % needs
  86 µm of copper per stack, 1 % needs 429 µm. Vias, the strip and the
  series-capacitor ESR (≤ 0.5 mΩ) together stay below ~1 %. This copper is
  in the loss budget only: at 35 µm its 12 % drop would move the converter's
  operating point, so the estimate holds for thick copper (≲ 2 % drop,
  ≳ 215 µm). Package-inclusive, first-order sum with the buildable
  inductor array: ~81-86 % for 86-429 µm and 50-150 pH.
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
- **The gate drive removes it.** Slowing only the hard turn-on, with the
  72 A/ns turn-off kept, holds every switch ≤ 40 V, start-up included, up
  to 150 pH: 37.1 V at 50 pH with 36 A/ns, 36.4 / 38.0 V at 100 / 150 pH
  with 18 A/ns. It costs 0.1-0.4 W and 1.9 µs on the load step, because
  under ZVS the turn-on carries no voltage. Dymond et al. (2018) report the
  same on a 40 V GaN bridge leg. One side effect: open-loop start-up then
  loses on-time (Vo 0.958 V when the loop takes over, 224 A at 100 pH); a
  longer start-up on-time restores it (155 A).
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
- **The turn-on rate has a window.** Voltage wants di/dt_on ≤ 3.0 V / L;
  regulation wants di/dt_on ≥ ~20 A/ns (at 150 pH, 12 A/ns deepens the
  load-step dip from −12 to −16 mV and slows the recovery; 18-24 A/ns do
  not). The window closes at L ≈ 3.0 V / 20 A/ns = 150 pH.
- **Above ~150 pH the turn-off binds and has a price.** The 72 A/ns turn-off
  ring exceeds 40 V on its own; a slower turn-off peaks near
  V_rail + 2 L·di/dt, so L·di/dt_off ≤ ~10 V is needed (300 pH: ~32 A/ns,
  37.7 V). Its V-I overlap costs channel loss: about +7 W per 250 W module at
  200 pH and +20-28 W (8-11 %) at 300 pH, against ≤ 0.4 W for the slow
  turn-on below 150 pH.
- **Resulting specification,** checked on 13 transient tests (line ramps
  2-10 µs, falling steps, inductance × 0.7 / 1.3) and on four modules: loop
  ≤ 50 pH, turn-on 36 A/ns, turn-off 72 A/ns, start-up on-time 36.5 ns →
  switch ≤ 37.6 V, start-up ≤ 198 A, after steps ≤ 180 A. 100 pH works at
  18 A/ns. In general: turn-on between ~20 A/ns and 3.0 V / L, turn-off
  72 A/ns up to 150 pH and ≤ 10 V / L above, start-up on-time from one fitted formula (50-300 pH).
  Published embedded-GaN loops are 230-320 pH, which this design can drive
  only at several percent of efficiency. **In the tested model (ideal damper
  at Q 7, 25 °C, nominal Cs, linear current-ramp edges) the turn-on window
  closes near 150 pH, with 0.6 V margin at the worst corner: a candidate
  bound for layout (125 pH for margin), not a hardware limit.**
- **Rating used:** EPC2067's 40 V continuous rating. The datasheet allows
  48 V transients, and EPC's Phase 16 reliability report allows repetitive
  overshoot up to 120 % for ≤ 1 % of life (measured on 100 V parts). The
  specification does not rely on that rule; without the slow turn-on,
  50 pH would satisfy it and 100 pH would not.

## 4. Open values, with the cases run

| value (not published) | cases | what it decides |
|---|---|---|
| input-bus slew, load-step specification | steps ≤ 4.8 V at any tested slew from 1 µs: ≤ 200 A, inductance × 0.7-1.3 included. 8 V steps need ≥ 6 µs falling, ≥ 10 µs rising (≥ 50 µs at inductance × 0.7). Faster falling ramps: 218-260 A | the valley margin to keep, so how close to high-side ZVS the design may run |
| output routing and copper | lateral at 35 / 86 / 429 µm: 12.3 / 5 / 1 % loss; a vertical output removes most of it | module efficiency |
| inductor matching across modules | ±5 / 10 / 20 % spread: heaviest module +12-16 / +25-34 / +57-79 % loss; co-simulated peak 194 / 208 A at ±5 / 10 % worst case (200 A near ±7 %) | whether passive sharing suffices |
| inductor technology, footprint per phase | MPC-class R/L 79 µΩ/nH (= 170 HBS1 500 nH units per phase): 2.5 MHz best; with 29-40 current-rated units per phase, 86.6-87.7 % and 2.5 MHz best by 0.2-0.6 points; air-core in 0.25-0.63 cm²: 5 MHz; saturation must cover the 200 A transient peak | the switching frequency; the efficiency; the peak-current budget |
| QH / QL placement, loop inductance | 50-300 pH: loop loss 1.4 / 3.8 / 6.4 W at 50 / 100 / 150 pH; ≤ 40 V with turn-on ≤ 3.2 V / L to 150 pH; above, turn-off ≤ 10 V / L at +7 W (200 pH) to +20-28 W (300 pH) | loss, and whether the drive alone can hold 40 V |
| gate drive, turn-on vs turn-off | 72 / 72 A/ns: 42-51 V after a 4.8 V / 1 µs step (50-100 pH); the overshoot follows L × turn-on di/dt (≤ 3.2 V for 40 V), tested 50-300 pH | whether a separate turn-on path is needed |
| derating rule | 40 V continuous used; a 120 % / 1 %-of-life rule would admit 50 pH without the slow turn-on | how much drive slowing is needed |
| loop damping | ring Q 7-30 at 50-100 pH: no change; Q 100, 300 or undamped: valley detection lost from start-up (2400-9000 late edges) even with the slow turn-on | a damping requirement, Q ≤ 30 with an ideal parallel damper; at the ring frequency that is ≳ 4-8 mΩ series-equivalent (Q 7: 19-32 mΩ); the physical source is open |
| series-capacitor technology | ESR ≤ 0.5 mΩ: < 1 %; ESL not yet modelled | ladder ringing |
| output-capacitor placement, processor-side decoupling | the lateral Vo path is 63-628 pH per module (Fig. 5 geometry); with the capacitors at the modules a 1 kA/µs load slew drops 16-157 mV at the processor, faster than the loop (module-to-module ringing ≤ 1 mV) | load-side decoupling or load slew; Vo sensed at the common strip |

Four answers would narrow the package specification most:

1. Can P24's gate driver give the turn-on its own, slower edge (18-36 A/ns)
   while the turn-off stays near 72 A/ns? From the datasheet's gate charge
   that is roughly 5-10 Ω source and ~1 Ω sink resistance per device; with
   no sink resistor the turn-off would reach ~160 A/ns, which alone limits
   the loop to ~60 pH.
2. Which derating rule do you apply to repetitive ns-scale drain overshoot
   on 40 V GaN: the continuous rating, or a transient allowance such as
   EPC's 120 % for ≤ 1 % of life?
3. What is the prototype's commutation-loop inductance? A double-pulse
   V_DS capture would do: a CNN trained on simulated captures, followed by a
   circuit fit, recovers L, Q and di/dt within 1-6 % (probe ≥ 0.7 GHz,
   noise ≤ 0.4 V rms, current known within 2 %). The same capture gives the
   ring's Q, which must stay ≤ ~30. With L known, the drive spec follows
   from the formulas above; above ~150 pH the turn-off must
   slow as well, at several percent of efficiency.
4. How was the start-up on-time set? A slow turn-on needs it raised by
   ~16 ns × (di/dt in A/ns)^-½ plus ~6 ns per nH of loop (formula above).

Otherwise I will continue across the ranges above.

## 5. How the results are checked

- Every experiment registers its pass criteria before it runs; results are
  reported against them, misses included.
- Two independent models check each other: an analytical event map and
  averaged model, and the co-simulation.
- Every controller option reproduces the previous design bit for bit when
  switched off; a regression suite runs on every push.
- Learned models (surrogates, Gaussian processes, CNNs, reinforcement
  learning) propose or flag; the co-simulation decides. An anomaly detector
  trained on clean runs found the ZVS loss behind the package overshoot,
  which no hand-written check covered.
- About 180 experiments and over 60 derivation notes so far. Running status:
  `reports/CURRENT_STATUS.md`; trade-offs: `reports/TRADEOFF_SCORECARD.md`.
