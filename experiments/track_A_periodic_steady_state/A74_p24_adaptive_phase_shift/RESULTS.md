# A74 - P24 phase shifts that follow the measured period (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`. Boundary: `BOUNDARY.md`, with Amendment 8
written after the progress logs of runs 0-3 and before the diagnostic
reruns. Records:
- `run_*.json`;
- `a74_summary.json`: the 2 x 2 table and the regression gate;
- `a74_diag.json`: the diagnostic reruns;
- `regression_gate_vs_A73.json`.

**Model: the physical model** (A73's simulator, copied). The question is
the timing of P24's four-phase circuit. The mathematical model is
three-phase P25-native and has no valley trigger (BOUNDARY Section 2).

## 0. Verdict

**The cause proposed in A73 is refuted.** Shifts that follow the measured
period do not change phase 4's turn-on. In all four cells of the 2 x 2
(shift rule x restart time), phase 4's high side is turned on by the
restart timer in every cycle (50 of 50 in the last 50 cycles), at
Vds ≈ 11.03 V.

**Phase 4's problem is its current level, not its timing.** The diagnostic
log gives each phase's current at its low-side turn-off:

| phase | low-side turn-off | current at the turn-off | high-side turn-on |
|---|---|---:|---|
| 1 | current comparator | -2.50 A | valley, 11.8 ns later, Vds 9.87 V |
| 2 | timed | -3.35 A | valley, 11.1 ns later, Vds 9.79 V |
| 3 | timed | -3.35 A | valley, 11.1 ns later, Vds 9.79 V |
| **4** | timed | **+7.08 A** | **restart timer, 20 ns later, Vds 11.03 V** |

These are the means over the last 50 cycles of rerun 0d (fixed shifts).
Rerun 1d (period-following shifts) gives the same values to 0.01 A and
0.01 V.

The shift rule moved phase 4's turn-off from `t_ref` + 150.0 ns to
`t_ref` + 167.2 ns, but its current at the turn-off stayed +7.08 A. Its
whole waveform moves with the shift. Phase 4 therefore runs ~10 A above
phases 2-3 at the equivalent point of its cycle.

**What happens in each phase-4 cycle:**
1. At the turn-off, the current is positive, so the low-side diode clamps
   the node.
2. The current crosses zero ~11 ns later, and only then does the node
   start to ring. This is an estimate from the slope `-Vo/L` ≈
   -0.66 A/ns; at the restart edge the log shows -1.44 A.
3. The 20 ns restart timer turns the high side on while the node is still
   rising: the minimum Vds since the turn-off equals the Vds at turn-on,
   11.03 V.

## 1. The 2 x 2 runs

| run | shifts | restart | period | Vo | `VCs/Vin` | peak Vds | peak i | phase 4 (last 50 cycles) |
|---|---|---:|---:|---:|---|---:|---:|---|
| 0 (= A73 run 5) | fixed k*T0/N | 20 ns | 222.891 ns | 0.9653 V | 0.7487 / 0.5034 / 0.2579 | 24.8 V | 161 A | restart 50/50, 11.03 V |
| 1 | follow T_meas | 20 ns | 222.883 ns | 0.9651 V | 0.7487 / 0.5034 / 0.2579 | 24.8 V | 157 A | restart 50/50, 11.03 V |
| 2 | follow T_meas | 60 ns | 222.876 ns | 0.9649 V | 0.7487 / 0.5034 / 0.2661 | 24.6 V | 161 A | restart 51/51, 11.03 V |
| 3 | fixed k*T0/N | 60 ns | 222.868 ns | 0.9648 V | 0.7487 / 0.5034 / 0.2613 | 24.8 V | 158 A | restart 50/50, 11.04 V |

- **Every run ends in a periodic state.** The last 20 sections vary by
  < 1 mA and < 0.1 mV.
- **Phases 1-3 turn on by the valley path in every cycle** in all four
  runs.
- **No period was clamped.**

**The steady state still depends on the restart time, under both shift
rules.**
- `VCs3/Vin` moves from 0.2579 to 0.2613 (fixed shifts) or 0.2661
  (period-following). Phase 4's position at the section moves with it: the
  largest section difference is 12.5 (fixed) or 123 (period-following), in
  V and A.
- The period changes by ≤ 0.023 ns, and Vo by ≤ 0.45 mV.

## 2. Checks

- **Regression gate.** Run 0 replays A73 run 5 over its full length
  bit-identically: 1801 sections, difference 0.0, equal end state.
- **Diagnostic reruns.** Reruns 0d and 1d reproduce runs 0 and 1
  bit-identically: 1801 sections each, difference 0.0, equal end states.
  The added log does not change the dynamics.

## 3. What is still open

**Why phase 4's current level is offset.** Two candidates, not yet
separated:
1. **Phase N is structurally different.**
   - For phases 1..N-1, the node `x_k` is tied through the flying capacitor
     to `a_k`, which carries two high-side devices. The switching-node
     capacitance is therefore `C_low + 2*C_high` = 13.02 nF.
   - Phase N has no flying capacitor below it, so its node sees
     `C_low + C_high` = 9.30 nF.
   - Its on-state voltage is `VCs3` directly: 12.4-12.8 V against ~11.8 V
     for phases 2-3.
2. **A self-reinforcing state.** The restart (hard) turn-on changes phase
   4's volt-seconds. The ladder then shifts (`VCs3` rises), which keeps
   phase 4's current high, which keeps its turn-off current positive.

**A discriminating test.** Per-phase current sensing: every phase turns its
low side off at its own `i_k <= -2.5 A`, as phase 1 does. Published
precedent is UCC28063A's interleaving, in which both channels are masters
with their own ZCD.
- If a state with all four phases ringing then exists, the restart state
  is an alternative fixed point of the single-sensor rule.
- If it does not, the cause is structural (candidate 1).

**Runs 2-3 (60 ns restart).** Phase 4 is also restart-driven there, even
though the ring had 60 ns to reach its valley. These runs have no
diagnostic log, and this is not yet explained.

## 4. Limits

- **The circuit is A73's idealised P24 module.**
  - linear Coss;
  - 0.54 mOhm lumped per phase;
  - ideal unidirectional diodes;
  - an ideal input ramp;
  - Cout 4.672 mF (inherited, suspect);
  - one module (250 W), not P24's four.
- **The controller is idealised.** Open-loop Ton; zero latency; exact
  timing.
- **Project decisions.** The restart times, the period clamp and the
  period-following rule are `PROJECT_DECISION`s. The rule was a diagnostic
  of the cause, not a proposed controller; the interleaving papers in
  BOUNDARY Section 3 have not been read yet.

## 5. Next

1. **Per-phase current sensing (physical model)**, as in Section 3, to
   separate the two candidates.
2. **The mathematical model.** The four-phase extension with the valley
   trigger. The structural question is whether a periodic orbit with all
   phases soft-switched exists for P24's module under each sensing rule.
3. **A75 (running).** Controller latency and a predictive valley turn-on
   for phases 1-3.

## 5a. Reproduction

```
zsh run_a74.sh        # runs 0-3 (run 0 = A73 run 5 replay, the gate)
zsh run_a74_diag.sh   # reruns 0d, 1d with the diagnostic log
python3 a74_analyze.py && python3 a74_diag.py
```

The datasheet PDFs are not in this repository.
