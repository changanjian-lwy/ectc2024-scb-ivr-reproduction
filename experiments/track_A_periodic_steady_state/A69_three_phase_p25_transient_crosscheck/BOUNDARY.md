# A69 - physical-model cross-check of the mathematical model's D41 orbit (BOUNDARY)

Track A, `SENSITIVITY_ONLY` / cross-check. Written before any run.

## 1. Question

The mathematical model (D41, commit 71ff6ab) finds a periodic section of the
P25-native three-phase SCB at P25 scale under single-sensor phase-shift
control. The orbit has:
- a period of 1946.41 ns and ZVS on all three high sides;
- a residual at the noise floor after one cycle;
- a weakly unstable complex eigenvalue pair, |lambda| = 1.060, in the
  lossless model.

With 0.5 mOhm series resistance (D42) the orbit returns formally, with
|lambda| = 1.043.

Does an independent time-domain simulation of the same circuit and control
reproduce these results? That means the same section state, the same period
and the same slow drift away from the orbit.

## 2. Independence

A69 does not use the mathematical model's code:
- no affine flows;
- no event-root location;
- no entry contracts, control memory or section functions.

It is a separate program with a different numerical method:
- a fixed-step trapezoidal integration of the nodal equations. Backward
  Euler is used for the first two steps after any topology change, to damp
  switching ringing;
- switches are resistors when ON;
- reverse conduction is a resistive diode branch when the OFF switch's Vds
  is below zero;
- the controller checks its conditions once per step.

The mathematical model's results are used only as the initial state and as
the reference for comparison.

## 3. Circuit and values (matched to D41)

- **Topology.** P25 Fig. 1: `vin-SH1-a1-SH2-a2-SH3-x3`, `SLk: xk-0`,
  `Cs1: a1-x1`, `Cs2: a2-x2`, `Lk: xk-out`, `Co: out-0`, and a
  constant-current load.
- **Values.**
  - 12 V input;
  - 30 nH per phase;
  - Coss 0.69 nF on each high side and 1.38 nF on each low side, linear;
  - Cs1 = Cs2 = 100 uF;
  - Co = 100 uF;
  - 67.5 A load;
  - Ton 500 ns;
  - negative target -2.5 A (alpha 5% of 50 A) on phase 1 only;
  - phase shifts 666.67 ns and 1333.33 ns after phase 1's high-side
    turn-on.
- **Idealisation parameters** (`NUMERICAL_IDEALIZATION`): switch ON
  resistance 10 uOhm; diode ON resistance 10 uOhm; OFF branches carry only
  their Coss.
- **Series resistance.** Two cases: 0 (lossless, vs D41) and 0.5 mOhm per
  phase (vs D42).

## 4. Controller (the D41 rule, re-implemented)

- **Phase 1.**
  - SH1 turns on when `V(vin) - V(a1) <= 0` after SL1 has turned off.
  - SH1 turns off after Ton.
  - SL1 turns on when `V(x1) <= 0`.
  - SL1 turns off when `i1 <= -2.5 A`.
- **Phases 2 and 3.** The same, except that SLk turns off at
  `t_ref + shift_k`, where `t_ref` is phase 1's latest high-side turn-on.
  SH2 turns on at `V(a1) - V(a2) <= 0`; SH3 at `V(a2) - V(x3) <= 0`.
- **Section.** Each phase-1 high-side turn-on is a section. The recorded
  state is (a2, x1, out, i1, i2, i3), the mathematical model's section
  coordinates.

## 5. Procedure and acceptance

1. **Initial state.** Start from D41's (or D42's) section state, with a1
   at vin (SH1 on) and x2 = x3 = 0.
2. **Run length.** Run 150 cycles.
3. **Step-size check.** Use h = 10 ps. Repeat the first 20 cycles at 5 ps.
4. **Cycle-1 comparison.** Compare against the mathematical model's
   section after one cycle and its period.
   - Declared agreement: period within 0.2 ns; currents within 0.05 A;
     voltages within 5 mV.
   - The fixed step bounds event timing to +/-h, which dominates this
     tolerance.
5. **Drift.** Fit the growth of the section-state deviation over cycles and
   compare it with |lambda|.

## 5a. Amendment (before the long runs)

The first 5-cycle smoke runs used a 10 uOhm ON/diode resistance, as in
Section 3. They showed a cycle-1 period offset of -249.5 ps, with -9 mA /
-6 mA in i2/i3.
- The offset is unchanged at h = 5 ps, so it is not discretization.
- It scales exactly with the ON resistance: -25.9 ps at 1 uOhm and -3.5 ps
  at 0.1 uOhm.

It is the resistive drop, about 5e-4 of Vo, acting over the ~1.5 us
current decay. The ON/diode resistance for all further runs is therefore
0.1 uOhm (`NUMERICAL_IDEALIZATION`). The smoke-run files are kept.

## 6. Decides / does not decide

Decides:
- whether the mathematical model's orbit, and its weak instability, are
  properties of the circuit, not of the event machinery.

Does not decide:
- real-device behaviour (GS61008T vendor model);
- closed-loop control;
- start-up.
