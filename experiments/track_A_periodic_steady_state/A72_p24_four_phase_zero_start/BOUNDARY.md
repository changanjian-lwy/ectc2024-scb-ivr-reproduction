# A72 - the A71 start-up sequence on P24's four-phase module (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Question

A71 took the P25-scale three-phase SCB from all-zero state to its periodic
section. The steps were:
- fixed timing with the input ramped at Roberts' 30x rate and no load;
- the load and P25's current-sensed control, with the Chiang valley
  fallback, switched on together.

Does the same sequence work on the converter this project reproduces?
That is P24's module: four phases, 48 V -> 1 V, 5 MHz, EPC2067, where A67
says ZVS cannot be reached at P24's 1-2% negative current. Specifically:
1. Does the series-capacitor ladder track the ramp?
2. Do the switch voltages stay under EPC2067's 40 V rating (Kim et al.,
   TPEL 2018: SCB start-up stress)?
3. Does the controller settle on a periodic state, and does every high
   side then turn on by the valley path, as A67 predicts?

## 2. Circuit (P24 values as the project already uses them)

| item | value | label / source |
|---|---|---|
| topology | `vin-SH1-a1-SH2-a2-SH3-a3-SH4-x4`, `SLk: xk-0`, `Csk: ak-xk` (k = 1-3), `Lk: xk-out` | P24 Fig. 1 (four-phase SCB) |
| Vin | 48 V, ramped | `P24_EXPLICIT` |
| L per phase | 1.4666667 nH | P24 Eq. 4 branch (Track A/B `LOCKED`) |
| Cfly (Cs1-3) | 3 uF | Track A/B corrected first-principles value, `SENSITIVITY_ONLY` |
| Cout | 4.672 mF | inherited from Track A/B; Track B README flags it as a cross-topology EPE2019 figure (suspect) |
| load | 4 mOhm resistive (1 V^2 / 250 W), switched on at `t_load` | Track A (A56-A64) / Track B convention |
| switches | 2 (high) / 3 (low) EPC2067 per switch | Table 3 4-module row (Track A) |
| Coss, linear | 1860 pF per device (datasheet Co(tr)): high side 3.72 nF, low side 5.58 nF | `EXTERNAL_DEVICE_DATA`; the project's time-equivalent view (A59) |
| series R per phase | 0.54 mOhm = duty-weighted Ron (1.55 mOhm per device; D = 1/12) | `PROJECT_DECISION`, first order as in D42; inductor DCR 0 as in Track A |
| ON / diode resistance | 0.1 uOhm | `NUMERICAL_IDEALIZATION` (A69 5a) |

## 3. Controller

As A71, generalised to N = 4:
- **Mode S (fixed timing).**
  - T0 = 200 ns, Ton = 16.667 ns (P24 Eq. 3, `P24_EXPLICIT`).
  - Phase 1's low side turns off at `t_on1 + T0 - t_dead`; phases 2-4 at
    `t_ref + (k-1)*T0/4`.
  - The fixed dead time is `t_dead` = 2.15 ns (A51/A52's constant,
    inherited).
- **Mode P** (P25's single-sensor rule, transferred as D41/A70 did).
  - Phase 1's low side turns off at `i1 <= -2.5 A`: 2% of the ~125 A
    ripple, within P24's stated 1-2% (`PROJECT_DECISION` inside a
    `P24_EXPLICIT` range).
  - Phases 2-4 use the same fixed shifts.
  - The low side turns on at ZVS of SLk.
  - The high side turns on at ZVS or by the valley path (A70,
    `dV_hys` 0.05 V).
- **Handover** at the first phase-1 high-side turn-on at or after
  `t_hand`, as in A71.

## 4. Code and regression gate

`a72_transient.py` generalises A71's simulator to N phases and to either a
constant-current or a resistive load. A71's files are not modified.

Gate, before any P24 run: with N = 3, P25 values and the constant-current
load, the first 30 us of A71 run 6 (`handover_with_load_ramp46`) must be
reproduced. The requirement is the same section count and every section
within 1e-9 V / 1e-9 A.

## 5. Runs

Ramp time from Roberts' rule applied to P24, as derived in Track B
(`ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`): f1,4 = 153.0 kHz at 3 uF.
The 30x ramp is **68.61 us**, the same value Track B's R04E17 used.

| run | t_ramp | t_load = t_hand | t_end |
|---|---:|---:|---:|
| 1 main (30x) | 68.61 us | 88.61 us | 388.61 us |
| 2 fast (3x) | 6.861 us | 26.86 us | 326.86 us |
| 3 control: mode P from t = 0 | 68.61 us | 88.61 us (load only) | 388.61 us |

h = 10 ps. Output-LC settling (L/4 with 4.672 mF, R 4 mOhm) has a time
constant of ~37 us, so 300 us after the handover covers ~8 time constants.

## 6. Reporting

- **Ladder.** `|VCsk/Vin - (4-k)/4|` over the ramp, by Vin band.
- **Stress.** The peak `Vds` of every switch over the whole run, against
  40 V. The peak phase current.
- **End state.**
  - Periodic: the last 20 sections vary by < 1 mA and < 0.1 mV.
  - Report the section state, the period, Vo, and the valley firings per
    cycle in steady state (A67 predicts four per cycle, at Vds ~10 V).
  - Otherwise report a stall or oscillation as it falls.

## 7. Decides / does not decide

Decides:
- whether the A71 sequence, the valley fallback and the handover rule
  take the idealised P24 module from all-zero state to a periodic state,
  within device voltage ratings.

Does not decide:
- Track B's divider precharge. Not modelled here; the question is whether
  the ramp alone suffices.
- Nonlinear Coss, vendor models, gate drivers, closed-loop Ton,
  temperature.
- Whether Cout = 4.672 mF is right. It is inherited and suspect;
  sensitivity is only reported if a run shows it matters.

## 8. Amendment (after runs 1-3, before runs 4-8)

Runs 1-3 showed four things.
1. **The ladder fails to track under mode S, even with no load.**
   `VCs/Vin` jumps between ~0.02 and ~0.97 with a ~10 us pattern. The
   peak phase current grows with Vin to 423 A. The switch Vds peaks at
   47.6 V (SH3), above EPC2067's 40 V.
2. **The run-1 "stall" 18 us after the handover is probably false.**
   The handover came from an unbalanced ladder (`VCs/Vin` 0.51 / 0.48 /
   0.41). Phase 1 then rises by ~250 A in one Ton and needs ~670 ns at
   Vo = 0.55 V to return to -2.5 A. That exceeds the 3*T0 = 600 ns stall
   window, and i1 was still falling (7.5 A) when the run stopped.
3. **Run 2 (fast ramp) stalled for real,** with phase 2 in UP. A likely
   cause is a positive current at the timed low-side turn-off: the
   low-side diode conducts, so the node has no resonance and neither the
   ZVS nor the valley path can fire.
4. **Run 3** stalled at 0.6 us, as expected.

Track B's R04E16 with the same ramp (68.61 us, ramp only) did not run
away: peak IL1 86.9 A. Its netlist differs:
- complementary gates with no dead time;
- no device capacitances;
- the load connected throughout;
- input parasitics of 5 nH and 10 mOhm.

Added runs, mode S only (no handover), t_end = t_ramp + 20 us = 88.61 us,
as a 2 x 2 factorial to find which factor drives the ladder oscillation:

| run | t_dead | load during the ramp |
|---|---:|---|
| 4 | 2.15 ns | off (as run 1) |
| 5 | 0.05 ns | off |
| 6 | 2.15 ns | on from t = 0 (4 mOhm) |
| 7 | 0.05 ns | on from t = 0 |

A 0.05 ns dead time is the nearest this event scheme gets to Track B's
complementary gates: five 10 ps steps.

Run 8 is run 1 rerun with the stall window widened to 20*T0 = 4 us, to see
what mode P does after the handover. From run 8 on, P24 runs use 20*T0.
The code change adds only the stall window and a `--t-dead` option; the
defaults reproduce runs 1-3.

## 9. Amendment (after runs 4-8, before runs 9-10)

Runs 4-7 (mode S only, 2 x 2): the ladder fails in all four cells.
- The maximum ratio deviation is 0.44-0.49.
- The peak currents are 427-510 A.
- The switch voltage peaks at ~47.6 V, above the 40 V rating.

Neither the dead time nor the load explains it. Track B's R04E16 (ramp
only) also ends unbalanced: VCs 19.9 / 13.2 / 6.6 V against 36 / 24 / 12,
Vo 0.56 V. Only R04E17's divider precharge reached 35.8 / 23.8 / 11.9 V
and Vo 1.006 V. At P24 the ramp alone does not balance the ladder, in
either model.

Run 8 (stall window 4 us), after the handover:
- mode P pulled the ladder to 0.747 / 0.500 / 0.261;
- the valley path fired on almost every edge, as A67 predicts;
- a phase-4 section current then crept up by ~0.65 A per cycle;
- a hard valley turn-on at 18.7 V upset the state, Vo went to -0.34 V,
  and the run stalled.

Two controller-implementation gaps were found.
1. **Crossing-only event detection.** Events fired only on a crossing.
   A condition already met on entering a state (e.g. i1 = -265 A <
   -2.5 A at the start of LOW; run 2: i1 = -316 A) never fired. A
   comparator-based controller is level-sensitive, so this is corrected:
   `level_events`, a condition met at step start fires at once.
2. **No resonance, no valley.** When the current at a timed low-side
   turn-off is positive, the low-side diode clamps the node. Neither ZVS
   nor the valley can then occur (run 2: phase 2 in UP with i2 =
   +109.5 A, Vds(SH2) flat at 33.7 V).

   Published practice for valley/ZCD-triggered controllers is a
   **restart timer** that forces the turn-on when the expected signal
   does not come:
   - TI UCC28051 datasheet: the restart timer sets the gate high if it
     stays off more than 400 us nominal, 200 us minimum;
   - TI UCC28063A datasheet: an on-time is generated if no ZCD
     negative-going edge is detected for the restart time,
     165/210/265 us.

   Transferred as `CROSS_PAPER_EXTENSION`, with values as
   `PROJECT_DECISION`:
   - the UP and DOWN waits turn on 20 ns after the low-side or high-side
     turn-off (~10x the 2.15 ns commutation);
   - phase 1's current-target wait turns the low side off 400 ns (2*T0)
     after it turned on.

Added runs, with all fixes on (`level_events`, both restart timers, stall
window 20*T0). Defaults leave runs 1-8 reproducible.
- 9: as run 8 (30x ramp, load and handover at 88.61 us, t_end 388.61 us).
- 10: as run 2 (3x ramp, load and handover at 26.861 us, t_end 326.861 us).

Question: with these fixes, does mode P, started from the unbalanced
ramp-only ladder, settle on a periodic state? The mode-S overvoltage
during the ramp is unaffected by these fixes. It still calls for
precharge.
