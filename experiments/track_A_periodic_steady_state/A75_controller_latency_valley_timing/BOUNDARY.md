# A75 - controller latency and the valley turn-on (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any declared run. One
smoke test preceded it; see Section 8.

## 1. Question and the cause being tested

Every controller in A69-A74 acts in zero time.
- A comparator condition (ZVS, the valley, phase 1's current target)
  changes the gate in the same instant, and every edge lands exactly.
- Real controllers have a latency t_d from the sensed condition to the
  gate edge: comparator, logic and gate driver.
  - TI LMG1210 (the driver A65 used): propagation delay 10 ns typical,
    18 ns maximum; high/low mismatch 1-3.4 ns.
  - Infineon 1EDBx275F (P25's driver): 45 ns (+6/-4 ns).

**Cause proposed.** At P24's point, ZVS is out of reach (A67), so the high
sides turn on by the valley path (A73, A74). A valley is a moving target:
after the minimum, the node rings back within half a resonance period.
- For P24 that is `pi*sqrt(L*(C_high + C_low))` = pi*sqrt(1.467 nH *
  9.30 nF) = 11.6 ns.
- A reactive turn-on therefore lands at `Vds(t_valley + t_d)`. For t_d
  near 11.6 ns, that is close to the next peak.
- A ZVS turn-on is different. The node is clamped by the device's reverse
  conduction, so it tolerates latency as long as the current stays
  negative through t_d.

**The remedy in the literature is prediction.** Chiang and Chen (IEEE TPEL
2009) state that their method "compensates for control circuit delay":
the turn-on signal is generated ΔtD before the target instant, so that the
switch turns on exactly at it. A70 transferred Chiang's two-path logic but
not this compensation, because the model had no delay. TI UCC28063A does
the same in practice: a delay of about 25% of the resonant period after
the ZCD edge, tuned empirically, places the turn-on at the valley.

**Test.**
1. With a realistic t_d, does P24's reactive valley turn-on move away from
   the valley? What does that do to Vds at turn-on and to the steady
   state?
2. Does a predictive (timed) valley turn-on restore it?
3. As a control, does P25's ZVS turn-on tolerate P25's own driver
   latency?

## 2. Model used, and why

**The physical model** (A74's simulator, copied). Latency and timing are
implementation-realism questions, and the event-level mathematical model
has no delays. The one-mechanism change in the simulator is the cheapest
discriminating test.

This is also the cheapest test of whether the missing controller-
implementation layer changes conclusions. That layer would be an HDL
controller with clocking, resolution and latency. If the latency changes
the P24 conclusions, the controller must be designed and described at
that level; an HDL (Verilog) controller co-simulated with the plant is
the standard form. That is a separate, later step.

## 3. Sources

All are read; the datasheets and papers are public, and none is in this
repository.
- **Chiang and Chen**, IEEE TPEL 24(9) 2009 (A70's source): the predictive
  turn-on with delay compensation.
- **TI UCC28063A datasheet**: valley switching by a delay of ~25% of the
  resonant period after ZCD, tuned empirically.
- **TI LMG1210 datasheet**:
  - propagation delay 10 ns typical, 18 ns maximum;
  - delay mismatch 1-3.4 ns;
  - programmable dead time 0.8-20 ns in PWM mode.
- **Infineon 1EDBx275F datasheet**: 45 ns propagation delay.
- **Roberts' PhD thesis** (University of Toronto) and Roberts and Prodić,
  IEEE OJ-PEL 2024. Their SCB controllers run on an FPGA at 125 MHz with
  counter-based DPWMs, i.e. 8 ns resolution. Thesis Chapter 2 bounds the
  flying-capacitor deviation by the DPWM resolution. **Resolution is not
  modelled in A75** (Section 7).

## 4. Controller as implemented

**Latency t_d (mode P only).** It applies to the comparator-triggered
decisions:
- the low side's ZVS turn-on;
- phase 1's low-side turn-off at `i1 <= -2.5 A`;
- the high side's ZVS turn-on and reactive valley turn-on.

When the condition is met, the decision is taken, and the gate edge
follows t_d later. Meanwhile that phase's other events are not evaluated.
- **Timer edges are taken as pre-compensated.** These are Ton's end,
  phases 2..N's timed turn-offs and the restart timers. Every command
  passes through the same driver, so their relative timing is set by the
  timer, not by t_d.
- **Mode S** is timer-only and unchanged.

**Valley modes.**
- **reactive**: A70's path. It fires at `Vds >= Vds_min + 0.05 V`; the
  edge follows after t_d.
- **predictive**: the high side turns on at `t_lo + dt_pred[k]`, a timed
  edge. This is Chiang's predictive turn-on, and equivalent to an adaptive
  dead time. `dt_pred` is per phase and starts at the half resonance
  period (11.6 ns at P24; `NUMERICAL_IDEALIZATION` from the circuit
  values). It is corrected at every predictive turn-on:
  - node still falling at turn-on (early): `dt_pred += 0.2 ns`
    (`PROJECT_DECISION` step);
  - a dip seen and passed (late): `dt_pred` = the observed time of the
    minimum after `t_lo`;
  - a flat node (no ring, e.g. a positive current): unchanged.

  `dt_pred` is capped at 3x the half period. The ZVS path stays reactive
  (with t_d), and the restart timers stay.

**Code.** `a75_transient.py`, a copy of A74's with `t_d`, `valley_mode`
and `dt_step` (defaults: 0, reactive, 0.2 ns). A74's files are not
modified.

**Regression gate (run 0).** With the defaults, run 0 replays A74's
baseline run over its full length. Every section and the end state must
be bit-identical.

## 5. Runs

**P24.** A74's sequence and settings:
- 30x ramp; load and handover at 88.61 us; t_end 388.61 us;
- `level_events`, `t_restart_low` 400 ns, stall window 20*T0,
  `diode_check`;
- the shift rule and restart time of A74's baseline run (Section 9).

| run | valley mode | t_d |
|---|---|---:|
| 0 | reactive | 0 (gate: A74 baseline replay) |
| 1 | reactive | 5 ns |
| 2 | reactive | 10 ns (LMG1210 typ.) |
| 3 | reactive | 18 ns (LMG1210 max.) |
| 4 | predictive | 0 |
| 5 | predictive | 5 ns |
| 6 | predictive | 10 ns |
| 7 | predictive | 18 ns |

**P25 control run.** This is A73 run 7's sequence: the P25 preset, 46 us
ramp, load and handover at 96 us, t_end 696 us, `diode_check`. Its zero-
latency reference is A73 run 7.

| run | valley mode | t_d |
|---|---|---:|
| 8 | reactive | 45 ns (1EDBx275F) |

## 6. Reporting

- **Per phase, over the last 50 cycles:**
  - the turn-on mechanism;
  - Vds at the actual high-side gate edge (mean and maximum);
  - the delayed-edge count.
- **A turn-on loss proxy.** `P_proxy = f_sw * sum_k 1/2 * (C_high + C_low)
  * Vds_on,k^2`. It is a proxy for comparison between runs, not a loss
  figure.
- **End state:**
  - periodic or not (the last 20 sections vary by < 1 mA and < 0.1 mV);
  - period, Vo, ladder ratios, section currents;
  - peak Vds against 40 V (P24) or 100 V (P25);
  - peak current;
  - restarts in the last 50 cycles.
- **Predictive runs:** the final `dt_pred` per phase, and the early / late /
  flat counts.
- **Phase 1:** the current at its low-side turn-off edge (more negative
  with latency).

## 7. Decides / does not decide

Decides:
- whether a latency at the LMG1210's level changes the zero-latency P24
  conclusions (A73, A74);
- whether Chiang-type prediction restores them;
- whether P25's ZVS turn-on tolerates 45 ns in this model.

Does not decide:
- **timing resolution.** Clock quantisation of the timers, the measured
  period and the shifts (8 ns on Roberts' 125 MHz FPGA; delay-line DPWMs
  go below 1 ns);
- channel mismatch, comparator offsets and noise, and the real valley-
  detector circuit;
- **loss.** The proxy is not a loss model;
- **predictive tuning.** Only one correction step is tested;
- nonlinear Coss and device models;
- the mathematical-model counterpart.

## 8. Smoke test before this boundary

This test is not a declared run. Its record was deleted, and no
conclusion rests on it.
- **Purpose:** to check that the code runs.
- **Setup:** the P25 preset from A69's lossless D41 section, t_d = 45 ns,
  20 us.
- **Seen:** high-side "ZVS" edges landed at Vds 1.0-2.3 V instead of ~0.
  A likely reason: P25's -2.5 A reverses within ~25 ns at
  `(Vx - Vo)/L` ≈ 0.1 A/ns, so the reverse conduction ends before the
  45 ns edge.

This is why run 8 is declared. That result will be taken from run 8, not
from the smoke test.

## 9. Baseline (fixed before any declared run)

**The P24 baseline is fixed shifts `k*T0/N` with `t_restart_high` 20 ns.**
That is A74 run 0, the bit-identical replay of A73 run 5.

Why: A74's progress logs show that period-following shifts do not change
phase 4's turn-on mechanism (A74 BOUNDARY Section 8). A75's subject is the
valley turn-ons of phases 1-3, which have the same structure under both
shift rules. The baseline is therefore the established state.

**Regression gate.** Run 0 must reproduce A74 run 0 bit-identically. The
pair is listed in `gate_pairs.json`.

**Code change before the runs.** A75 carries A74 Amendment 8's diagnostic
log: low-side turn-offs, and the extra fields of each high-side turn-on.
It does not change the dynamics, which the gate checks.
