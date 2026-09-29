# A71 - zero start of the P25 three-phase SCB, following a published sequence (BOUNDARY)

Track A, `CROSS_PAPER_EXTENSION`. Written before any run.

## 1. Question

Starting from all-zero state, does the P25-scale three-phase SCB reach
D42's 4.9 mOhm periodic section when started with a published start-up
sequence? The earlier attempts failed in two ways:
- A70 run 4 started with empty inductors into the full constant-current
  load, which pulled Vo negative;
- Track B's event-gated start-up controller (R04E21-R04E26) waited for a
  ZVS that could not come.

## 2. Sources, and what transfers

- **Stillwell and Pilawa-Podgurski, TPEL 34(3), 2019,
  DOI 10.1109/TPEL.2018.2843777, Sec. VI-C** (hardware, five-level FCML).
  Their sequence:
  1. output load disconnected;
  2. PWM switching running;
  3. input ramped slowly, so the flying capacitors follow;
  4. load enabled at full input voltage.

  What transfers: the ordering, and "switching runs during the ramp,
  load off", which is topology-independent.

  What does not transfer by citation: FCML's phase-shifted-PWM natural
  balancing. The SCB balances by charge balance through its inductors, so
  whether its series capacitors track the ramp is measured here, not
  assumed.
- **Roberts, PhD dissertation, Ch. 3.5** (SCB-specific; as used in Track B,
  `paper_locked/00_boundaries/ROBERTS_SOFTSTART_P24_MODEL_DERIVATION.md`).
  - Ramp Vin while the normal multiphase switching runs from t = 0.
  - The ramp time is `30 x 0.35/f1`, with
    `w_k,N = (2D/sqrt(L*Cfly)) * sin(k*pi/2N)`.
  - For P25 scale: N = 3, D = 0.25, L = 30 nH, Cfly = 100 uF. Then
    f1 = 22.97 kHz, `0.35/f1` = 15.2 us, and the 30x ramp is **457 us**.
- **Kim et al., TPEL 33(1), 2018, DOI 10.1109/TPEL.2017.2705705.** The
  conventional SCB's soft start is a gradual ramp with the normal gate
  pattern. Start-up voltage stress does not matter here: GaN rated
  100 V, 12 V input.
- **Chiang and Chen, TPEL 2009.** The valley fallback on the high-side
  turn-on, as in A70.

**Why the P25 control cannot run the start-up by itself** (derived, not
cited). Open loop, with Ton fixed and phase 1's low side turned off at
-2.5 A, each phase delivers a fixed average current:
`i_target + dI/2`, with `dI = (Vin/3 - Vo)*Ton/L` ≈ 50 A. That is
≈ 22.5 A, independent of the load.
- With the load disconnected, nothing takes that current, and Vo runs
  up.
- At Vo ~ 0, the current barely falls during the low-side interval, so
  the -2.5 A target is not reached (A70 Section 2).

The published sequences all start under fixed-timing PWM (voltage mode),
where no load means Vo ≈ D*Vin/3. The start-up therefore runs in fixed
timing, and control is handed to the P25 rule after the load is on.

## 3. Circuit

A70's simulator (A69 circuit and integration; 4.9 mOhm per phase; 0.1 uOhm
ON/diode), copied as `a71_transient.py`, with three changes:
- **Input.** `Vin(t) = 12 V * min(t/t_ramp, 1)`: an ideal ramped source,
  standing in for Roberts' eFuse ramp. Stillwell's R_LIMIT path is not
  modelled.
- **Load.** The constant current is 0 A before `t_load` and 67.5 A after
  (a step, as in Stillwell's load enable).
- **Initial state.** Every capacitor voltage and inductor current is zero.

## 4. Controller

- **Mode S (start-up, fixed timing), from t = 0 until the handover.**
  - Period `T0 = 2.0 us` (P25's 0.5 MHz) and Ton 500 ns.
  - Phase 1's low side turns off at `t_on1 + T0 - t_dead`. Phases 2 and 3
    turn off at `t_ref + T0/3, + 2T0/3`, exactly as in D41.
  - Both edges use a fixed dead time `t_dead = 20 ns`
    (`PROJECT_DECISION`: well above the ~5 ns ZVS commutation, small
    against Ton). Reverse conduction is taken by A69's diode branch.
- **Handover** (`PROJECT_DECISION`; no source gives one). The switch
  happens at the first phase-1 high-side turn-on at or after `t_hand`.
  - At that instant phase 1 is HIGH, and phases 2 and 3 are LOW, waiting
    on the same timers in both modes. No edge is mid-commutation, so no
    rule changes under a phase in transition.
  - The instant is recorded.
- **Mode P, after the handover.** A70's controller: the D41
  single-sensor rule with the Chiang valley fallback, `dV_hys` 0.05 V.

## 5. Runs

| run | t_ramp | t_load | t_hand | t_end |
|---|---:|---:|---:|---:|
| 1 main (Roberts 30x) | 457 us | 507 us | 607 us | 1207 us |
| 2 fast (3x) | 46 us | 96 us | 196 us | 796 us |
| 3 control: P25 rule from t = 0 (no mode S) | 457 us | 507 us | 0 | 1207 us |

At each phase-1 high-side turn-on the run records:
- the section state;
- Vin;
- `VCs1 = a1 - x1` and `VCs2 = a2 - x2`;
- the mode;
- the peak `|i|` over the cycle.

It also records each valley firing.

## 6. Acceptance / reporting

- **Ladder tracking during the ramp.** Report the maximum of
  `|VCs1/Vin - 2/3|` and `|VCs2/Vin - 1/3|` over sections with Vin > 1 V,
  and the peak phase current.
- **Final state.** Outcome (a) is the last section within 0.05 A / 5 mV of
  D42's 4.9 mOhm `z*`, as in A70. Otherwise: (b) another periodic state,
  or (c) a stall, with the stalled states reported.
- **Run 3** is expected to stall or run away. That would show why a
  fixed-timing start is needed. It is reported as it falls.

## 7. Decides / does not decide

Decides:
- whether a published start sequence, plus the valley fallback and a
  declared handover, takes the P25-scale SCB from all-zero state to the
  D42 section, in the idealised circuit.

Does not decide:
- P24 four-phase start-up, which needs Track B's precharge: 40 V devices
  against a 48 V input (Kim 2018);
- closed-loop Ton;
- real devices, gate drivers and auxiliary supplies;
- the best ramp or handover timing.

## 8. Amendment (after runs 1-3, before runs 4-6)

Runs 1-3 showed three things.
1. **The no-load fixed-timing ramp tracks.** At the end of the no-load
   interval, `VCs2/Vin` stays within 0.3335-0.3357 (run 1).
2. **Mode S with the 67.5 A load does not settle.** The ladder and the
   currents oscillate with an undiminished amplitude: `VCs2/Vin`
   peak-to-peak 0.19 in every 25 us window over 100 us, in both runs 1 and 2.
3. **The handover outcome depends on the oscillation's phase.**
   - Run 2 converged.
   - Run 1 handed over at a state with i2 = 51 A and i1 ≈ 0. Vo spiked
     to 2.0 V, then fell below zero, and phase 1's current-target wait
     stalled.

Added runs, declared here before running:
4. **Mode S with load, extended.** Fast ramp (46 us), load at 96 us,
   no handover, t_end 496 us. The question is whether the mode-S
   oscillation under load persists (a limit cycle) or slowly decays.
5. **Handover together with the load, from the settled no-load state.**
   Main ramp: t_ramp 457 us, `t_load = t_hand` = 507 us, t_end 1107 us.
   The load switches on at 507 us exactly. The handover takes effect at
   the first phase-1 high-side turn-on at or after 507 us, less than
   2 us later.
   - Rationale (derived, `PROJECT_DECISION`): open loop, mode P delivers
     ≈ 22.5 A per phase, i.e. the 67.5 A load. Mode P and the load are
     therefore matched from the start, and the unsettled "mode S under
     load" interval is skipped.
   - Stillwell and Pilawa-Podgurski connect the load at full input
     voltage. That ordering is kept; only the controller change is moved
     to the same moment.
6. **As run 5, with the fast ramp:** t_ramp 46 us, `t_load = t_hand` = 96 us,
   t_end 696 us.

Acceptance is as in Section 6.
