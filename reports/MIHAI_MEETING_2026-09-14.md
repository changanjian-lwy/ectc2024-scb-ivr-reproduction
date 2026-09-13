# ECTC 2024 SCB-IVR Reproduction - Progress Brief

## 1. Objective and present scope

The immediate objective is to reproduce and understand the operating mechanism
of the 2024 ECTC 48-to-1 V SCB integrated voltage regulator before expanding
the work into a broader design framework.

The current work deliberately separates three questions:

1. Does the paper-derived switching sequence produce a self-consistent
   periodic operating trajectory?
2. Can the flying-capacitor ladder reject a small perturbation around that
   trajectory?
3. Can a real controller establish and regulate that trajectory from zero
   initial energy?

The present validated work addresses Questions 1 and 2 under an explicit
1 V output-isolation boundary. It does not yet claim zero-start or closed-loop
output regulation.

## 2. Evidence rule used throughout

The implementation follows a source hierarchy rather than inventing a complete
controller:

- **Primary source:** the 2024 ECTC paper defines the target topology,
  four-phase/four-module architecture, analytical relationships and its own
  three-interval physical sequence.
- **Supplementary source:** the 2025 APEC paper is used only where the 2024
  paper is silent, for example explicit grounded low-side sources, detailed
  commutation mechanisms, prototype component information and control concepts.
- **Conflict rule:** when the papers differ, both interpretations are retained
  as separate branches. The 2025 sequence is not pasted over the 2024 sequence.
- **Unknown rule:** an unreported quantity remains an explicit model input or
  blocker. It is never adjusted merely to obtain a desirable waveform.

This rule produced a physical-event mapping layer. Paper-local labels such as
`t2` and `t3` are treated as aliases, because the same labels refer to different
physical events in the two papers.

## 3. Important 2024/2025 differences found

| Topic | 2024 ECTC | 2025 APEC | Implementation decision |
|---|---|---|---|
| Target | 48 V to 1 V, 1 kW; 4 phases x 4 modules | 12 V to 1 V, 200 W prototype; 3 phases x 3 modules | Keep 2024 as the reproduction target |
| Sequence detail | Three intervals centered on a displayed phase | Six prototype modes with more commutation detail | Store separately and map by physical event |
| Negative current | 1-2% of peak | Mode text 5-10%; design discussion up to 5% | P24 2% and P25 5-10% remain separate branches |
| Low-side source connection | Graphically ambiguous in the 2024 figure | Explicitly connected to common ground | Grounded connection is a P25-sourced supplement, visibly labelled |
| Device/prototype data | Target architecture and design tables | GS61008T, driver and prototype parts | Device data are modular; cross-voltage transfer is labelled |

## 4. Analytical audit before SPICE

For the 2024 four-phase, four-module, 5 MHz case, the paper relationships give:

- duty ratio: 8.333%;
- high-side on-time: 16.667 ns;
- phase peak current: 125 A;
- critical inductance from the printed equation: 1.4667 nH.

The 2024 Table I value at 5 MHz is 2.68 nH. This does not agree with the
printed equation; the difference is approximately a factor of 1.83. The 2025
`0.95 Lcrit` design factor does not explain the mismatch. The active mainline
therefore uses the calculated 1.4667 nH, while the table value remains a
documented unresolved source conflict.

## 5. Experiment logic and results

### 5.1 Early zero-start exploration - retained as negative evidence

Direct zero-state fixed-PWM simulations did not establish the intended
36/24/12 V ladder or 1 V output. Precharge, fixed takeover and instantaneous
zero-current comparators exposed startup-current accumulation, chatter and
unreported controller requirements. These runs are quarantined as diagnostic
evidence; they are not used to claim failure of the 2024 power stage.

### 5.2 Return to the paper's periodic operating assumption

The mainline was restarted from the 2024 boundary-mode assumption. A
phase-shifted triangular-current seed replaced the physically inappropriate
all-zero-current seed for a periodic four-phase snapshot. Fixed-point shooting
then reduced the maximum current residual:

| Stage | Maximum absolute current residual |
|---|---:|
| All-zero current seed | 80.468 A |
| Analytical phase-shifted triangular seed | 30.499 A |
| Shooting iteration 1 | 1.300 A |
| Shooting iteration 2 | 0.461 A |
| Shooting iteration 3 | 0.226 A |

This is a numerical periodic-state solver, not a startup method. Its initial
inductor energy is imposed for steady-state analysis and must not be presented
as naturally generated startup energy.

### 5.3 Commutation and branch checks

- The local phase-1 commutation chain was checked with device commutation
  capacitance included and no external snubber.
- In the shared two-phase local state, 8% negative current did not satisfy the
  selected high-side ZVS acceptance test; 9% and 10% did.
- In the full four-phase first-period model, the current reached only about
  2.7% negative, so the configured 8% event was never exercised. This is
  recorded as an unexercised condition, not a failed 8% hardware conclusion.
- The four-phase readiness detector was implemented using adjacent voltage
  differences rather than hard-coded absolute 24 V/12 V thresholds.

### 5.4 Isolated passive-balance test

To separate flying-capacitor charge redistribution from unresolved output
regulation, the output was explicitly clamped to 1 V and C1 was perturbed by
`-0.5/0/+0.5 V` with all other conditions identical.

After 20 periods:

- negative perturbation: `-0.5000 -> -0.4519 V` relative to control;
- positive perturbation: `+0.5000 -> +0.4827 V` relative to control.

Both signs moved toward the simultaneous control trajectory, supporting a
weak bidirectional passive restoring tendency. The response was asymmetric,
and the control orbit was not yet exactly periodic, so this is not proof of
asymptotic convergence.

### 5.5 One-state-group-at-a-time periodic tightening

The output-clamped model has seven free periodic states: four coupled inductor
currents and three flying-capacitor voltages. Each update received a separate
experiment folder and only one state group changed at a time.

| Experiment | Only newly updated state/group | Max capacitor residual | Max current residual |
|---|---|---:|---:|
| A11 control | parent seed | 2.934 mV | 1.340 A |
| A13 | four coupled inductor currents | 0.597 mV | 0.11114 A |
| A14 | C1 | 0.597 mV | 0.11113 A |
| A15 | C2 | 0.596 mV | 0.11110 A |
| A16 | C3 | 0.595 mV | 0.10491 A |

The current-group update produced the main improvement without worsening the
capacitor closure. It remains a steady-state numerical tool, not a physical
control action or design optimization.

## 6. Current model boundaries

- Single 250 W module of the 2024 1 kW architecture; four-module operation is
  not yet claimed.
- Four phases, 5 MHz, 48 V input, calculated 1.4667 nH inductors.
- P24-derived 2% branch is the active mainline; P25 thresholds remain separate.
- Constant scalar device commutation capacitance is included; nonlinear
  `Coss(Vds)`, detailed gate charge and package extraction are not yet included.
- External snubber capacitance is zero because neither paper provides its value.
- The passive-balance and tightening tests use an ideal 1 V output clamp as an
  isolation fixture.
- The 36/24/12 V capacitor values are periodic-state coordinates in these
  experiments, not zero-start results.
- No efficiency, thermal, EMI, reliability or hardware-loss claim is made.

## 7. Problems exposed by the reproduction

1. The 2024 printed critical-inductance equation and Table I are inconsistent.
2. The two papers attach different events to similarly named time boundaries;
   merging by `t1/t2/t3` would create a wrong sequence.
3. Their negative-current targets differ and cannot be silently averaged.
4. A complete startup/precharge/takeover law is absent.
5. Numeric dead time, sensing delay, nonlinear device capacitance and external
   snubber values are not fully reported.
6. The four-phase/four-module scheduling rule needs a collision audit; naive
   phase and module offsets can create coincident events.
7. Passive flying-capacitor restoration is observed locally, but output power
   balance and closed-loop regulation remain deliberately unresolved.

## 8. Focused questions for discussion

1. Should the 2024 printed inductance equation or Table I be treated as the
   intended 5 MHz design basis? Is there an omitted derating or current
   definition behind 2.68 nH?
2. Is the immediate goal the paper's ideal periodic mechanism, or should the
   next milestone include a specific startup and output-control strategy?
3. Are target device models, gate-driver delay/dead time, snubber capacitance,
   and flying/output capacitor bank data available for the 48 V design?
4. For the full 4 x 4 case, what module-origin scheduling convention should be
   used when simple `T/nP` and `T/nM` offsets coincide?
5. Should the P24 1-2% and P25 5-10% negative-current laws remain two formal
   cases, or is one intended for the target 48 V implementation?

## 9. Proposed next work after confirmation

1. Complete a tighter output-clamped periodic orbit using the documented
   one-state-group-at-a-time solver.
2. Re-run the symmetric passive-balance perturbation around that orbit.
3. Remove the ideal output clamp in a separate experiment and solve the power
   balance/output-control problem without changing the paper-derived topology.
4. Only then return to zero-start and determine whether a detachable
   precharge/takeover controller can reach the validated periodic orbit.
