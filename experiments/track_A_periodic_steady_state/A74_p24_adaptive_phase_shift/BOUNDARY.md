# A74 - P24 phase shifts that follow the measured period (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Question and the cause being tested

A73 reached a periodic P24 state from zero (A73 run 5):
- period 222.891 ns against the nominal T0 = 200 ns;
- Vo 0.9653 V.

**The problem.** In every cycle of that state, phase 4's high side is turned
on by the restart timer, never by ZVS or the valley path. The steady state
therefore depends on a `PROJECT_DECISION` value: the 20 ns restart time.

**Cause proposed in A73.** Mode P times phase k's low-side turn-off at
`t_ref + k*T0/N` (k = 1..N-1). Here `t_ref` is the phase-1 high-side turn-on
of the current cycle.
- The current-sensed phase 1 stretches the period to 222.9 ns.
- Phase 4 is therefore turned off ~17 ns early (150 ns against 3/4 of
  222.9 ns = 167.2 ns). Phases 2 and 3 are ~6 ns and ~11 ns early.
- At that instant phase 4's current is still positive. Its low-side diode
  clamps the node, and there is no resonance to detect.

**Test.** Place the shifts at `k*T_meas/N`, where `T_meas` is the measured
period. If the cause is right:
- phase 4 turns on by ZVS or the valley path in steady state;
- the restart timer no longer fires after convergence;
- the end state does not change when the restart time changes.

## 2. Model used, and why

**The physical model** (A73's simulator, copied): the question is about the
timing of P24's four-phase circuit. The mathematical model is three-phase
and P25-native, and it has no valley trigger yet, so it cannot represent
this case. The cheapest discriminating experiment is a one-rule change in
the simulator.

The matching policy change in the mathematical model (the D41 policy with
period-following shifts) is a follow-up. It is the structural check of
whether the new orbit exists and is stable.

## 3. Sources

**Keeping N phases evenly spaced when the switching period is not fixed.**
This is the standard problem of interleaved critical/boundary-conduction-
mode converters, where every phase's period is set by a current or voltage
event.
- **TI UCC28063A datasheet** (read; public; not in this repository),
  Sec. 8.3.2 "Natural Interleaving". It keeps two transition-mode phases
  near 180 degrees at variable frequency: "the phase-control function
  differentially modulates the on-times of the A and B channels based on
  their phase and frequency relationship". It notes that "some necessary
  phase-error deviation from 180°" is allowed "to maintain equal switching
  frequencies".
- **Master-slave and phase-shift schemes that time the other phases from
  the measured period.** Found on Crossref; not yet read:
  - Yin et al., APEC 2009, DOI 10.1109/APEC.2009.4802834;
  - Choi, APEC 2010, DOI 10.1109/APEC.2010.5433698;
  - Grote et al., ECCE 2011, DOI 10.1109/ECCE.2011.6064198 (digital,
    multi-phase);
  - Yao et al., IEEE TPEL 2025, DOI 10.1109/TPEL.2024.3521997 (interleaved
    multiphase, variable frequency, ZVS).

**How the rule used here is labelled.** It is the simplest period-following
rule. It is a `PROJECT_DECISION` used as a diagnostic, to test the cause in
Section 1. It is not a claim about the best interleaving method. The
papers above are to be read before a control rule is proposed.

## 4. Rule as implemented

- **When it applies.** Mode P only. Mode S (fixed timing, period exactly T0)
  is unchanged.
- **Measured period.** `T_meas` is the time between the last two phase-1
  high-side turn-ons (`t_ref` and the one before). At the handover, the
  previous period is mode S's, i.e. T0.
- **Clamp.** `T_meas` is limited to [0.5, 3]*T0 (`PROJECT_DECISION`: a
  minimum/maximum period guard, as UCC28063A's minimum-period timer). The
  number of clamped cycles is reported.
- **Shifts.** Phase k (k = 2..N) turns its low side off at
  `t_ref + (k-1)*T_meas/N`. Everything else is A73's controller:
  - level-sensitive events;
  - restart timers;
  - the valley path;
  - `diode_check`.

**Code.** `a74_transient.py`, a copy of A73's with:
- the option `adaptive_shift` (default off);
- a log of each high-side turn-on: its mechanism (timed / ZVS / valley /
  restart) and the Vds at turn-on.

A73's files are not modified.

**Regression gate (run 0).** With `adaptive_shift` off and A73 run 5's
settings, A74 replays A73 run 5 over its full length (388.61 us, handover
included). Every section and the end state must be bit-identical. The
replay also supplies the turn-on log for the fixed/20 ns cell.

## 5. Runs

All runs use A73 run 5's sequence and settings:
- Roberts' 30x input ramp, 68.61 us;
- load and handover together at 88.61 us;
- t_end 388.61 us;
- `level_events`, `t_restart_low` 400 ns, stall window 20*T0,
  `diode_check`.

The design is 2 x 2 (shift rule x restart time):

| run | shifts | `t_restart_high` |
|---|---|---:|
| 0 (= A73 run 5, replayed as the gate) | fixed k*T0/N | 20 ns |
| 1 | follow T_meas | 20 ns |
| 2 | follow T_meas | 60 ns |
| 3 | fixed k*T0/N | 60 ns |

Run 3 is the control. If the fixed-shift state depends on the restart time,
its end state differs from run 0's.

## 6. Reporting

- **Turn-on mechanism in the last 50 cycles.** For each phase, the counts of
  ZVS, valley and restart turn-ons, and the mean and maximum Vds at
  turn-on.
- **End state.** Periodic or not (the last 20 sections vary by < 1 mA and
  < 0.1 mV). Period, Vo, ladder ratios, section currents.
- **Stress.** Peak Vds per switch against EPC2067's 40 V; peak phase
  current.
- **Restart dependence.** The end-state difference between the 20 ns and
  60 ns runs, for each shift rule.
- **Clamps.** Number of clamped periods.

## 7. Decides / does not decide

Decides:
- whether the fixed-shift mismatch is the cause of phase 4's restart
  turn-ons in A73's P24 state;
- whether period-following shifts remove the steady state's dependence on
  the restart time.

Does not decide:
- **the controller's implementation.** Clock quantisation of the measured
  period and the shifts, comparator and gate-driver delays, and sensing
  noise are not modelled. The controller here reacts in zero time with
  exact timing;
- the best interleaving method (Section 3 papers, to be read);
- nonlinear Coss, device models;
- the mathematical-model orbit and its stability.

## 8. Amendment (after the progress logs of runs 0-3, before their records were analysed)

**The prediction of Section 1 already fails in the progress logs.** The logs
are printed every 250 cycles. With period-following shifts (runs 1-2),
phases 1-3 are identical between the 20 ns and the 60 ns restart runs, but
phase 4 and Cs3 are not:
- section `i4` is 121.0 A against -2.4 A;
- `VCs3/Vin` is 0.2579 against 0.2661.

The valley count grows by ~3 per cycle, as it does with fixed shifts. Phase
4 still does not ring.

The records of runs 0-3 log only the high-side turn-ons, so the cause
cannot be read from them. A diagnostic log is added to `a74_transient.py`.
- **Every low-side turn-off:**
  - the phase;
  - the phase current at the edge;
  - the time since `t_ref`;
  - the high-side Vds;
  - all phase states.
- **Every high-side turn-on, in addition:**
  - the minimum Vds reached since the low-side turn-off (how far the
    node rose);
  - the time since that turn-off;
  - the phase current.

The log does not change the dynamics. Runs 0 and 1 are rerun with it as
runs 0d and 1d. Each must reproduce its original run bit-identically:
sections and end state.

**Question.** At phase 4's timed low-side turn-off, is its current
positive, so that the node cannot ring? If so, is the cause the timing
(Section 1), or phase 4's current level? Two observations point to the
current level:
- in A73, phase 4's on-state voltage is `VCs3` = 12.38 V, against
  ~11.8 V for phases 2-3;
- in the SCB, the flying capacitors set each phase's volt-second balance
  (Roberts' thesis Sec. 2.3.1).
