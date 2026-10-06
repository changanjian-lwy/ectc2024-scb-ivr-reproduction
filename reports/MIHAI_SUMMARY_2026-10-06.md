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

- **Efficiency 90.6 %** per module (loss model applied to the simulated
  waveforms; 92.5 % with an ideal inductor).
- **±62.5 A load step:** +15.9 / −12.0 mV, back within 1 % in 6.6 / 3.6 µs.
- **Peak switch current ≤ 196 A** (limit 200 A) on every registered test of
  one module: driver mismatch, 30-100 ps jitter, load steps, ±10 % line
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
   at least 5.3 % for any inductance in P24 Table I. The co-simulation
   agrees: zero voltage first appears at 25 %; at 2 % the high side turns on
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
   with three times the 1 MHz valley margin. With an air-core stripline
   inside Fig. 5's footprint (0.25-0.63 cm² per phase) the optimum moves to
   5 MHz, 2-9 points above 2.5 MHz. The 2.5 MHz design therefore assumes a
   magnetic inductor; at 144 A per phase that is about 29 HBS1-class units
   in parallel (P24: 12 at 62.5 A). P24's Table I (2.68 nH at 5 MHz) and
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
  series-capacitor ESR (≤ 0.5 mΩ) together stay below ~1 %.
- **The loop inductance sets loss; hard turn-ons set the device voltage.**
  With the loop in the circuit model (ring Q 7) and 1-2 ns switching edges,
  the steady high-side peak stays ≤ 34 V up to 150 pH. The loop costs
  1.4 / 3.8 / 6.4 W per module at 50 / 100 / 150 pH, so 1 % allows about
  70 pH. The binding overshoot comes after transients: a rising line step
  makes phase 1 lose ZVS (its valley sits 12-15 A above the floor for
  ~13 µs), its high side turns on hard at 17-19 V, and the ring puts the
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
  start-up on-time of 35.5 ns + 36 A ÷ (turn-on di/dt) restores it (155 A).
- **Resulting specification,** checked on 13 transient tests (line ramps
  2-10 µs, falling steps, inductance × 0.7 / 1.3) and on four modules: loop
  ≤ 50 pH, turn-on 36 A/ns, turn-off 72 A/ns, start-up on-time 36.5 ns →
  switch ≤ 37.6 V, start-up ≤ 198 A, after steps ≤ 180 A. 100 pH works at
  18 A/ns. Above ~150 pH the turn-off ring alone exceeds 40 V (300 pH:
  48.8 V steady), so the turn-off must slow too, at a loss cost. Published
  embedded-GaN loops are 230-320 pH.
- **Rating used:** EPC2067's 40 V continuous rating. The datasheet allows
  48 V transients, and EPC's Phase 16 reliability report allows repetitive
  overshoot up to 120 % for ≤ 1 % of life (measured on 100 V parts). The
  specification does not rely on that rule; without the slow turn-on,
  50 pH would satisfy it and 100 pH would not.

## 4. Open values, with the cases run

| value (not published) | cases | what it decides |
|---|---|---|
| input-bus slew, load-step specification | steps ≤ 4.8 V at any tested slew from 1 µs: ≤ 200 A. 8 V steps need ≥ 6 µs falling, ≥ 10 µs rising. Faster falling ramps: 218-260 A | the valley margin to keep, so how close to high-side ZVS the design may run |
| output routing and copper | lateral at 35 / 86 / 429 µm: 12.3 / 5 / 1 % loss; a vertical output removes most of it | module efficiency |
| inductor matching across modules | ±5 / 10 / 20 % spread: heaviest module +12-16 / +25-34 / +57-79 % loss; co-simulated peak 194 / 208 A at ±5 / 10 % worst case (200 A near ±7 %) | whether passive sharing suffices |
| inductor technology, footprint per phase | MPC-class R/L: 2.5 MHz best; air-core in 0.25-0.63 cm²: 5 MHz | the switching frequency |
| QH / QL placement, loop inductance | 50-300 pH with 1-2 ns edges: loss 1.4 / 3.8 / 6.4 W at 50 / 100 / 150 pH; with the slow turn-on ≤ 38 V to 150 pH; 300 pH 48.8 V steady | loss; above ~150 pH the turn-off must slow too |
| gate drive, turn-on vs turn-off | 72 / 72 A/ns: 42-51 V after a 4.8 V / 1 µs step (50-100 pH); turn-on 36 / 18 / 9 A/ns: ≤ 40 V to 50 / 150 / 150 pH, 9 A/ns too slow | whether a separate turn-on path is needed |
| derating rule | 40 V continuous used; a 120 % / 1 %-of-life rule would admit 50 pH without the slow turn-on | how much drive slowing is needed |
| loop damping | ring Q 7 assumed; undamped, the ring breaks the valley detection | whether the valley detection survives |
| series-capacitor technology | ESR ≤ 0.5 mΩ: < 1 %; ESL not yet modelled | ladder ringing |

Four answers would narrow the package specification most:

1. Can P24's gate driver give the turn-on its own, slower edge (18-36 A/ns,
   e.g. separate source and sink resistors) while the turn-off stays near
   72 A/ns?
2. Which derating rule do you apply to repetitive ns-scale drain overshoot
   on 40 V GaN: the continuous rating, or a transient allowance such as
   EPC's 120 % for ≤ 1 % of life?
3. What is the prototype's commutation-loop inductance? A double-pulse
   V_DS capture would do: a CNN trained on simulated captures, followed by a
   circuit fit, recovers L, Q and di/dt within 1-6 % (probe ≥ 0.7 GHz,
   noise ≤ 0.4 V rms, current known within 2 %). Above ~150 pH the turn-off
   must slow as well.
4. How was the start-up on-time set? A slow turn-on needs it raised by
   ~36 A ÷ (turn-on di/dt).

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
