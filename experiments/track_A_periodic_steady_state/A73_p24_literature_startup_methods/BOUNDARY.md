# A73 - P24 start-up with the published ladder-control methods (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Question and the cause being tested

A72 found that P24's four-phase ladder does not follow an open-loop,
fixed-timing input ramp. Vds reached 47.6 V against EPC2067's 40 V rating,
and P25's control could not rebalance the ladder afterwards. The literature
read on 2026-09-29 names the cause: **open-loop natural balancing is too
slow**. Xia and Stauth measured 3.5 ms open-loop against 25 us closed-loop
recovery. Their remedy, and Wei et al.'s, is to control the flying-capacitor
voltages in proportion to Vin.

A73 tests that cause directly, with two published remedies:
- **Method 1.** Ratio-preserving precharge, then a soft start. If the
  ladder starts balanced, do switching, the load and the handover stay
  within the rating and settle? This separates "an unbalanced start" from
  "the P24 operating point itself". A72 run 8 drifted near balance, so the
  latter is not ruled out.
- **Method 2.** Closed-loop active balancing during the input ramp. Does
  switching-node feedback keep the ladder proportional where A72's open
  loop did not?

## 2. Sources

- **Wei, Ramadass, Ma**, IEEE JSSC 56(8) 2021, DOI 10.1109/JSSC.2021.3053457,
  Sec. IV. They precharge the flying capacitors before regulation, at rates
  in proportion to their targets (dVCF1/dt = 2 dVCF2/dt), so all targets
  are reached together and the switches stay below their rating.
- **Kim, Cha, Park, Lee**, IEEE TPEL 33(1) 2018, DOI 10.1109/TPEL.2017.2705705,
  Sec. IV: an SCB soft start with the duty ramped from zero.
- **Xia and Stauth**, IEEE JSSC 57(6) 2022, DOI 10.1109/JSSC.2022.3162166,
  Sec. III-A. Their balancing sliding mode integrates `(Vx - Vin/4)` over
  each odd (charging) state and shortens the state when the average Vx is
  below Vin/4 (longer when above). This gives negative feedback on the
  flying-capacitor deviation.
- **A72's controller fixes carried over:**
  - level-sensitive events;
  - restart timers (TI UCC28051/UCC28063A practice);
  - a stall window of 20*T0.

## 3. Circuit

A72's P24 circuit, unchanged:
- 48 V; 1.4667 nH; Cfly 3 uF; Cout 4.672 mF (inherited, suspect);
- 4 mOhm load; linear Coss 1860 pF per device;
- 0.54 mOhm per phase; t_dead 2.15 ns; T0 200 ns; Ton 16.667 ns.

The code is `a73_transient.py`, a copy of A72's with the options below.
A72's files are not modified.

**Regression gate.** With all new options off, the first 20 us of A72 run 4
(`s_ramp_td2p15_noload`) must be reproduced bit-identically.

## 4. Methods as implemented

**Method 1: precharged ladder plus duty-ramp soft start.**
- **Initial state.** VCs = (36, 24, 12) V with Vin = 48 V held from t = 0,
  and Vo = 0, all currents 0.
  - This is the end state of an ideal Wei-type ratio precharge
    (`NUMERICAL_IDEALIZATION`: the precharge circuit itself is not
    modelled).
  - The output capacitor is not precharged. In Wei, precharge concerns
    the flying capacitors only.
- **Soft start, mode S.** Ton ramps linearly from 0 to 16.667 ns over
  t_ss = 86 us.
  - This is Roberts' 30x rule applied to the output filter:
    `f_out = 1/(2 pi sqrt((L/4) Cout))` = 121.6 kHz, and
    `30 * 0.35/f_out` = 86.3 us.
  - Carrying the rule over from the flying-capacitor mode to the output
    mode is a `PROJECT_DECISION`.
- **Then the A71 handover:** load and mode P together at t = 106 us.

**Method 2: closed-loop balancing during the ramp** (A72 run 1's sequence,
with mode S's high-side on-time modulated).
- **Rule.** Phase k's high state ends when its "effective time" `tau_k`
  reaches Ton, with
  `d tau_k/dt = clip(1 - k_b * (V(x_k) - Vin/4)/(Vin/4), 0.25, 4)`.
  - V(x_k) below Vin/4 therefore shortens the state, as in Xia and
    Stauth's rule.
  - A hard cap of 2*Ton applies.
  - Below Vin = 2 V the rate is 1 (no sensing at a near-zero input).
- **Gain.** `k_b` has no transferable value: Xia's is `gm/Cbal`, a circuit
  constant. Runs use `k_b` = 1 and 3 (`PROJECT_DECISION` /
  `SENSITIVITY_ONLY`).
- **Scope.** Mode P after the handover is unchanged: P25's rule, with no
  balancing term.

## 5. Runs

| run | method | details | t_end |
|---|---|---|---:|
| 1 | M1 | precharged ladder, 86 us Ton ramp, load + handover at 106 us | 406 us |
| 2 | M2 | k_b = 1; Vin ramp 68.61 us; load + handover at 88.61 us | 388.61 us |
| 3 | M2 | k_b = 3; otherwise as run 2 | 388.61 us |

## 6. Reporting

- The peak Vds per switch against 40 V, over the whole run, and before the
  handover.
- The ladder deviation `max |VCsk/Vin - (4-k)/4|`:
  - during the ramp or soft start (Vin ≥ 12 V);
  - at the handover;
  - at the end.
- The peak phase current.
- The end state: periodic (the last 20 sections vary by < 1 mA and
  < 0.1 mV), drifting, or stalled. Valley and restart firings per cycle
  in the final 50 cycles.

## 7. Decides / does not decide

Decides:
- whether A72's failure is due to the open-loop ladder (then run 2 or 3
  succeeds);
- whether, given a balanced ladder, the P24 operating point under mode P
  is itself reachable and steady (run 1).

Does not decide:
- the precharge circuit's own design;
- real sensing and gate drive;
- nonlinear Coss;
- the right value of `k_b`;
- whether mode P needs its own balancing term. If run 1 shows mode P
  drifting from a balanced start, that becomes the next question.

## 8. Amendment: a simulator defect found before any A73 run (2026-09-29)

**The defect.** The first smoke test of run 1 lost the precharged ladder
within 2 us. The capacitor voltages jumped by ~11 V in single 10 ps steps.
Instrumenting the step showed SL1, gate off and conducting only through its
diode branch, carrying **+3.4 MA drain->source** at t = 200 ns, the instant
SH1 was turned on.

The cause: since A69, a reverse-conduction branch is a 0.1 uOhm resistor
whose on/off state is updated only at step boundaries. Within a step it
therefore conducts in **both** directions. When a switch is turned on while
the opposite device's diode conducts (a hard turn-on with a positive
current at a timed low-side turn-off, or the mirror case), the input is
shorted through that "diode" for one step. The flying capacitor is then
charged by several volts. A real diode blocks that direction, so the node
simply rises: hard switching of Coss.

**Which earlier results are affected.** Any run with hard turn-ons against a
conducting opposite diode:
- A72, all runs: fixed timing with positive currents at the timed
  turn-offs;
- A71's mode-S-under-load oscillation: runs 1, 2 and 4.

Runs where every turn-on happened at ZVS, or at a free resonance valley,
are not affected: the A69 orbit checks, A70, and A71 runs 5 and 6. This is
checked below by counting diode corrections.

**The fix, `diode_check`.** After every step, a diode-only branch whose
Vds ends above 0 (drain->source current) is turned off, and the step is
recomputed. This repeats until no branch violates. The default is off, so
the regression gates still reproduce A72; its default setting was
re-verified as bit-identical. With the fix, the run-1 smoke test holds the
ladder at 35.98 / 23.99 / 12.13 V. Peak Vds is 24.0 V, the normal SCB peak
of 2*Vin/N on SH2-SH4 while the preceding phase is on.

**Runs, all with `diode_check`.** The A73 runs 1-3 are as declared above.
Re-checks of the affected earlier conclusions use this simulator (`--preset
p25` = A71's circuit):

| run | re-check of | settings |
|---|---|---|
| 4 | A72 run 4 (P24 ramp only, mode S, no load) | t_ramp 68.61 us, no load, t_end 88.61 us |
| 5 | A72 run 9 (P24 ramp, then load + handover, controller fixes) | as A72 run 9 |
| 6 | A71 run 4 (P25 mode S under load 400 us) | P25, t_ramp 46, t_load 96, no handover, t_end 496 us |
| 7 | A71 run 6 (P25 load + handover with fast ramp) | P25, t_ramp 46, t_load = t_hand = 96, t_end 696 us |

Corrections to A71's and A72's RESULTS are written after these runs.

## 9. Amendment (after runs 1-7, before run 8)

Run 6 showed that the "mode S under load never settles" finding of A71 is
an artefact. With `diode_check`, it settles within 100 us. A71's
recommendation to hand over together with the load rested on that finding,
and A71 run 1 (handover 100 us after the load) stalled. That run is
therefore re-checked:

| run | re-check of | settings |
|---|---|---|
| 8 | A71 run 1 | P25, t_ramp 457, t_load 507, t_hand 607, t_end 1207 us, `diode_check` |

## 10. Amendment (after runs 1-7, with run 8 running)

A69's deadlock and A70's valley-fallback recovery were computed with the
same bidirectional diode branch. The deadlock itself was a wait on a
resonance, which looks independent of the defect. The transient before it,
however, may have contained hard turn-ons against a conducting diode. Both
are re-checked with `diode_check`, starting from the lossless D41 section
(A69 `ref_D41_lossless.json`) with the D42 4.9 mOhm circuit (P25 preset):
Vin held at 12 V, the CC load on from t = 0, mode P from t = 0, t_end 541 us
(~250 cycles).

| run | re-check of | valley path |
|---|---|---|
| 9 | A69 deadlock (`damped4p9` from the lossless orbit) | off |
| 10 | A70 run 2 (`deadlock_start_4p9`) | on (`dV_hys` 0.05 V) |

The A69 simulator started with SH1 on, SL2 and SL3 on, a1 = Vin and
x2 = x3 = 0; `init_z` reproduces that. A69 had no restart timers and used
crossing-only events. Runs 9-10 use neither fix, so that only the diode
model differs.
