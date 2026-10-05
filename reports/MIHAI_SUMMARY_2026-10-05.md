# SCB-IVR reproduction: progress since 14 September

Changan Jian · 5 October 2026 ·
[github.com/changanjian-lwy/ectc2024-scb-ivr-reproduction](https://github.com/changanjian-lwy/ectc2024-scb-ivr-reproduction)

Since our meeting the work has moved from checking one module's switching
sequence to a closed-loop design of the full 48 V → 1 V, 1 kW system of the
ECTC 2024 paper (P24):

- one four-phase module and the four-module, 16-phase system both run in
  co-simulation: a Verilog controller against a circuit model with the
  datasheet's nonlinear Coss and reverse conduction, cross-checked against
  analytical models;
- both controller designs are frozen after randomised testing;
- the package level (P24 Figs. 5-6) has started.

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
   copper loss rises from 2.6 to 13.8 W (L ∝ 1/f). A first-principles
   stripline inductor in P24's in-package footprint (≤ 2 cm² per phase)
   puts the optimum at 2-5 MHz, never 1 MHz; hence 2.5 MHz (90.6 % against
   90.2 % for the best 5 MHz design). P24's Table I (2.68 nH at 5 MHz) and
   Eq. (4) (1.47 nH) disagree; this work follows Eq. (4).
4. **Interleave errors grow with the phase count.** A 9.4 ns slot offset,
   invisible on one module (N·D = 0.31), gave 45.9 A rms of 16-phase output
   ripple instead of 6.75 A rms (N·D = 1.22). Referencing every slot to
   phase 1's low-side turn-off removed it.
5. **Current sharing,** which P24 names as the primary challenge without a
   method: with one common on-time the modules share by their inductance
   (+5 % L: −4.6 % current; +10 %: −8.8 %, still soft-switched), with no
   per-module current sensing.
6. **Fast input steps need a feed-forward.** ±4.8 V steps over 1 µs peaked
   at 216-218 A. A Vin feed-forward found with reinforcement learning, then
   reduced to a six-parameter rule and built in Verilog, brings them to
   ≤ 182 A at no steady-state cost. Learning was used only as a search
   tool; an earlier policy that exploited its reward was rejected.

P24 does not describe the controller, start-up or module synchronisation;
these are this work's choices, taken from the critical-mode PFC
interleaving literature.

## 3. Package level (started 5 October)

P24 Figs. 5-6 give the layout but no copper, via or loop values, so these
are budgets over plausible ranges:

- **Lateral output copper dominates.** Fig. 5 routes each phase sideways to
  a central Vo / GND strip. With one 35 µm layer each way this costs 30.7 W
  per 250 W module (12.3 %), more than the converter's own 25.9 W. 5 % needs
  86 µm of copper per stack, 1 % needs 429 µm. Vias, the strip and the
  series-capacitor ESR (≤ 0.5 mΩ) together stay below ~1 %.
- **The commutation loop limits the device voltage.** For the 40 V EPC2067,
  a high-side turn-off at 143 A allows at most 141 pH of loop inductance
  (energy bound); at 200 A, 72 pH. Published embedded-GaN loops are
  230-320 pH.
- **In progress:** the loop inductance is now in the circuit model; a
  single-edge check agrees with the bound within 1.5 V. Next: a 50-300 pH
  sweep on the frozen design, measuring the overshoot and whether the
  controller's V_DS valley detection survives the ringing.

## 4. Open values, with the cases run

| value (not published) | cases | what it decides |
|---|---|---|
| input-bus slew, load-step specification | steps ≤ 4.8 V at any tested slew from 1 µs: ≤ 200 A. 8 V steps need ≥ 6 µs falling, ≥ 10 µs rising. Faster falling ramps: 218-260 A | the valley margin to keep, so how close to high-side ZVS the design may run |
| output routing and copper | lateral at 35 / 86 / 429 µm: 12.3 / 5 / 1 % loss; a vertical output removes most of it | module efficiency |
| QH / QL placement, loop inductance | 50-300 pH (next experiment) | turn-off overshoot on 40 V devices; valley detection |
| series-capacitor technology | ESR ≤ 0.5 mΩ: < 1 %; ESL not yet modelled | ladder ringing |

If you know which of these cases is closest to the intended build, it
would narrow the sweeps; otherwise I will continue across the ranges above.

## 5. How the results are checked

- Every experiment registers its pass criteria before it runs; results are
  reported against them, misses included.
- Two independent models check each other: an analytical event map and
  averaged model, and the co-simulation.
- Every controller option reproduces the previous design bit for bit when
  switched off; a regression suite runs on every push.
- About 150 experiments and 65 derivation notes so far. Running status:
  `reports/CURRENT_STATUS.md`; trade-offs: `reports/TRADEOFF_SCORECARD.md`.
