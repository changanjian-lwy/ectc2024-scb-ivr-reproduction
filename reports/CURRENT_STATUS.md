# Current Work Status

Updated: **2026-10-09** (item 93: A179 and the paper map; items 62-67: the ML block A146-A150 and the
package drive specification A151-A152; items 68-87: D68-D78, A153-A162 and the hot efficiency; items 88-90: D79 and
A163-A166, the gate drive). This is the current navigation
summary; dated reports remain historical snapshots.

The project runs two models in parallel on purpose, each checking the other:
the **mathematical model** (native P25 event model, Section 1) and the
**physical model** (Track A circuit simulations, Section 2). Since
2026-09-29 both are maintained by one session. The mathematical-model
session's work was committed unchanged as the baseline (`0f50511`).

**Since 2026-09-30 the mathematical model is P24-native** (D43-D67 in
`symbolic_derivations/03_P24_native/`; the cycle-by-cycle valley map D63
is its core), because the physical model is P24's four-phase module and
the two models must describe the same circuit to check each other. Each
BOUNDARY names its cheaper check: D63 for controller transients (latest
A143, A148-A150), D65 and the single-edge harnesses for the package
(A144-A151), D66 for current sharing (C14). Not yet in any mathematical
model: RTL arbitration (A141, A142, C13), the start-up handover (A152's
start-up Ton is calibrated on short co-simulations) and the slow turn-on
above 100 pH (the harness underpredicts it, A151).
Section 1's P25-native three-phase form is the record of D39-D42 (+ A69)
and is not continued; its open items were answered in the P24-native form
(see "Verification and next step").

## 1. Mathematical model — native P25, three phases / one module

**Status (2026-10-06): closed in this form, kept as the record.** The
mathematical model continues P24-native (header above; items 2-67, from D43).

**Latest (2026-09-29, D39–D42, cross-checked by A69):**

**Acceptance clarification ([fresh audit](AUDIT_D41_D42_RETURN_ACCEPTANCE_2026-09-29.md)):**
D42's saved 4 mΩ point passes the original full return criterion on replay;
the 4.9 mΩ point completes all 15 modes but remains above the current-return
tolerance. D41's saved lossless point also remains formally unreturned.
Read "closed orbit" claims below as near-closure unless the formal status
passes; linearized stability estimates do not replace that return check.

- **Why D23–D38 kept failing.** The synthetic F/H/s fixture's switch-node
  flip time `sqrt(L*C)` is 122–150× its on-time. P25's built point has
  ~1.5%. In the fixture, ZVS commutation runs on the same time scale as the
  other phases' currents, so "phase 3 reaches zero before SH2 ZVS" is a
  scale effect.
  - Physical-model A67 derives the criterion.
  - A68 runs this machinery read-only at P25 scale. There, M5 SH2 ZVS
    passes on the first try.
- **[D39](../symbolic_derivations/02_P25_native/D39_ZVS_RISE_WINDOW_ENVELOPE.md):**
  write-up of the affine-envelope bound on the D38 window.
- **[D40](../symbolic_derivations/02_P25_native/D40_TOLERANCE_CONSISTENT_ENTRY.md):**
  a reverse gap within the voltage tolerance that moves strictly outward is
  released under its own status, with the value kept. This resolves the
  conflict between tolerance-accepted roots (a −6 nV SH2 ZVS residual kept
  by the ON switch) and D11's exact-zero entry. At P25 scale, M1–M15 now
  completes without any override.
- **[D41](../symbolic_derivations/02_P25_native/D41_SINGLE_SENSOR_PHASE_SHIFT_CONTROL.md):**
  P25 Sec. III single-sensor control is an optional policy.
  - Phase 1 is current-sensed. Phases 2 and 3 turn their low sides off at
    fixed phase shifts after phase 1's high-on.
  - At P25 scale, Newton converges to a returned section: ZVS on all three
    high sides, period ~1.946 µs.
  - The per-phase control of D06 leaves the phase spacing nearly neutral
    (`J−I` singular values ~3e-4) and does not converge.
  - The returned orbit is weakly unstable in the lossless open-loop model.
- **[D42](../symbolic_derivations/02_P25_native/D42_DAMPING_CONTINUATION.md):**
  per-phase series resistance, continued 0 → 4.9 mΩ from the D41 orbit.
  - The unstable pair falls monotonically: 1.060 → 1.026 (1 mΩ) → 0.991
    (2 mΩ). It crosses the unit circle at ~1.75 mΩ.
  - At P25's estimated 4.9 mΩ (duty-weighted GS61008T Ron + Coilcraft DCR),
    the largest |λ| is 0.926.
  - The weak instability is an artefact of the lossless idealisation, not
    of the control structure.
  - Open loop, Vo sags to 0.844 V: Ton and the load are held.
- **Physical-model cross-check
  ([A69](../experiments/track_A_periodic_steady_state/A69_three_phase_p25_transient_crosscheck/RESULTS.md)).**
  An independent fixed-step circuit simulation, sharing only the start state,
  reproduces:
  - the period to 3.5 ps;
  - the lossless drift growth, 1.059 vs 1.060;
  - the 0.5 mΩ growth, 1.039 vs 1.043;
  - the 4.9 mΩ decay of a 0.2 A kick, 0.929 vs 0.926.

  Started far from the damped orbit, the fixed-shift control deadlocks: the
  timed low sides turn off without enough negative current, and nothing
  forces a turn-on. Hardware needs a timeout fallback.

The historical record follows.


**Purpose:** define a coupled switching model before claiming a periodic
solution. No P24 fourth phase or module coupling is implicit.

**Important D33 correction:** the old synthetic +20 A phase-1 entry is a
valid diagnostic initial state, but not a candidate for this event cycle's
periodic return: M15→M1 retains negative phase-1 current. D29's neighborhood
also lies outside that return domain. Its local failure results remain valid;
they do not constitute a meaningful periodic-solution search.
See [D33](../symbolic_derivations/02_P25_native/D33_PERIODIC_SECTION_DIRECTION_AUDIT.md).

[D34](../symbolic_derivations/02_P25_native/D34_NEGATIVE_RETURN_SEED_DIAGNOSTIC.md)
tests four new negative-i1 seeds with devices/control frozen. Two fail the M1
turn-off current-domain check; two reach M2 but encounter phase-2 current zero
before low-side commutation within an extended search window. No periodic
candidate succeeds. Short-horizon exhaustion is recorded separately.

[D35](../symbolic_derivations/02_P25_native/D35_DOWN_COMMUTATION_CHARGE_ACCOUNTING.md)
accounts for the same two M2 continuations: roughly 2.67 C is delivered
against 5.50 C required before i2 reaches zero; SL1 Vds remains about 1.03 V.
These are synthetic values and an unaccepted diagnostic interval, not a
completed M2, device Qoss measurement, or global infeasibility proof.

[D36](../symbolic_derivations/02_P25_native/D36_TWO_VOLTAGE_SEED_GRID.md)
varies only two initial voltages with devices/control frozen. Two of six
negative-i1 seeds pass M2; the furthest accepts M1–M4 and stops in M5 at i1=0.
All still lack a complete return trajectory. Synchronous node/current/gate
states are saved, separating accepted states from unaccepted diagnostic roots.

[D37](../symbolic_derivations/02_P25_native/D37_SAME_PATH_NEGATIVE_TARGET_AND_COMMUTATION.md)
accounts for those same trajectories: the furthest M5 delivers only about
7.6% of its target charge before i1 reaches zero. Its Vo is already decreasing,
so D31's monotone-output bound is explicitly inapplicable. No control value changed.

[D38](../symbolic_derivations/02_P25_native/D38_A2_OFFSET_ZVS_VS_RISE.md)
derives one new initial a2 from a pre-SH2 affine offset, then reruns from M1.
M1–M5 reach SH2 ZVS, but M6 starts with negative inductor voltage/current
slope and its scheduled turn-off is rejected. ZVS admission does not establish
the paper's intended rising-current mode or a complete periodic solution.

[D39](../symbolic_derivations/02_P25_native/D39_ZVS_RISE_WINDOW_ENVELOPE.md)
evaluates an analytical whole-window comparison envelope. With the other
D38 seed coordinates frozen, X2 remains below Vo throughout that window;
further a2-only tuning there cannot deliver positive M6 entry slope.
Floating-point evaluation is not certified interval arithmetic or global infeasibility.

| Stage | Completed work | Evidence |
|---|---|---|
| Definitions | Physical events, shared nodes, sign domains, reverse constraints and control memory | [D02–D09 index](../symbolic_derivations/README.md) |
| Continuous dynamics | Constant-linear-component affine flow retaining switch capacitors and dynamic output capacitor | [D10](../symbolic_derivations/02_P25_native/D10_LOCAL_AFFINE_FLOW.md) |
| Admissible entry | Direction check at a zero reverse gap; no epsilon time skip or state projection | [D11](../symbolic_derivations/02_P25_native/D11_SINGLE_MODULE_ENTRY_DIRECTION.md) |
| First connected handoff | One synthetic M1→M4-entry trajectory passes; its M5 continuation stops when phase 3 reaches zero before SH2 ZVS | [D12](../symbolic_derivations/02_P25_native/D12_CONNECTED_FIRST_HANDOFF.md), [D13](../symbolic_derivations/02_P25_native/D13_NEGATIVE_TARGET_AND_HIGH_HANDOFF.md) |
| Failure explanation | Integrated volt-second budget and output charge track the same trajectory | [D14](../symbolic_derivations/02_P25_native/D14_FREEWHEEL_MARGIN_AND_SEED_SCOPE.md) |
| Three-phase assembly | All 15 main modes supported by node equations; M7–M15 explicitly identified as cyclic extensions | [D15](../symbolic_derivations/02_P25_native/D15_THREE_PHASE_MODE_ASSEMBLY.md) |

**Boundary:** constant linear capacitances/inductances, declared winding
resistance, ideal gate transitions, declared reverse-branch surrogate,
constant external ports during each local flow. Synthetic test states are
algebraic fixtures, not paper device values. No nonlinear GaN or physical
gate-driver validation is implied.

**Current result:** all three handoffs and a 15-mode single-period attempt are
implemented (D16–D21). A complete admissible trajectory and periodic return
are **not yet demonstrated**. The frozen synthetic seed neighborhood (D29)
stops at M5 when phase 3 reaches zero before SH2 reaches ZVS.

Local continuation after the GitHub presentation update:
[D16](../symbolic_derivations/02_P25_native/D16_THREE_PHASE_COMMUTATION_GUARDS.md)
extends guard screening and entry-direction checks to all six commutation
intervals. [D17](../symbolic_derivations/02_P25_native/D17_THREE_PHASE_HANDOFF_EXECUTION.md)
then extends handoff execution to all three phases, with explicit M15→M1
cycle counting and state continuity. D17 checks: 427 portable,
446 full-suite. At that stage high-on orchestration was still open.

[D18](../symbolic_derivations/02_P25_native/D18_HIGH_ON_COMPETING_EVENTS.md)
adds high-on interval screening against competing current/reverse events,
without treating turn-off current as an observed peak. At D18, full-cycle assembly
was the next step; D19 subsequently implemented it. D18 verification: 433 portable and 452 full-suite
checks passed; these remain software/model-contract tests, not paper operating points.

[D19](../symbolic_derivations/02_P25_native/D19_SINGLE_PERIOD_ATTEMPT.md)
now composes a full single-period attempt with a per-step trace. The unchanged
old synthetic seed still stops in M5 at phase-3 current zero. No successful
full-cycle trajectory or periodic-state closure is claimed. D19 verification:
457 full local checks and 438 portable checks passed.

[D20](../symbolic_derivations/02_P25_native/D20_FIXED_BOUNDARY_SHOOTING_CONTRACT.md)
defines six independent electrical seed coordinates with all physical/control
boundaries frozen. This branch requires fixed declared design peaks; it does
not silently substitute them for measured-peak feedback or solve a periodic orbit.
Latest local verification: 462 full-suite and 443 portable checks passed.

[D21](../symbolic_derivations/02_P25_native/D21_SEED_FEASIBILITY_VS_RETURN.md)
connects candidate evaluation to the cycle attempt and D08 return check.
Blocked attempts produce no fabricated residual. A synthetic ±10% i3-entry
diagnostic remains blocked in M5 at all three points, not a paper operating-point test.
Latest D21 verification: 465 full-suite and 446 portable checks passed.

[D22](../symbolic_derivations/02_P25_native/D22_ALL_LOW_CURRENT_ORDER_BOUND.md)
adds an analytical necessary current-order bound for exact zero-R/zero-node
all-low phase pairs. The old trajectory has 3 V·s third-phase margin at the
negative target; its later M5 failure remains. Nonzero node residuals are
explicitly excluded rather than erased.
Latest D22 verification: 470 full-suite and 451 portable checks passed.

[D23](../symbolic_derivations/02_P25_native/D23_COMMUTATION_CHARGE_DEFICIT.md)
quantifies the same synthetic M5 failure using full-network affine charge
normalization: only about 5.2% of required commutation charge is supplied before
phase 3 reaches zero. This is not an actual-device Qoss or alpha estimate.
Latest D23 verification: 473 full-suite and 454 portable checks passed.

[D24](../symbolic_derivations/02_P25_native/D24_PHASE_SPECIFIC_COMMUTATION_FORMULAS.md)
independently derives all three upward-commutation transfer coefficients.
Identical switch capacitors do not imply identical phase coefficients: the
physical capacitor-network positions differ. No periodic solution is claimed.
Latest D24 verification: 477 full-suite and 458 portable checks passed.

[D25](../symbolic_derivations/02_P25_native/D25_FORCED_COMMUTATION_ODE.md)
derives and checks the forced target-Vds second-order equation with dynamic
output voltage and winding resistance. The local capacitance normalization
cannot be substituted blindly into an isolated-LC resonance formula.
Latest D25 verification: 480 full-suite and 461 portable checks passed.

[D26](../symbolic_derivations/02_P25_native/D26_FIVE_STATE_COMMUTATION_MODEL.md)
independently assembles a five-state coupled local commutation model.
It matches the full network and preserves the old failure, but does not yet
reconstruct every OFF-switch voltage and cannot replace the full event scanner.
Latest D26 verification: 484 full-suite and 465 portable checks passed.

[D27](../symbolic_derivations/02_P25_native/D27_FULL_NODE_RECONSTRUCTION.md)
now reconstructs all nodes and six switch voltages from the reduced flow.
Cross-checks preserve the old failure root and entry residuals; the main
event scanner still uses the original full-node model.
Latest D27 verification: 487 full-suite and 468 portable checks passed.

[D28](../symbolic_derivations/02_P25_native/D28_ACCEPTED_TRACE_INTEGRAL_LEDGER.md)
adds the accepted-trace integral ledger. The unchanged M1–M4 prefix balances
69.248873 C of synthetic output charge; failed M5 is excluded. A positive
prefix charge is not a proof that no complete periodic orbit exists.
Latest D28 verification: 491 full-suite and 472 portable checks passed.

[D29](../symbolic_derivations/02_P25_native/D29_FROZEN_SEED_NEIGHBORHOOD.md)
checks six initial coordinates individually at ±10%, keeping all components
and control settings frozen. All 13 synthetic cases fail at M5/i3 at both
200- and 400-point resolution. This is local diagnostic evidence, not a
global no-solution statement or paper-parameter search.
Latest D29 verification: 493 full-suite and 474 portable checks passed.

[D30](../symbolic_derivations/02_P25_native/D30_CHARGE_FLUX_NECESSARY_BOUND.md)
derives a conservative charge/flux obstruction under exact zero-R/zero-ON-node
premises. It is not a ZVS success test. The old continuous seed is explicitly
ineligible because its nonzero ON-node residual is retained, not projected away.

[D31](../symbolic_derivations/02_P25_native/D31_RESIDUAL_PRESERVING_CHARGE_BOUND.md)
extends that bound to the residual-bearing affine continuation without
altering the entry state. Its synthetic required charge is 20.3152 C versus
a conservative available upper bound of 1.4960 C. This explains the local
obstruction, not ideal-switch algebraic admissibility, preceding numerical
error, complete-cycle infeasibility, or paper hardware performance.

[D32](../symbolic_derivations/02_P25_native/D32_ACCEPTED_TRACE_ENERGY_LEDGER.md)
checks accepted M1–M4 energy accounting. Retaining 1.72e-7 J of ON-node
residual work closes the synthetic ledger to approximately 2.1e-14 J.
Residual work is not MOS loss, and energy balance is not periodicity.

## 2. Physical model — Track A four-phase circuit simulations

These cases investigate periodic states and device/timing trade-offs. Their
boundaries differ from the strict native P25 core and from one another.

| Reading group | Question | Starting point |
|---|---|---|
| A49–A52 | Can a coupled periodic state be solved and cross-checked? | [A52](../experiments/track_A_periodic_steady_state/A52_spice_crosscheck_reduced_load_zvs/RESULTS.md) |
| A53–A56 | How do inductance, actual switch currents and equal delivered power change the comparison? | [A56](../experiments/track_A_periodic_steady_state/A56_equal_power_regulated_loss_comparison/RESULTS.md) |
| A57–A59 | What changes with reverse conduction, separate dead times and nonlinear capacitance? | [A59](../experiments/track_A_periodic_steady_state/A59_nonlinear_coss_epc2067/RESULTS.md) |
| A60–A63 | How conditional is the result on temperature, winding loss, load and flying capacitance? | [A60](../experiments/track_A_periodic_steady_state/A60_temperature_ron_sensitivity/RESULTS.md), [A61](../experiments/track_A_periodic_steady_state/A61_inductor_loss_break_even/RESULTS.md), [A62](../experiments/track_A_periodic_steady_state/A62_load_sweep_fixed_deadtime/RESULTS.md), [A63](../experiments/track_A_periodic_steady_state/A63_flying_capacitor_sensitivity/RESULTS.md) |
| A64–A66 | Does the conclusion survive EPC's vendor model, a real gate driver and P24's own inductor? | [consolidated](../experiments/track_A_periodic_steady_state/CONSOLIDATED_FINDINGS_A53_A64_2026-09-28.md), [A64](../experiments/track_A_periodic_steady_state/A64_vendor_model_spice_crosscheck/RESULTS.md), [A65](../experiments/track_A_periodic_steady_state/A65_lmg1210_gate_driver_spice/RESULTS.md), [A66](../experiments/track_A_periodic_steady_state/A66_p24_embedded_inductor_sizing/RESULTS.md) |
| A67–A69 | How much negative current does SCB ZVS need? Does that explain the mathematical model's failures? Does a circuit simulation confirm its P25 orbit? | [A67](../experiments/track_A_periodic_steady_state/A67_zvs_negative_current_scaling/RESULTS.md), [A68](../experiments/track_A_periodic_steady_state/A68_mainline_machinery_at_p25_scale/RESULTS.md), [A69](../experiments/track_A_periodic_steady_state/A69_three_phase_p25_transient_crosscheck/RESULTS.md) |

These are **conditional engineering studies**, not proof that the paper's
small negative-current rule, rated power and timing hold simultaneously.
Newer corrections supersede the corresponding older loss comparisons, not
the original archived files. Consult each case before reusing a number.

## 3. Zero-start — separate from periodic-state analysis

**Status (2026-10-06): carried by the co-simulation.** Start-up is the RTL
sequence of A103 (mode S open loop, handover to mode P), with the
feed-forward seed of A137 / C10 and A152's start-up Ton for a slow
turn-on; every co-simulated row includes it. Track B's LTspice
zero-start records stay as they are; R04E16's ~55 % ladder question
(below) is not pursued.

[Track B](../experiments/track_B_zero_start_extension/README.md) and the
[startup model audit](../results/ZERO_START_BOUNDARY_AND_MATH_MODEL_AUDIT.md)
record startup assumptions and mathematical construction. Fixed-PWM
startup/convergence studies do not demonstrate a paper-consistent handoff to
event-controlled ZVS. A prescribed periodic-state voltage ladder must never
be reported as self-established startup balance.

## Verification and next step

**Current (2026-10-06):** the portable suite (631 tests, all pass, 1 skipped) runs on every push (CI);
the acceptance gate holds 50 co-simulated experiments, every registered
miss documented in its RESULTS. The 2026-09-29 text below is kept as the
record. Its open items were answered in the P24-native models:
1. a phase shift that follows the measured period -> D51 / D52 and
   A92-A97 (period-following slots, then `slot_lo`, C02);
2. closed-loop Ton -> D59 (voltage loop, A104) and D63 (closed-loop valley
   map, checked against every co-simulated transient);
3. the valley trigger in the control memory -> D47 (predicted turn-on)
   and the floor (A118);
4. device realism -> EPC2067's datasheet Coss(V) and reverse conduction in
   the co-simulation plant (A59, A88). P25's GS61008T was not run.

On 2026-09-29, the current shared workspace passed **520 portable checks**
and **539 full local checks** on a fresh rerun. Counts include both sessions' work.
The extra local checks use generated LTspice logs; all are software/model
regressions, not independent physical experiments.

Full-cycle reachability is established at P25 scale (D40). A returned
periodic section exists under D41 single-sensor control. With P25-scale
damping it is stable (D42), and an independent circuit simulation confirms
the orbit and its stability (A69). Next, with the model that should carry
each question:

1. **Adaptive phase shift (mathematical model).** P25's circuit is
   unpublished. A phase shift that follows the measured period is the other
   plausible reading, and it should be compared with D41's fixed shift for
   existence and stability.
2. **Closed-loop Ton (mathematical model).** Open loop, Vo sags to 0.844 V
   at 4.9 mΩ. P25 regulates to 1 V. The question is whether a slow Ton loop
   keeps the orbit stable.
3. **Start-up (both models).**
   - **Done ([A70](../experiments/track_A_periodic_steady_state/A70_valley_fallback_turn_on/RESULTS.md)).**
     A69's deadlock is removed by a published valley-switching fallback
     (Chiang and Chen, TPEL 2009). The A69 deadlock start settles on
     D42's 4.9 mΩ section (within 0.6 mA). Runs near the orbit are
     unchanged.
   - **Next, mathematical model.** Add the valley trigger to the control
     memory and re-check the D41/D42 orbit and its stability.
   - **Done ([A71](../experiments/track_A_periodic_steady_state/A71_p25_soft_start_sequence/RESULTS.md)).**
     A zero start of the P25-scale SCB reaches D42's 4.9 mΩ section. The
     sequence has three parts:
     - fixed timing with the input ramped at Roberts' 30x rate and no
       load (Stillwell and Pilawa-Podgurski 2019);
     - the load and the P25 control switched on together;
     - the valley fallback for the high-side turn-on.

     *Withdrawn (2026-09-30, A73):* the claim that fixed timing under load
     falls into a sustained oscillation was a simulator artefact. A later
     handover works too.
   - **Corrected ([A73](../experiments/track_A_periodic_steady_state/A73_p24_literature_startup_methods/RESULTS.md), 2026-09-30).**
     A72's failure on P24 was a simulator defect: the diode branch conducted
     both ways within a step. With it fixed:
     - the A71 sequence works on P24, reaching a periodic state with
       Vds ≤ 24.8 V (within the 40 V rating);
     - the published methods reach the same state: Wei 2021 ratio precharge
       and Xia and Stauth 2022 closed-loop balancing;
     - A71's "hand over with the load" rule is withdrawn (fixed timing
       under load does settle);
     - A69's deadlock and A70's recovery are re-verified.
   - **Refuted ([A74](../experiments/track_A_periodic_steady_state/A74_p24_adaptive_phase_shift/RESULTS.md), 2026-09-30): adaptive phase shift.**
     In the P24 steady state, phase 4 is turned on by the restart timer
     every cycle. Shifts that follow the measured period do not change
     that. At its timed turn-off, phase 4 carries +7.08 A (phases 2-3:
     -3.35 A). The problem is its current level, not its timing.
   - **Done ([A75](../experiments/track_A_periodic_steady_state/A75_controller_latency_valley_timing/RESULTS.md), 2026-09-30): controller latency.**
     - At P24, reactive valley detection loses the valley at a 10 ns
       comparator-to-gate latency (LMG1210 typical).
     - A predictive, self-corrected turn-on keeps it up to 10 ns. This
       follows Chiang 2009 and Schaef et al. ISSCC 2019, which is P25's
       own zero-cross-detection reference.
     - In those predictive runs phase 4 also rings.
     - P25 tolerates 45 ns (edges at 0.8-1.7 V).
   - **Done ([A76](../experiments/track_A_periodic_steady_state/A76_p24_single_module_control_rules/RESULTS.md), 2026-09-30): control rules.**
     - **Adopted:** comparator self-trim (Schaef). It absorbs 10-18 ns of
       latency.
     - **Dropped:** reactive ZVS.
     - **Rejected:** per-phase current conditions (cycle skipping, ladder
       drift, Vds up to 44 V).
     - **Phase 4 depends on the negative-current target.** At P24's -2.5 A
       (2%) it stays restart-driven. At -8.8 A (7%, inside P25's 5-10%)
       every phase is soft.
   - **Done ([A77](../experiments/track_A_periodic_steady_state/A77_verilog_controller_cosim/RESULTS.md), 2026-09-30): Verilog controller.**
     - **Implementation:** synthesizable, 250 MHz with 125 ps delay-line
       edges, 2-FF synchronised comparators.
     - **Co-simulated with the A76 plant.** It reproduces A76's steady
       state within quantisation.
     - **Synchroniser effect:** a 4 ns edge jitter on phase 1's
       comparator-decided turn-off.
     - **Counter-only 125 MHz is inadequate at P24.**
   - **Done ([A78](../experiments/track_A_periodic_steady_state/A78_p24_negative_current_target/RESULTS.md), 2026-09-30): negative-current target.**
     - **P24's 1-2% is not enough.** Phase 4 is restart-driven up to 4%.
     - **5% (P25's lower bound, -6.25 A) is the smallest target that
       meets the single-module criterion.**
     - Conduction loss barely changes; the turn-on proxy falls.
   - **Done ([A79](../experiments/track_A_periodic_steady_state/A79_p24_output_voltage_loop/RESULTS.md), 2026-09-30): output-voltage loop.**
     - An integral Ton loop regulates the module to 1.0000 V.
     - At 5%, phase 4 is bistable: the soft and restart states coexist.
     - At 7.5% (-9.375 A), both gains settle soft, for +2% conduction loss.
   - **Done ([A80](../experiments/track_A_periodic_steady_state/A80_verilog_full_module_controller/RESULTS.md), 2026-09-30): the full Verilog module controller.**
     - Co-simulated from zero at 7.5%, it regulates to 1.0002 V with every
       phase soft, matching Python within quantisation.
     - It reproduces the 5% bistability.
     - Its dither is 2.3-4.0 A, from clock quantisation.
   - **Next (single-module level first).**
     1. Done ([A81](../experiments/track_A_periodic_steady_state/A81_verilog_async_fast_path/RESULTS.md)):
        an asynchronous fast path for phase 1 removes its 4 ns edge
        jitter, and the dither halves (4.0 to 1.9 A). The remainder is
        probably Ton LSB toggling (not yet shown).
     2. Done ([D43](../symbolic_derivations/03_P24_native/D43_P24_FOUR_PHASE_EXACT_EVENT_MAP.md), mathematical model):
        a P24-native four-phase exact event map. It is independent of the
        simulator: ideal switches, charge-conserving hard turn-ons, matrix-
        exponential flow, roots on the exact trajectory.
        - It reproduces A79's three steady states. The turn-on voltages
          agree to ~0.01-0.1 V, and all orbits are stable (|mu| max 0.986).
        - At 5% the soft and phase-4-restart states are two stable
          orbits.
        - **Mechanism.** At 3-5% the restart orbit's phase-4 valley comes
          before the 20 ns restart. The restart state persists only because
          the corrector learns at predictive edges only, and locks once
          dt_pred passes 20 ns. Escaping along the valley always returns
          to the soft orbit.
        - **Threshold.** At <= 2% (P24), phase 4 has no self-consistent soft
          orbit. The threshold is 2-2.5%, not A78's 4-5%.
     3. Done ([A82](../experiments/track_A_periodic_steady_state/A82_p24_corrector_learns_at_restart/RESULTS.md)):
        D43's prediction holds in the physical model. With the corrector
        also learning at restart edges, 3-5% are all soft (criterion 2
        met), 2% (P24) stays restart-driven, and 2.5% is the edge. The two
        models agree within 0.16 ns / 0.2 A / 0.05 V.
     4. Done ([A83](../experiments/track_A_periodic_steady_state/A83_verilog_corrector_fix/RESULTS.md)):
        the fix in the Verilog co-simulation. 3% and 5% are soft with A81's
        unchanged RTL; the dither is 1.6 A.
     5. Next:
        - Done ([A84](../experiments/track_A_periodic_steady_state/A84_p24_perturbation_uniqueness/RESULTS.md)):
          a kick into the restart state is undone in one cycle by the
          fixed corrector, and locks the old one for good. The fixed
          controller has one attractor.
        - Done ([A85](../experiments/track_A_periodic_steady_state/A85_verilog_ton_resolution/RESULTS.md)):
          the RTL dither is the Ton / edge resolution. With 31 ps edges it
          falls from 1.66 to 0.90 A, and the Verilog controller meets
          criterion 2 in full at 5%. Roberts' minimum-duty-increment method
          is the alternative to a finer delay line.
     6. **Single-module level: all five criteria met at 3-7.5%, with the
        corrected controller, in the physical model (Python and Verilog)
        and cross-checked in the mathematical model (D43).** P24's stated
        1-2% negative current is not enough in either model.
     7. Done: device realism with EPC2067's datasheet Coss(V) (public; A59
        digitisation checked against three printed values).
        - [A86](../experiments/track_A_periodic_steady_state/A86_p24_nonlinear_coss_adopted_controller/RESULTS.md),
          physical model.
        - [D44](../symbolic_derivations/03_P24_native/D44_P24_EQUIVALENT_LINEAR_COSS.md)
          and [D45](../symbolic_derivations/03_P24_native/D45_P24_NONLINEAR_COSS_EVENT_MAP.md),
          mathematical model.

        **Results.**
        - **P24's 2% works with the datasheet curve:** every phase soft,
          phase 4 at -1.85 A and 10.24 V, and a unique attractor.
        - **The lower bound moves from 2.5-3% (linear) to 1.5-2%.** 1% is
          restart-driven, and 1.5% is the edge.
        - **The two models agree.** D45's nonlinear event map matches at
          2-7.5% within 0.05 A and 0.03 V.
        - **The mechanism is the high-side curve's shape.** No
          equivalent-linear capacitance reproduces it (D44); the high-side
          curve alone does (D45 part E).
        - **Correction.** D43's valley times were one 0.25 ns grid step
          early. The effect is at most 0.13 A; no conclusion changes.

        **So "P24's 1-2% is not enough" is qualified:** 2% works with
        typical Coss, and 1-1.5% does not.

     8. Done: the reverse-conduction drop.
        - [A87](../experiments/track_A_periodic_steady_state/A87_p24_reverse_conduction_drop/RESULTS.md),
          physical model.
        - [D46](../symbolic_derivations/03_P24_native/D46_P24_REVERSE_DROP_EVENT_MAP.md),
          mathematical model.

        **The data.** EPC2067 Fig. 8 at 25 C, checked against EPC's public
        SPICE model within 6-12 mV, and fitted per device as Vf 2.089 V
        plus 6.01 mOhm.

        **Results.**
        - Every phase stays soft at 2-7.5% (criterion 2 passes).
        - The loss is 55-57 W at 250 W out: 9.8 ns of low-side reverse
          conduction per edge, from the adopted 10 ns comparator-to-gate
          latency. It is 10 W at 2 ns.
        - The two models agree within 0.05 A, 0.03 V and 0.03 W.

        **Literature check.** Zhang et al., TPEL 2023, DOI
        10.1109/TPEL.2022.3217456 (A87 Section 4a).
        - It confirms the static Vth - V_goff + R_on i form.
        - It adds a dynamic threshold for Schottky-type p-GaN gates. It
          cannot be quantified for EPC2067 from public data, so P_rev is
          the static value.
        - It frames dead time as a trade-off between turn-on and reverse-
          conduction loss.

     9. Done: a predicted low-side turn-on.
        - [A88](../experiments/track_A_periodic_steady_state/A88_p24_predictive_low_side_turn_on/RESULTS.md),
          physical model.
        - [D47](../symbolic_derivations/03_P24_native/D47_P24_PREDICTED_LOW_SIDE_EVENT_MAP.md),
          mathematical model.

        **The rule.** The low side turns on at t_off + dtl. dtl is learned
        from the V_DS = 0 crossing (late: set to it; early: +0.05 ns). This
        is P25's timed dead time and a PWM-mode GaN driver's programmable
        dead time (LMG1210).

        **Results.**
        - The reverse-conduction loss goes from 56 W to 0 W at 2-7.5%, and
          every phase stays soft. The orbit equals the ideal-diode one.
        - GaN's 2.09 V reverse threshold leaves 0.16-0.22 ns after the
          crossing before any reverse conduction.
        - The dead time is 0.94-1.24 ns.
        - The two models agree within 0.04 A, 0.03 V and 3.5 ps.

     10. Done: the predicted low side in the Verilog controller
         ([A89](../experiments/track_A_periodic_steady_state/A89_verilog_predicted_low_side/RESULTS.md),
         co-simulated with A88's realistic plant at 5%).
         - **Result.** 0 W reverse-conduction loss, criterion 2 in full
           (dither 0.91 A), peak 27.0 V / 173 A, matching A88 within the RTL
           quantisation. The RTL's old reactive low side costs 109 W with the
           realistic device.
         - **A latent hazard, found and fixed.** A81's asynchronous
           phase-1 front end was armed at the turn-off command, a 10 ns
           driver delay before the physical turn-off. With the timed low side
           this caused a shoot-through at the handover (773 A, 38 V). The fix
           is 20 ns leading-edge blanking.
         - **The addition is opt-in and gated.** 26 of 26 unit tests pass
           (A81's 18 unchanged), synthesis is clean, and three co-simulation
           gates are bit-identical.

     11. Done: junction temperature 125 C.
         - [A90](../experiments/track_A_periodic_steady_state/A90_p24_junction_temperature_125c/RESULTS.md),
           physical model.
         - [D48](../symbolic_derivations/03_P24_native/D48_P24_HOT_JUNCTION_EVENT_MAP.md),
           mathematical model.

         **The data.** RDS(on) x 1.586 (Fig. 9, within 0.25% of the EPC
         model); reverse drop at 125 C; Coss unchanged (no public
         temperature data).

         **Results.**
         - The module still works: every phase soft at 2-7.5%, 0 W reverse
           loss, criterion 2 at 2-5% (7.5%: dither 1.09 A).
         - Conduction loss rises from about 12.4 to about 19.8 W.
         - The timing window narrows to 0.15-0.21 ns.
         - The two models agree within 0.04 A and 0.03 V.

     12. Done: gate-driver timing.
         - [A91](../experiments/track_A_periodic_steady_state/A91_verilog_gate_driver_timing/RESULTS.md),
           Verilog co-simulation at 5%.
         - [D49](../symbolic_derivations/03_P24_native/D49_P24_DRIVER_MISMATCH_OFFSET.md),
           mathematical model.

         **The data.** LMG1210: high/low delay mismatch 1 ns typical,
         3.4 ns maximum. There is no jitter specification, so σ = 30 and
         100 ps are a sensitivity.

         **Results.**
         - **The adopted correctors do not absorb a static mismatch.**
           They set their delay to a time measured from the actual edge,
           but add it to the command time.
         - **m = ±3.4 ns:**
           - the fixed 2.15 ns start-up dead time shoots through;
           - with 4.5 ns, both signs still shoot through after the
             handover. At +3.4 ns the high-side corrector learned a
             1.2 ns swing time from a transient.
         - **m = -1 ns:** 94% hard low-side turn-ons (an estimated
           2.0-6.9 W), then a shoot-through. Phase 4's crossing, 0.98 ns,
           is shorter than |m|; D47 gives 0.96 ns.
         - **m = +1 ns:** runs. P_rev 4.30 W, and D49 gives 4.31 W. The
           dither is 2.35 A.
         - **Jitter:** no shoot-through and at most 0.06 W, but the
           dither is 2.75 A (30 ps) and 4.73 A (100 ps), against 0.91 A.
         - **The gate (driver model off)** is bit-identical to A89 r2.

         **So the controller has to change before the next factor.** That
         is A92: an error-based update (the body-diode-conduction sensing
         of the adaptive dead-time literature), a floor on the actual dead
         time, and a start-up dead time above the maximum mismatch.

     13. Done: error-based correctors.
         - [A92](../experiments/track_A_periodic_steady_state/A92_verilog_error_based_correctors/RESULTS.md),
           Verilog co-simulation.
         - [D50](../symbolic_derivations/03_P24_native/D50_P24_ERROR_BASED_CORRECTORS.md),
           mathematical model.

         **The rule** follows APEC 2023 (DOI 10.1109/APEC43580.2023.10131397)
         and ECCE Europe 2025 (DOI 10.1109/ECCE-Europe62795.2025.11238584):
         - subtract the actual edge's error from the delay, with target
           94 ps and gain 1/2;
         - floors of 0;
         - start from 4.5 ns.

         **Results.**
         - **No cross-conduction** at m = 0, ±1, ±3.4 ns or σ = 30, 100 ps.
         - **The fixed point does not depend on m:** low-side edge 0.10-0.11 ns
           after the crossing. P_rev is 0 W, or 11.79 W where the floor binds
           (m = +3.4; D50 gives 11.77 W).
         - **Steady-state dither** is 0.43-0.75 A.
         - **The gate** is bit-identical to A89 r2.

         **Open.**
         - **The 826 A start-up/slot hazard (m = -3.4 ns).** Vo at the
           handover depends on m, the period falls below phase 4's fixed
           slot, and phase 4 starves.
         - **Jitter amplification** (1.65 / 5.51 A). The valley moves with
           the corrected edges, so the closed loop of correctors and
           circuit has to be modelled.

     14. Done, not adopted: period-following slots.
         - [A93](../experiments/track_A_periodic_steady_state/A93_verilog_period_following_slots/RESULTS.md),
           Verilog co-simulation.
         - [D51](../symbolic_derivations/03_P24_native/D51_P24_PERIOD_FOLLOWING_SLOTS.md),
           mathematical model.

         **The rules.**
         - Slots at (k-1)·T_meas/4 (P24/P25's T/nP), against the fixed
           T0/4 multiples.
         - A missed-slot guard.

         **Results.**
         - The m = -3.4 ns starvation is gone: 172-174 A, against 827 A.
           The guard alone gives 267 A.
         - **But** the steady-state dither rises to 1.04-1.60 A. The
           two-cycle component grows with the slot index, because the
           period's alternation is injected into the slots.
         - The orbit does not move (D51).
         - **Next:** slots from a two-cycle average of the period. The
           adopted design stays A92 until then.

     15. Done: a faster co-simulation plant.
         - [A94](../experiments/track_A_periodic_steady_state/A94_cosim_plant_speedup/RESULTS.md).
         - It reproduces the original plant bit for bit: 300k steps, and
           full replays of A89 r2, A92 j100 and A93 m3n_both.
         - It is 1.66 times faster per run.
         - Scheduling: at most 4 runs at a time.
         - Then the agreed code clean-up, before new physics.

     16. Code clean-up, in progress (agreed on 2026-10-01: results must not
         change; less duplication; faster).
         - Done:
           - [A95](../experiments/track_A_periodic_steady_state/A95_cosim_c_kernel/RESULTS.md):
             the plant step in C. Bit-identical, 3.17 times faster than
             the original.
           - The shared co-simulation package `src/scb_ivr/cosim/`: RTL,
             bridge, plants, entry point, preset, unit tests. The full
             replay gate passes on 4 archived runs.
           - `.gitignore` for run logs and build directories.
           - [A96](../experiments/track_A_periodic_steady_state/A96_cosim_c_loop/RESULTS.md):
             the step loop, the bridge's monitors and the Newton fallback
             in C. Bit-identical; a full run takes about 2 min, 4 at a
             time (originally 24 min alone, 70-73 min in batches).
           - One solver for the D47-D51 orbits:
             `src/scb_ivr/p24_orbit_solver.py`, with the entry point
             `scripts/p24_orbits.py --variant`. It replaces 5
             copy-and-paste outer loops, and all 13 archived orbits are
             recomputed bit-identically (`--gate`).

     17. Done, adopted: slots from the two-period average.
         - [A97](../experiments/track_A_periodic_steady_state/A97_verilog_averaged_period_slots/RESULTS.md),
           Verilog co-simulation, run on the shared package.
         - [D52](../symbolic_derivations/03_P24_native/D52_P24_CLOSED_LOOP_SLOT_RULES.md),
           mathematical model: the closed-loop linearisation with the
           correctors.

         **The rule.** Phase k's slot is at
         (k-1)·(T_{n-1} + T_{n-2})/8, with the follow rule and the guard.

         **Results.**
         - m = -3.4 ns: 156 A, against A92's 827 A.
         - The two-cycle component is back to A92's (0.13-0.18 A), and so
           is the dither.
         - A93's early high-side turn-ons are gone.
         - The orbit is unchanged.
         - With 100 ps jitter the turn-off spread is 5-14% above A92's.

         **What D52 shows.**
         - The two-cycle alternation is the closed loop's forced response
           to the trim's ±1 LSB limit cycle; the modes are at
           |λ| = 0.65-0.66.
         - The follow rule injects (k-1)/4 of the period alternation into
           phase k, amplified 4.9 times. Averaging removes it at z = -1.
         - Both models agree.

         **Adopted** (A97 RESULTS Section 7, with m3p's one-sided dither
         reading stated there). `src/scb_ivr/cosim/presets/p24_5pct_adopted.json`
         carries the three slot bits.

     18. Done: why gate-driver jitter is amplified.
         - [A98](../experiments/track_A_periodic_steady_state/A98_jitter_amplification/RESULTS.md),
           Verilog co-simulation.
         - [D53](../symbolic_derivations/03_P24_native/D53_P24_GATE_JITTER_CLOSED_LOOP.md),
           mathematical model.

         **The mechanism, in both models.**
         - Phase 1's current-comparator turn-off turns on-time jitter into
           period jitter (×10.5).
         - Phases 2-4 inherit it through their slots (0.68 A/ns).
         - The correctors cannot reduce it (≤ 7%).

         **The models agree.** D53 (linear circuit, exact controller)
         matches the co-simulation within 10-20%, and predicted 6 of A98's 7
         runs within the registered bands.

         **Gain 1/4 was tested and not adopted.** It halves the turn-ons
         before the valley but costs more reverse-conduction loss than the
         hard-on loss it saves.

     19. Done, not yet adopted: a timed phase-1 turn-off.
         - [A99](../experiments/track_A_periodic_steady_state/A99_timed_phase1_turn_off/RESULTS.md),
           Verilog co-simulation.
         - [D54](../symbolic_derivations/03_P24_native/D54_P24_TIMED_PHASE1_TURN_OFF.md),
           mathematical model.

         **The change.** The comparator only measures. dlo steps ±1 LSB
         toward 94 ps after the crossing.

         **Results.**
         - It removes the ×10.5 period amplification.
         - Jitter response of phases 2-4: −30 to −38%.
         - Without jitter, the trim's limit cycle is gone (0.018 A).
         - Both models agree, mostly within the registered bands; j30's
           period spread is 35% high.

         **Waiting on** a load-step test with a coarse/fine dlo rule.

     20. Done, recommended: the timed turn-off under load steps.
         - [A100](../experiments/track_A_periodic_steady_state/A100_timed_turn_off_load_steps/RESULTS.md),
           Verilog co-simulation.
         - [D55](../symbolic_derivations/03_P24_native/D55_P24_DLO_RULE_LOAD_STEPS.md),
           mathematical model.

         **The rule.** dlo's step doubles while consecutive decisions
         agree, up to 32 LSB.

         **Results.**
         - Under ±25 and ±62.5 A steps, phase 1's turn-off current stays
           within 0.6-1.7 A; A99's ±1 rule is off by 19-23 A.
         - Vo moves as in the comparator design.
         - Jitter: −24 to −35% against A97.

         **Trade-off review:**
         [`reports/TRADEOFF_SCORECARD.md`](TRADEOFF_SCORECARD.md), with
         one table for A92-A100, the loops to avoid, and the priorities to
         set.

     21. **Extension, kept separate (not part of the reproduction):** an
         auxiliary commutation branch for the high side's zero-voltage
         turn-on (A101, A102, D56, D57). Everything is in
         [`extensions/aux_commutation_branch/`](../extensions/aux_commutation_branch/README.md).
         Built and evaluated as cases; not adopted.

         **Main-line results computed there:**
         - **P24's 1-2%.** With P24's own inductor values (Table I) and
           node compositions, full high-side zero voltage without a branch
           needs at least 5.3% (D57 Section 2).
         - **Hard turn-on loss.** D56's central estimate (own Eoss plus the
           other node capacitances' charge through the channel; Qoss·V for
           identical devices) is the energy balance's minimum: 9.3 W for four
           phases at 5%. A91's lower bound is not reachable.
         - **The 2% target in the Verilog co-simulation.**
           - The adopted design is soft (A102 `ref_2pct`) and matches D51's
             2% orbit within 0.05 V.
           - The orbit, D51 at 2%, is in `symbolic_derivations/03_P24_native/diagnostics/`.
         - **The start-up overshoot.** The adopted design's own start-up
           reaches 1.277 V at the handover (88.6 µs), dips to 0.903 V and
           settles by about 150 µs. The start-up is the next main-line item.

     22. Done: the start-up sequence (main line).
         - [A103](../experiments/track_A_periodic_steady_state/A103_p24_startup_sequence/RESULTS.md),
           Verilog co-simulation.
         - [D58](../symbolic_derivations/03_P24_native/D58_P24_STARTUP_AVERAGED.md),
           averaged model: mode S is a voltage source, mode P a Ton-set
           current source, plus the integral loop. Within 0.03 V of the
           reference start-up.

         **Results.**
         - **The cause.** The overshoot (1.277 V) was mode S open loop at no
           load. The dip (0.903 V) was the load arriving at the handover.
         - **The fix, by sequence only.** Load from t = 0, handover at 72 µs,
           mode S Ton at the full-load value. Vo peaks at 1.013 V, is
           17.6 µs above 1 V and within 1% from 73.5 µs (before: 205.7 µs).
           This meets VRD 11.1's overshoot limits; the final state is
           unchanged.
         - **The condition.** The boot load must be ≳ 70% of full load. A
           light boot load needs a regulated mode S with a reference soft
           start (RTL), and mode P's light-load limit (≈ 100 A at the lower
           Ton clamp) remains.

     23. Done: the output-voltage loop as a PI on Ton (main line, T6).
         - [A104](../experiments/track_A_periodic_steady_state/A104_p24_voltage_loop_pi/RESULTS.md),
           Verilog co-simulation. New RTL input `cfg_kp`: +5.8% cells.
         - [D59](../symbolic_derivations/03_P24_native/D59_P24_VOLTAGE_LOOP.md),
           a sampled PI on D58's current-source plant. It reproduces A100's
           steps within 2 mV.

         **Results.**
         - PI at 30-150 kHz (the present loop is 7.5 kHz) cuts ±62.5 A steps
           from ±12% to ±4.6-1.1%, with recovery in 51-3 µs instead of
           ~100 µs. Every registered criterion is met in all ten runs, and
           D59 was within 7% on the excursions.
         - The series-capacitor resonance (140 kHz) showed no effect, even
           at 153 kHz.
         - The cost is Ton dither: at light load, phases 2-4's turn-off sd
           goes from 0.24 A to 0.27-0.36 A (100-150 kHz); +6-9% under 30 ps
           jitter.
         - **Recommended: 100 kHz** (±1.7%, within 1% in 10 µs).

     24. Done: the integrated single-module design on the standard matrix.
         - [A105](../experiments/track_A_periodic_steady_state/A105_p24_integrated_standard_matrix/RESULTS.md),
           22 Verilog co-simulations.

         **The single-module level's finish line** (A105 BOUNDARY Section 1):
         1. one integrated design passes the standard matrix (**done**);
         2. the model cross-checks (**done**);
         3. a summary of the open choices for evaluation (open).

         Line steps are the one operating condition left (A106).

         **Results.**
         - Both candidates pass every hard constraint in 22 of 22 runs: no
           overlap, peaks 165-176 A.
         - **I2 (timed phase-1 turn-off + A103's start + PI 100 kHz) is
           recommended.**
           - It is better than I1 (comparator) on every switching row:
             j30 0.49-0.53 A against 0.63-0.72 A; j100 1.04-1.19 against
             1.64-1.84 A; mismatch 0.02-0.16 against 0.22-0.32 A.
           - It is equal on the steps: ±25 A within ±6 mV, ±62.5 A within
             ±15 mV.
         - **T6's open half is not a blocking loop:** phase 1's sd is
           0.16 A at 0 ps.
         - **I1's proportional term** turns ADC-code toggling into Ton
           dither under driver mismatch. A deadband would fix it; not
           tested.

     25. Done: line steps on the integrated design.
         - [A106](../experiments/track_A_periodic_steady_state/A106_p24_line_steps/RESULTS.md),
           Verilog co-simulation with an input step (new opt-in plant
           feature).
         - **Results.** ±10% input steps move Vo by ≤ 18.5 mV with the PI
           (39-70 mV with the I-only loop). The ladder re-divides within
           25 µs. No overlap; zero voltage kept.
         - **One hard-constraint miss.** A +10% step over 1 µs peaks at
           207 A (> 200 A); over 10 µs, 171 A.
           - Input feed-forward or a bus slew limit would address it; not
             tested.
           - D59 misses the fast steps: it lacks the ladder's dynamics.

     26. **The single-module level is closed (2026-10-02).** All three
         items of the finish line are done:
         1. the integrated design (A105's I2) passes the standard matrix;
         2. the models cross-check it;
         3. the open choices are written up as cases:
            [`SINGLE_MODULE_SUMMARY_2026-10-02.md`](SINGLE_MODULE_SUMMARY_2026-10-02.md).

         Line steps (A106) were added, with one miss: a +10% step over
         1 µs peaks at 207 A.

         The next level (multi-module, package, thermal, protection,
         light load) is to be chosen with Mihai.

     27. Done: the integrated design over the series-capacitor range.
         - [A107](../experiments/track_A_periodic_steady_state/A107_p24_series_capacitor_range/RESULTS.md),
           Cs 0.6 and 8.7 µF.
         - [D60](../symbolic_derivations/03_P24_native/D60_P24_LADDER_RELAXATION.md):
           in mode P the ladder relaxes and does not resonate.
         - Also new: cfg `circuit` (any circuit value as a scenario) and
           the shared standard matrix `scb_ivr.cosim.matrix`.

         **Results.**
         - **No resonance anywhere.** The 100 kHz loop holds over the
           range, and load steps do not depend on Cs.
         - **At 8.7 µF the start-up peaks at 215 A.** That is mode S: the
           fixed ramp's margin is 19x. The ramp should scale with √Cs (a
           parameter; not run).
         - **At 8.7 µF fast line steps reach 221-244 A.**
         - **At 0.6 µF:** +1.7 V blocking, the high side turns on at ~10 V,
           more spread.
         - **D60 has the structure but not the rate** at a large Cs.

     28. Done: multi-module readiness (averaged, no co-simulation).
         - [D61](../symbolic_derivations/03_P24_native/D61_P24_MULTIMODULE_READINESS.md).
         - **The physics.** In mode P a phase's current goes as Ton/L, while
           its period depends on Ton alone, not on L or i_neg. With unequal
           inductors, Ton cannot give equal currents and equal periods
           together.
         - **Independent integrators** on a shared output diverge (±0.5 mV
           ADC offsets).
         - **Free-running modules slip an interleaving slot** in 9 µs per
           LSB of Ton difference: active synchronisation is required.
         - **Baseline:** one shared voltage loop, a common Ton, and slave
           modules slot-synchronised. The current sharing error then equals
           the inductor tolerance. Optionally, i_neg trims the sharing if the
           inductors match within +6%.
         - **The module interface:** common Ton in, phase-1 slot reference
           in, i_neg trim in, enable/pre-bias in; module current out,
           phase-1 timing out.
         - **What moves to the system level:** the voltage loop (A104's
           gains), Cout and the start-up sequence. The Cout experiment on
           one module is dropped.

     29. Done: the module's loss budget and efficiency.
         - [D62](../symbolic_derivations/03_P24_native/D62_P24_LOSS_BUDGET.md),
           on A105 I2's measured waveforms and the EPC2067 datasheet.
         - **Efficiency at 250 W out:** 80.7-89.3% with magnetic-core
           inductors (middle case 87.9%; 85.8% at 125 C).
         - **The middle case's three largest terms:** switch conduction
           (36%), the high side's valley hard turn-on (26%), gate drive
           (21%).
         - **P24 Table 2's air-core embedded inductors** (4-6 mΩ/nH) would
           give ~52%. At 1.47 nH and 125 A, only a low-R/L magnetic core is
           viable.
         - **Erratum:** the extension's D57 "as_main_inductor" case was the
           switch resistance. The effect is small.

     30. Track C started (multi-module): 4 modules, 16 phases, 1 kW.
         - **Framework:**
           - [Track C README](../experiments/track_C_multi_module/README.md):
             module count and the P24 consistency table;
           - C1: the bridge per module, bit-identical;
           - C2/C3: slave RTL, the generated `scb_multi`, M plants joined
             at every 4 ns window; M = 1 bit-identical.
         - **First experiment:**
           [C01](../experiments/track_C_multi_module/C01_four_modules_baseline/RESULTS.md),
           four A105 I2 modules on one output (D61 scheme A).
           - Every registered criterion passes except the L5 sharing check
             as written. Its metric reads 2% high; normalised, the result
             is within 2.3 A of D61.
           - Four identical modules behave as one module ×4:
             - steps +11.4 / −14.6 mV vs +11.65 / −14.68 mV;
             - start-up 1.0131 V;
             - valleys and high-side turn-on equal.
           - ±5% L shares ±4.7% (D61 ±5.5%).
         - **Flagged deviation:** the 16-phase interleave is not uniform.
           Phase 1 of each module sits one valley delay (9.44 ns) early
           (A93/A97's slot reference). The output current ripple is
           45.9 A rms against 6.6 A for a uniform grid. Correction: C02.
         - **New mechanism:** the slaves' valleys are not regulated (only
           the master's phase 1 is boundary-timed). D61's scheme B (i_neg
           trim) needs a per-slave valley target.

     31. The interleave deviation corrected:
         [C02](../experiments/track_C_multi_module/C02_uniform_interleave/RESULTS.md).
         - **The change:** opt-in `slot_lo`. Phases 2-4 and the slaves are
           slotted from phase 1's low-side turn-off. Default off; gates
           bit-identical.
         - **One module:** low-side turn-offs exactly T/4 apart. Identical
           to A105 up to the handover; valleys, V_DS, steps and jitter
           unchanged.
         - **Four modules:**
           - the 16 gaps are 14.49-14.54 ns (C01 4.4-23.9);
           - output current ripple 45.9 → 6.75 A rms; switching ripple per
             period 162.8 → 31.0 A pk-pk, as predicted;
           - sharing, steps and start-up equal to C01.
         - **Missed as registered:**
           - the window pk-pk (the Ton limit cycle moves the per-period
             mean by 10.7 A);
           - slave 1's late fires in j30 (6, each < 0.2 ns, mostly while
             the master's turn-off is still learning). Flagged: a
             predicted slave reference.
         - **Recommended for the design from C03** (the four-module
           standard matrix).

     32. The four-module standard matrix:
         [C03](../experiments/track_C_multi_module/C03_four_module_standard_matrix/RESULTS.md).
         - **The matrix:** 18 runs, no overlap in 72 module-runs. Each
           module equals its single-module row (valleys within 0.05 A,
           V_DS within 0.01 V). Steps within 8% of the single module's.
         - **A slave at +10% L** keeps zero-voltage switching (valleys
           ≤ −3.9 A; current −8.6%). D61's scheme A suffices to ±10%.
         - **Open:**
           - l_p48_1us's 207 A: phase 1's rail takes the whole step;
             scenarios (a)-(d) for A108;
           - rare late fires: slave 1 (C02's latency), and phase 1 with
             `slot_lo` in line steps (mechanism not identified; late fires
             are not time-stamped).
         - **Literature:**
           [LITERATURE.md](../experiments/track_C_multi_module/LITERATURE.md).
           The decisions mapped to papers, with DOIs; eight papers added
           and read.

     33. Line-slew tolerance:
         [A108](../experiments/track_A_periodic_steady_state/A108_p24_line_slew_tolerance/RESULTS.md),
         the adopted single module, ±4.8 V over 1-50 µs.
         - **Peak ≤ 200 A** from 2.4 V/µs rising, and at every falling
           slew.
         - **Every valley negative** only at ≤ 0.24 V/µs rising; falling
           not even at 0.096 V/µs (phases 3-4 at +9.6 / +12.1 A).
         - **Mechanisms, both quantitative:**
           - phase 1's timed turn-off adapts ≤ 1 ns per cycle, which
             follows ≤ 0.24 V/µs;
           - the slotted phases have no current correction, and the
             ladder lags a ramp by about rate × 11 µs, ~12 A per volt.
         - **Remedies screened:**
           - a per-phase Ton feed-forward makes the ladder unstable for a
             fraction above 0.53;
           - a peak limit is too slow (11 ns path).
         - **For evaluation:** the bus slew the module must ride.
         - **Candidate A109:** a per-phase valley trim of the slots. It
           also gives slaves the valley target D61's scheme B needs.

     34. The valley trim of the slots is falsified:
         [A109](../experiments/track_A_periodic_steady_state/A109_p24_slot_valley_trim/RESULTS.md).
         - The offsets wound up to their bound. Valleys did not move,
           jitter rose to 1.6 A sd, and four modules lost their
           interleave. No line step improved.
         - **The cause:** in the SCB at a common period, the high-rail
           phases carry the ladder's restoring current while it
           re-divides (phase 4: +13% at 0.096 V/µs). The extra current
           lifts their valleys. Slot timing cannot change that.
         - **Erratum** added to A108's mechanism.
         - **Not adopted** (default off; candidate for removal).
         - **Options left:** accept a short loss of zero-voltage turn-on;
           per-phase boundary turn-off during transients (the interleave
           slides); input slew shaping or active Cs balancing.
         - **Open:** derive the per-phase current split during ladder
           motion.

     35. Module spread, and the multi-module level closed.
         - [C04](../experiments/track_C_multi_module/C04_module_spread/RESULTS.md):
           - Cs ±20%: currents ±0.4%;
           - R ±30%: ±1.3% (the slaves act as ~3.3 mΩ sources);
           - with L ±5%: −5.2 / +6.1%.
           - No overlap, uniform interleave, zero voltage kept.
         - **Summary for evaluation:**
           [MULTI_MODULE_SUMMARY_2026-10-02.md](MULTI_MODULE_SUMMARY_2026-10-02.md):
           - the design;
           - the results;
           - the differences from P24;
           - the choices (sharing, bus slew, zero voltage during ladder
             motion, Ton resolution, slave reference);
           - what is not in this level.

     36. External review of the multi-module level (2026-10-03): five
         points, all checked true, all fixed.
         - **Wording:** the high side turns on at its valley (~9 V, up to
           9.62 V), not at zero voltage; only the low side switches at
           zero voltage. Corrected in the summary and the errata.
         - **Interleave:** ±0.05 ns is the mean. Cycle by cycle: ≤ 0.62 ns
           steady, ≤ 1.4 ns with jitter, ≤ 2 ns through steps
           (`matrix.gaps_per_cycle`).
         - **Code:**
           - `step_stats` returns inf when not recovered;
           - `plant.join_nodes` (Co-weighted, bit-identical for equal Co);
           - `scripts/acceptance.py`, the gate: all experiments ACCEPTED,
             43 misses documented, 0 unexplained.
         - **Safe to tell Mihai:** the four-module co-simulation runs and
           reproduces; the modules stay locked and interleaved; the low
           sides switch at zero voltage, the high sides at their valleys.
         - **Not safe to say:** "all ZVS" or "±0.05 ns throughout".

     37. High-side zero voltage by the negative current:
         [A110](../experiments/track_A_periodic_steady_state/A110_p24_high_side_zvs/RESULTS.md).
         - **Raising the target from 5% to 10-30%** brings the high-side
           turn-on from 9.0 V down to ~0. It follows D57's energy balance
           within 0.2 V: zero voltage first at 25% (D57: 26.7%).
         - **Efficiency** (D62 middle case on the measured waveforms) is
           best at **20%: 90.17%, +2.25 points over 5%**. The high side's
           hard turn-on (8.9 → 0.7 W) and the gate drive (lower
           frequency) outweigh the extra conduction.
         - **At 30% the valley-based turn-on timing breaks down** once the
           node clamps at the rail: 236 A peaks, hard turn-ons in between,
           the −62.5 A step does not recover, jitter spread 7-20 A.
         - **Next (A111):** a zero-voltage-aware turn-on measurement; then
           20% through the standard matrix as the efficiency candidate.

     38. The zero-voltage valley is falsified:
         [A111](../experiments/track_A_periodic_steady_state/A111_p24_zero_voltage_valley/RESULTS.md).
         - Targeting the node's arrival at the rail destabilises 25-30%,
           as A101 found with the branch: spreads 7-17 A, hard turn-ons
           to 10 V, peaks 227-270 A. Not adopted.
         - **Practical high-side zero voltage is reached at 25% with the
           existing controller (A110):** −0.16 to +0.86 V, the hard-turn-on
           loss 0.04 W against 8.9 W at 5%.
         - **Next (A112):** 20% and 25% through the standard matrix.

     39. The 20% and 25% designs on the standard matrix:
         [A112](../experiments/track_A_periodic_steady_state/A112_p24_zvs_designs_matrix/RESULTS.md).
         - **Both are robust in steady state:** no overlap; the high side's
           level holds under mismatch and jitter.
         - **20% passes** except the line-step edges: peaks 199-204 A,
           the 1 µs falling step recovers in 75 µs.
         - **25% oscillates slowly after load decreases and falling line
           steps:** 160-180 µs to settle. Phase 1's learned turn-off does
           not follow Ton.
         - **Next (A113):** A100's Ton feed-forward, or the comparator
           turn-off, at 25%.

     40. Phase 1's turn-off at 25% and 20%:
         [A113](../experiments/track_A_periodic_steady_state/A113_p24_zvs_turn_off_following/RESULTS.md),
         [A114](../experiments/track_A_periodic_steady_state/A114_p24_zvs_comparator_matrix/RESULTS.md).
         - **The dlo feed-forward** fixes the load step but wrecks line
           steps. Falsified.
         - **The comparator turn-off (I1)** keeps the steady state (90.15-
           90.18%) and fixes load steps and falling line steps (≤ 11 µs).
           But rising line steps run away (246-290 A): phase 1 stretches
           at its boundary and the slotted phases follow its period with
           unchanged rails.
         - **Established (A110-A114):**
           - practical high-side zero voltage at 25% and the efficiency
             optimum at 20% (+2.2 points), robust in steady state;
           - the limit is fast line transients, a property of "phase 1 at
             its boundary, phases 2-4 on slots" magnified by the large
             negative current.
         - **Remedy:** a controller architecture change (each phase on its
           own boundary) or an input slew limit.

     41. P24's 1 MHz design point:
         [A115](../experiments/track_A_periodic_steady_state/A115_p24_one_mhz_design_point/RESULTS.md).
         - **Why:** 25% (A110) was too much ripple. The papers keep the
           negative current within 5-10%.
         - **Design:** Eq. (4)'s 7.333 nH, Cs 15 µF, controller times ×5
           (period) or ×√5 (node), D59 loop at 60 kHz.
         - **Results:**
           - at 10% the high side turns on at 0.9-1.9 V (0.05 W of hard
             turn-on);
           - at 12.5%, zero voltage;
           - ripple +8.6% over the 5 MHz 5% design;
           - D57 within 0.23 V.
         - **Efficiency (D62 middle):** 89.0%. The switching losses fall
           16.8 → 1.6 W, but the inductor copper rises 2.6 → 13.8 W. With
           an ideal inductor, 93.6%.
         - **Open:**
           - the −62.5 A load step at 10% runs away: phase 1's timed
             turn-off lags Ton, and the loop is 3× faster per period than
             at 5 MHz;
           - 12.5% oscillates until the turn-off is timed (A110's
             flat-valley mechanism).
           - **Next, A116:** a slower loop, or A113's remedies, at 1 MHz
             10%.

     42. The 1 MHz design's transients:
         [A116](../experiments/track_A_periodic_steady_state/A116_p24_one_mhz_transients/RESULTS.md).
         - **The trigger is the valley crossing the zero-voltage threshold
           (H1).** A 30 kHz loop only turns the runaway into a 200 µs
           oscillation.
         - **The comparator turn-off (c60) fixes the load steps:**
           +28.0 / −28.6 mV, 16 / 22 µs. D59 is exact. The steady state
           is unchanged. It is the provisional 1 MHz controller.
         - **The ±4.8 V / 1 µs line steps fail in every variant** (c60:
           341 / 206 A, back in ≤ 52 µs). The ladder is 5× slower with
           Cs 15 µF.
         - **The trade-off map** is rewritten through A116, with the loop
           and which links are measured:
           [TRADEOFF_SCORECARD](TRADEOFF_SCORECARD.md).
         - **Next:** A117, the 1 MHz line-slew tolerance; then a smaller
           Cs.

     43. The missing link modelled, and tested:
         [D63](../symbolic_derivations/03_P24_native/D63_P24_VALLEY_MAP.md),
         [A117](../experiments/track_A_periodic_steady_state/A117_p24_one_mhz_line_slew_cs/RESULTS.md).
         - **D63 is a self-built, cycle-by-cycle valley map:** each
           phase's valley against D57's threshold, the reverse-conduction
           ramps, the slots, the ladder and the loop.
           - It reproduces every comparator load step within 10%, and
             line-step peaks within 1-9%.
           - It found a candidate rule: the timed turn-off with a
             comparator floor.
         - **A117 (14 runs, registered from D63):**
           - D63's peaks hold (within 10%); its outcome rule is falsified
             and refitted (> ~12 A for ≥ ~25 periods);
           - Cs 3 µF passes the fast line steps but its handover
             oscillates to 517 A, so Cs has a window;
           - the comparator's rising-step failure is not slew-limited.
         - **Next:** a Cs window and a softer handover in D63; A118, the
           floor turn-off.

     44. Machine learning as an extension
         ([ml_design_assist](../extensions/ml_design_assist/README.md),
         asked for 2026-10-03):
         - **A120:** a numpy MLP surrogate of D63, every registered target
           met (test peak MAE 2.0 A; co-simulation error 8.7 against
           D63's 9.2 A; 11 000× faster).
         - **Its search of 100 000 designs:**
           - at 1 MHz the 1 µs line step is binding;
           - with a bus slew ≥ 5 µs, the floor rule with Cs ≲ 8 µF is
             feasible in most of its range;
           - the comparator never is.
         - **Optimising on the surrogate selects its errors** (+7 A at
           the optimum), so every choice is re-checked by D63 and the
           co-simulation.
         - **Next:** A121 (Gaussian-process residual, active learning),
           A122 (a policy-gradient turn-off rule).

     45. The floor, and a 1 MHz candidate:
         [A118](../experiments/track_A_periodic_steady_state/A118_p24_floor_turn_off/RESULTS.md),
         [A121](../extensions/ml_design_assist/experiments/A121_gp_residual_active/RESULTS.md),
         [A122](../extensions/ml_design_assist/experiments/A122_rl_turn_off_policy/RESULTS.md).
         - **RTL option `cfg_lo_floor`** (+35 cells; default bit-identical):
           phase 1's turn-off is the earlier of the timed edge and its
           current reaching i_target − 2 A.
         - **A118:**
           - the floor holds phase 1 at −14.5 A in every step and fixes
             A115's runaway;
           - **floor + Cs 6 µF meets the load steps and the ±4.8 V steps
             over ≥ 5 µs** (≤ 193 A); start-up 157 A; efficiency 88.97%;
           - the 1 µs steps reach 201 / 206 A;
           - 15 µF fails ±4.8 V / 5 µs (211 / 241 A).
         - **A122:** RL in D63 rediscovers the floor.
         - **A121:** a GP registered before A118 predicted it within its
           error bars (92%).
         - **Next:** the standard matrix for the candidate.

     46. The candidate on the standard matrix:
         [A119](../experiments/track_A_periodic_steady_state/A119_p24_one_mhz_candidate_matrix/RESULTS.md).
         - **Passes:** driver mismatch and jitter (j30 sd 0.17 A, 0.01
           over), ±25 A, ±4.8 V / 10 µs.
         - **Misses:** −8 V / 10 µs at 205 A; with A118's 1 µs steps,
           the misses are all 1-6 A over 200 A.
         - **The floor also removes the low-line limit cycle at 40 V**,
           where the target sits past the threshold.
         - **A +3.4 ns driver mismatch costs 0.85 points** (reverse
           conduction 2.4 W; dtl cannot go below 0).
         - **Next:** the last amps (floor depth, fc), then four modules at
           1 MHz.

     47. The inductor from first principles, and the frequency it implies:
         [D64](../symbolic_derivations/03_P24_native/D64_P24_INDUCTOR_FREQUENCY.md).
         - **Model:** a stripline air-core inductor, R_dc/L =
           2ρ/(μ0 h t) and R_ac/L = 2ρ/(μ0 h δ), joined to the converter
           model at 0.5-5 MHz.
         - **At P24's in-package scale** (≤ 2 cm² per phase) the best
           frequency is 2-5 MHz, never 1 MHz. 1 MHz needs ~6 cm² × 4 mm
           per phase.
         - **The likely sweet spot:** 2-3 MHz with a 10-15% target
           (margin 5-10 A).
         - **Redirects the plan:** a 2-3 MHz design point before four
           modules at 1 MHz.

     48. The 2.5 MHz design point:
         [A123](../experiments/track_A_periodic_steady_state/A123_p24_candidate_last_amps/RESULTS.md),
         [A124](../experiments/track_A_periodic_steady_state/A124_p24_two_point_five_mhz/RESULTS.md).
         - **A123:** no single lever closes 1 MHz's last 1-6 A.
         - **A124, 2.5 MHz, 12.5%, floor, Cs 6 µF, 100 kHz:**
           - **90.61%**, the best measured;
           - a 7.9 A margin;
           - load steps +15.9 / −12.0 mV;
           - falling line steps pass;
           - the no-floor control recovers (D63's refitted rule,
             prospective).
         - **Open:** rising line steps (+4.8 V / 5 µs 210 A), a limit
           common to every frequency.
         - **Recommended design:** 2.5 MHz / 12.5%.
     49. Conformal bands for registered predictions:
         [A125](../extensions/ml_design_assist/experiments/A125_conformal_registration/RESULTS.md)
         (extension `ml_design_assist`).
         - Tested in run order on the 43 bounded registered D63 rows of
           A117-A124. Peak coverage at nominal 80%: 74% (S), **82%
           (signed, band −1.3% to +18.4% of D63)**; the hand ±10% band
           was in effect a 76% band.
         - **Found:** D63's second weak domain (−8 V / 10 µs at 1 MHz,
           +18-22%); the Vo extreme's sign flips in 9 of 43 rows; the
           recovery time is good only to ×3.
         - **From now on** each boundary registers the conformal band
           (Mondrian and signed, 80%) next to D63's point; the hand
           ±10% is retired.
     50. Vin feed-forward for rising line steps:
         [A126](../extensions/ml_design_assist/experiments/A126_ppo_line_feedforward/RESULTS.md),
         [A127](../extensions/ml_design_assist/experiments/A127_ppo_anchored_feedforward/RESULTS.md),
         [A128](../extensions/ml_design_assist/experiments/A128_cosim_vin_feedforward/RESULTS.md)
         (extension `ml_design_assist`).
         - **A126:** PPO policies gamed the reward (steady state
           shifted); invalid.
         - **A127:** anchored pure feed-forward (asymmetric critic)
           passes the steady and long checks 3/3; distilled to a
           6-parameter falling-step rule (Ton from phases 4, 2-3 to
           phase 1 while Vin falls).
         - **A128 (cosim, 2.5 MHz, RTL `scb_vff.v`, opt-in cfg "vff"):**
           every A124 row <= 200 A (worst 188 A): +4.8 V 1/5 µs
           181.5/175.4 A, −4.8 V 1 µs 175.5 A; steady state and loads
           unchanged; vff off bit-identical.
         - **Cost:** −8 V / 10 µs peak 168.5 → 188.2 A, Vo −28 → +38 mV
           (registered no-harm Vo criterion misses).
         - **A129** ([RESULTS](../extensions/ml_design_assist/experiments/A129_cosim_vff_slope_gate/RESULTS.md)):
           a latched slope gate (cfg vff "gth" 100 codes = 2 V; on at
           g ≥ gth, off at g = 0) removes the cost: −8 V / 10 µs 170.9 A,
           |Vo| 28.6 mV (A124 168.5 / 28.2); −4.8 V / 1 µs 173.6 A; worst
           row 181.5 A. The 2.5 MHz standard matrix (m, j, ±25 A) passes
           with and without it. **Adopted** as the line-step closure:
           steps ≤ 4.8 V at any tested slew ≥ 1 µs; −8 V / 5 µs is 208 A
           with the gate closed, so 8 V falls still need ≥ 10 µs.
         - **A130** ([RESULTS](../extensions/ml_design_assist/experiments/A130_cosim_slope_boundary/RESULTS.md)):
           bus-slew spec of the adopted design (cosim, two step phases):
           steps ≤ 4.8 V ≥ 1 µs (4.8 V/µs, rise and fall); −8 V ≥ 6 µs
           (1.33 V/µs; 192.2 A); +8 V ≥ 10 µs (0.8 V/µs; 198.3 A,
           marginal). **Line closed.**
         - **A138-A139 (2026-10-05, GP level-set map, L / Cs x 0.7-1.3):**
           [A139](../extensions/ml_design_assist/experiments/A139_gp_boundary_noise_floor/RESULTS.md)
           corrects A130's spec: the peak is not monotone in slew, so a
           minimum slew is not a spec. Falling -4.8 V: 173.5 A at 1 us and
           172.2 A at 5.1 us (nominal), 192.2 A at 2.3 us (L x 0.9, Cs x
           1.05; corrected in A140); rising at L x 0.7: +4.8 V 185.2 / 188.6 /
           205.9 A at 1 / 5 / 20 us; nominal +8 V 197-209 A at every slew.
           A139's certified table (95 % bound) is the spec under tolerance.
           A138's own bands failed (GP noise collapse, budget to one
           direction); A139 measured the scatter (heavy-tailed: one step
           position in six adds +14 A) and passed 3/3.
         - **A140 (2026-10-05, why):**
           [RESULTS](../experiments/track_A_periodic_steady_state/A140_p24_slew_nonmonotone/RESULTS.md).
           Falling: the vff slope gate (gth 100) stays shut on -4.8 V
           slower than ~2.3 us, and phase 4's turn-on current rises
           (191.6 A at 2.5 us vs 162.2 A at 2 us with the gate open).
           gth 50 flattens -4.8 V but costs -6.4 V (214 A) and L x 1.3
           -8 V / 10 us (198 A): gth stays 100, falling spec = windows.
           Rising: the high slow-ramp peaks follow a duplicate phase-1
           turn-on (two turn-ons ~6 ns apart restart the Ton timer, +20-38
           A); without it L x 0.7 +4.8 V stays <= 194 A at 1-40 us. Next:
           A141, the duplicate turn-on in the RTL.
         - **A141 (2026-10-05, fix):**
           [RESULTS](../experiments/track_A_periodic_steady_state/A141_p24_floor_late_report/RESULTS.md).
           The duplicate is an RTL defect: the floor fires in the window
           before the committed timed edge (or slave slot), its report
           arrives two windows later in UP and was ignored, so Ton counted
           from the later clocked turn-on. cfg `floor_late` 1 (late report
           -> t_on = a_tlo + dt_pred; t_lo kept, it is the slaves'
           ext_ref): 0 duplicates in 18 runs, peaks <= nodup + 1.9 A.
           L x 0.7 rising: +4.8 V <= 191.6 A at 1-40 us; +8 V 210.1 A at
           20 us, 182.1 A at 50 us. **Adopted** (single module); four
           modules provisional (2 rows: 180.1 / 177.7 A; the handover's
           slave duplicates at 145 us are removed too) - C12 reran the
           matrix: adopted on four modules too.
     51. The final design on four modules:
         [C05](../experiments/track_C_multi_module/C05_four_module_final_design/RESULTS.md),
         [C06](../experiments/track_C_multi_module/C06_slave_floor/RESULTS.md);
         [summary Section 8](MULTI_MODULE_SUMMARY_2026-10-02.md).
         - **C05:** four modules of A124 + A129's feed-forward pass the
           steady state, load and line steps and ±10% slave L, but m1n,
           m3n, j100 fail after the handover: a slave's slotted phase 1
           has no current-decided turn-off, its valley runs to −96 /
           −130 A, the master's Ton rises to its cap (positive feedback).
         - **C06:** A118's floor on a slave's phase 1 (cfg `slave_floor`,
           RTL + bridge, off bit-identical, unit tests 64/64): 18/18 rows
           without overlap, peak ≤ 185 A, locked.
         - **Adopted (user decision, against the registered criterion
           6)** with residuals: late fires in the post-handover
           transient (m1n 19, m3n 68), l_m48_1us +14% Vo / 11.1 µs
           recovery, per-cycle spacing up to 65 ns through line steps
           (35 ns without the floor), back < 0.5 ns within 100-150 µs.
         - **C07:** C04's module spread on the final design: floor on, no
           overlap, ≤ 193 A, locked; R ±30% moves valleys ±1.7 A, steady
           state unchanged by the floor (≤ 0.053 A); floor off 265 A.
         - **Erratum:** A105's period was 232 ns (T/16 14.5 ns), not
           1 µs; the final design's 31.6 ns spacing is wider.

     52. L tolerance and the feed-forward's phase-1 cap (2026-10-04):
         [A134](../experiments/track_A_periodic_steady_state/A134_p24_inductance_cap_lock/RESULTS.md),
         [A135](../experiments/track_A_periodic_steady_state/A135_p24_relative_cap/RESULTS.md),
         [A136](../experiments/track_A_periodic_steady_state/A136_p24_relative_cap_lowpass/RESULTS.md),
         [A137](../experiments/track_A_periodic_steady_state/A137_p24_vff_restart_at_handover/RESULTS.md),
         [C08](../experiments/track_C_multi_module/C08_relative_cap_four_modules/RESULTS.md),
         [C09](../experiments/track_C_multi_module/C09_seed_four_modules/RESULTS.md),
         [C10](../experiments/track_C_multi_module/C10_seed_before_entry/RESULTS.md).
         - **A134:** A132/A133's "ladder limit cycle" is a lock made by
           scb_vff's absolute phase-1 cap (A128: k / rail, k = L0 x 180 A).
           When the steady Ton a load needs crosses it (s_p62 at L x 1.1,
           n0 at L x 1.3), phase 1 sits at the cap, rail 1 rises to 16.5 V,
           the slotted phases saturate the loop and Vo falls 90 mV. D63 with
           the RTL-exact cap reproduces it; k = 0 or k x L/L0 removes it.
           The adopted design was within 200 A only at L0 (rising rows
           206-214 A at L x 0.7-0.9, cap-bound at 1.05, locked at 1.1).
           A133's L x 1.3 step rows fell in phase 1's learning phase
           (timed at 818 us, after the 800 us step).
         - **A135:** a relative cap (ton x 1.3 x rss / rail) never locks but
           follows the loop's transient ton rise: L0 +4.8 V / 1 us 203 vs
           183 A. Not adopted.
         - **A136:** the relative cap on Ton's low-pass (cfg vff rel_q8 320,
           rel_lp 1) equals the absolute cap at L0 (step rows within 2.8 A)
           and is idle in steady state. **Adopted for the operating mode:**
           L x 0.7-1.3, every A124 row <= 189 A, no lock. Open: handover
           late fires (m3n 107-173) and start-up peaks 185-218 A.
         - **A137:** restarting the feed-forward's low-passes at mode P
           (cfg vff seed 1) removes that regression at L0 and L x 1.3 (m3n
           late fires 11 / 0, start-up peaks 163 / 152 A, below the original
           184 A), operating mode unchanged; at L x 0.7 the handover stays as
           with the old cap (mode S's fixed Ton), so the registered criterion
           fails. **Adopted by user decision (2026-10-04):** the design's
           setting is g125 + vff {rel_q8 320, rel_lp 1, seed 1}.
         - **C08:** four modules at L x 1.2 lock with the absolute cap
           (10.5 %, Vo 0.917 V) and hold with A136's (1.12 %, Vo 1.000 V);
           C06's rows keep the hard constraints, but the handover late fires,
           m3n's end-window sd (0.11 A) and s_m25 (+7.3 A) are new: rerun
           with A137 (C09) before adoption.
         - **C09:** the restart does not carry over to four modules. The
           slaves enter mode P 30-80 ns after the master, when the master's
           first ADC sample has already kicked the broadcast Ton 1136 -> 683,
           so they seed Ton's low-pass there; their phase-1 cap is ~0.7 of
           need and they lock for ~35 us (rail 1 13.8-15.4 V): peaks
           192.5-203.5 A, handover late fires (C08 locked all four modules).
           After 242 us the design is C06's. C08's s_m25 +7.3 A was the step
           offset (C06 at C08's offset: 152.7 A); C08's m3n sd is the voltage
           loop's ADC limit cycle (one code = 5.69 Ton LSB), history-
           dependent, also in C06's ls_p10. Not adopted: the four-module
           final design stays C06 (absolute cap) until C10 seeds every
           module from a value independent of its entry time.
         - **C10:** seed 2 (cfg vff seed 2) restarts Ton's low-pass from
           the Ton of the clock before mode P (mode S's 1136) in every
           module. Four modules: slave rail 1 <= 12.36 V on all 18 rows,
           no lock, steady-row peaks 163-180 A, post-step peaks within
           -2.2..+4.2 A of C06 (max 188.7 A); handover late fires m1n 25 /
           m3n 90 (C06 19 / 68). Single module: 18/18 records identical to
           seed 1. One registered item fails: one late fire on s_m62 after
           the step (C06 at the same step offset 0, C10 at C06's offset 0).
           **Adopted by user decision (2026-10-05):** the four-module final
           design is C06 + vff {rel_q8 320, rel_lp 1, seed 2}; the single
           module's adopted setting is g125 + the same vff (one scb_vff for
           both levels).
         - **C11:** that design at L x 1.2 (s_p62, m3n, l_p48_1us) and
           L x 1.3 (s_p62): handover clean (rail 1 <= 12.87 V; C08 without
           the restart 17.2 V for 52 us, 212.8 A), peaks <= 188.0 A, no
           lock (ladder <= 1.22 %), late fires 0-5. Four modules hold
           L x 1.0-1.3 handover included; L x 0.7-0.9 not run.
         - **C12:** that design + cfg floor_late 1 (A141) on all 22 rows
           (C10's 18 + C11's 4): 0 floor-first duplicates (44 before),
           peaks <= 188.0 A (L0 <= 184.0 A), rail 1 <= 12.87 V, late
           fires <= 5 (m3n 108 vs 90), no lock. **Final four-module
           design = C10 + floor_late 1.**

     53. Random-stimulus test of the adopted single-module RTL (2026-10-05):
         [A142](../experiments/track_A_periodic_steady_state/A142_p24_random_stimulus/RESULTS.md).
         120 seeded draws (L / Cs x 0.7-1.3, driver, line + load steps,
         step instant incl. the mode-P comparator phase) with event-level
         oracles: 0 floor-first duplicates, 0 overlaps, every run settles;
         criterion 3 fails on one draw. A rising line step during the
         comparator phase (144 us to the timed switch, 520-810 us)
         oscillates: phase 1's comparator holds its valley by stretching
         the period, phases 2-4 lose theirs, peaks 245-388 A, Vo up to
         +-10 %. It reaches inside A139's certified envelope (+4.8 V at
         4-5 us, nominal L / Cs: 254 / 247 A); timed mode is clean (same
         step 196 A). **The single-module controller is not frozen; A143 =
         a comparator-phase fix, C13 waits.**

     54. Shortened comparator phase (2026-10-05):
         [A143](../experiments/track_A_periodic_steady_state/A143_p24_short_comparator_phase/RESULTS.md).
         Mechanism (records): the stretched period deepens the phase 2-4
         valleys; their error-based dt_pred then falls 11 -> 2-4 ns in one
         or two reports (it rises 0.28 ns per report), the high side turns
         on with the valley current still flowing, and phases 2-4 swing
         with the series capacitors (~4.6 us). D63 has no dt_pred block and
         stays damped. Fix: cfg lo_learn 1024 -> 4 (no RTL change; A99's
         1024 served a 1-LSB dlo rule that A100 replaced). Pass 6/6: A142's
         rows 351 / 254 / 247 / 388 -> 196 / 176 / 176 / 186 A; handover
         better (L x 0.7 m3n 182 -> 146 A, L x 1.3 rail 1 12.81 -> 12.38 V);
         A129 matrix + L corners -1.7 ... +4.8 A (max 191.4 A); four
         modules m3n late fires 108 -> 4. The trim stays at +1 A, so the
         floor sits 2-4.5 A deeper. **Adopted on one and four modules: the
         single-module controller is frozen; C13 runs with lo_learn 4.**

     55. Four-module random-stimulus test (2026-10-05):
         [C13](../experiments/track_C_multi_module/C13_random_stimulus_four_modules/RESULTS.md).
         30 random draws (L / Cs x 0.7-1.3, driver mismatch, line + load
         steps, steps from 145 us) on C12 + lo_learn 4. As registered 5/6:
         one floor-first duplicate (y08), traced to a rounding tie - floor
         and clocked turn-off 0.36 LSB (11 ps) apart, the floor's report
         rounds to t_lo, so floor_late cannot order them; second turn-on
         on a gate already on, peak normal. 279 records hold 17 K1 races
         (0.04-26.7 LSB, the mirror order) and this one: known class K5.
         No NEW events, all settle, rail 1 <= 12.53 V. Peaks > 200 A only
         on falling ramps outside A139's table; one module gives the same
         within 1-11 A. **Four-module design frozen; the multi-module level
         is closed.**

     56. Package layer opened (2026-10-05, user decision):
         [D65](../symbolic_derivations/03_P24_native/D65_P24_PACKAGE_PARASITICS.md),
         P24 Figs. 5-6 transcribed (paper_locked, coverage LOCKED). From
         first principles with the steady waveforms: Fig. 5's lateral
         output / ground copper to the central strip dominates - 30.7 W per
         250 W module with one 35 um layer each, 429 um of copper per stack
         for 1 %; vias, strip and Cs ESR (<= 0.5 mOhm) < ~1 % together. The
         commutation loop bounds the high-side voltage: <= 141 pH at the
         steady 143 A for 40 V, 72 pH at 200 A, 37 pH at C13's 260 A
         (published embedded-GaN loops 230-320 pH). **Next: the loop
         inductance in the co-simulation plant (one parasitic, swept
         25-300 pH on the frozen design).**
     57. The cost of passive current sharing (2026-10-05, math):
         [D66](../symbolic_derivations/03_P24_native/D66_P24_SHARING_COST.md).
         Calibrated on C12 ls_p5 / ls_p10 and C07 all_n0 (the measured −5 %
         module lies between the two valley bounds). The heavy (smaller-L)
         module binds the peak, not the temperature: through transients it
         reaches 200 A at about ±5 % worst-case L spread or −9 % on one
         module (+12-18 % loss there, 2-5 K at an assumed 1 K/W); ±10 %
         worst case 210-214 A, +25-34 % loss. An i_neg trim (D61 scheme B)
         cannot fix it: the heavy module's valley margin falls to 2.7 A at
         one −5 % module (0.5 A at 43.2 V) and below zero beyond. Sharing is
         an inductor-matching specification; C03's "±10 % sufficient" holds
         only for larger L (erratum in C03).
     58. Commutation-loop inductance in the plant (2026-10-05, mixed):
         [A144](../experiments/track_A_periodic_steady_state/A144_p24_commutation_loop_inductance/RESULTS.md).
         cfg "loop" (l_ph in series with each high-side drain, parallel
         damping; off bit-identical) on the frozen design, 50-300 pH, Q 7.
         The controller survives (0 late, 0 new duplicates, peaks -6..+3 A).
         Device voltage fails at every L: besides D65's own turn-off
         (steady SH1 17 / 27 / 34 / 52 V), a hard turn-on of phase k-1
         rings SH_k (already at 2 rails, 24 V) to ~24 + 1.7 dV,
         independent of L: 46-47 V at start-up, 57-58.5 V after a +4.8 V /
         1 us line step. Loop energy 3.9 / 7.7 / 11.3 / 24.5 W per module
         (1 % needs ~30 pH). Undamped, the ring breaks the valley tracking
         (8000+ late fires, 225 A). D65's single-edge bound holds within
         1.5 V. **Next: finite switching speed (both edges); loop Q is a
         question for Mihai.**
     59. The premise behind 2.5 MHz (2026-10-05, math):
         [D67](../symbolic_derivations/03_P24_native/D67_P24_FREQUENCY_PREMISE.md).
         The repo cited D64 (air-core stripline) for 2.5 MHz, but A124's
         90.61 % uses D62's MPC-class R/L (79 µΩ/nH), the core family of
         P24's package (12 parallel HBS1 per phase at 1 MHz, 8 modules).
         In Fig. 5's 0.25-0.63 cm² per phase an air-core picks 5 MHz (2-9
         points above 2.5 MHz). 2.5 MHz therefore assumes a magnetic
         inductor (~29 HBS1-class units per phase at 144 A); the inductor
         technology joins the questions for Mihai. Corrected: D64 scope
         note, A124 erratum, P24 Fig. 5 transcription, scorecard T14, the
         Mihai summary; track_C README's P24 table now lists every final
         design choice with its reason.
     60. Sharing cost checked in co-simulation (2026-10-05, RTL cfg only):
         [C14](../experiments/track_C_multi_module/C14_sharing_spread_check/RESULTS.md).
         Frozen four-module design, module 2 heavy. D66 holds in steady
         state (share +7.3 / +7.7 / +14.9 %, peaks 155.8 / 156.4 / 168.4 A);
         its transient is 2-7 A pessimistic (194.4 / 195.4 / 207.9 A for
         ±5 % worst / −10 % one low / ±10 % worst; nominal increment 40.7 A,
         not 45 A). The 200 A crossing is near ±7 % worst-case spread, so
         the summary's ±5 % holds with 5.6 A margin. A +4.8 V step's second
         Vo bump (~35 us, the ladder rebalancing) grows with the spread:
         +6.1 mV nominal, +12.9 mV (over 1 %) with one module at −10 %.
     61. Finite switching edges in the plant (2026-10-06, mixed):
         [A145](../experiments/track_A_periodic_steady_state/A145_p24_finite_switching_edges/RESULTS.md).
         cfg "edge": the channel current is a right-hand-side source during
         an edge (turn-off ramp, hard turn-on ramp until V_DS <= 0; off
         bit-identical). 72 / 144 A/ns (143 A in 2 / 1 ns), 50-150 pH, Q 7:
         the controller holds everywhere, but V_DS <= 40 V fails at every
         point (best 50 pH / 2 ns: 37.3 V start-up, 41.8 V after +4.8 V /
         1 us). A ramp turns L di/dt into channel loss rather than removing
         the overshoot (-6 / -27 % at 100 pH, not a ring's sinc -13 / -47 %).
         Steady state <= 33.9 V up to 150 pH. Loop-dependent loss 1.4-1.7 /
         3.8 / 6.3-6.4 W at 50 / 100 / 150 pH: 1 % at ~70 pH (A144's
         0.5 L I^2 was twice the damper's energy). Edges alone 1.2 / 2.7 W;
         D62's turn-off formula ~30 % low. **The hard-turn-on overshoot is a
         control problem (next: A148 in the ML block); loop spec ~70 pH.**
     62. CNN identification of the commutation loop (2026-10-06, ML):
         [A146](../extensions/ml_design_assist/experiments/A146_cnn_loop_identification/RESULTS.md).
         From one simulated V_DS capture (unknown probe 0.7-2 GHz, noise,
         jitter, I0 error) a 1-D CNN reads L / Q / di/dt / k with medians
         2.2 / 4.0 / 5.9 % / 0.012 and 90 % conformal coverage 0.90-0.91
         (damped-sine fit 7.9 / 25 / 42 %). A 6-parameter simulator fit is
         more accurate (1.1 / 0.6 / 1.7 %) but sticks at a bound on 6 of 40
         captures, 5 of them fast edges; started from the CNN it recovers 4.
         3/5 as registered (the misses are the measurement limits).
         **Procedure: CNN, then fit; needs noise <= ~0.4 V rms, probe
         >= 0.7 GHz and > 1 / t_f, I0 within ~2 %.**
     63. Learned anomaly detector against the oracles (2026-10-06, ML):
         [A147](../extensions/ml_design_assist/experiments/A147_cnn_anomaly_detector/RESULTS.md).
         2/4 as registered. On the oracle classes the CNN autoencoder adds
         nothing (AUROC 1.000 vs z-score 0.999; z-score 0.3 % false alarms
         vs 1.4 %). Its unexplained flags found a property no check
         watched, ZVS loss: in the frozen design, after the in-spec +4.8 V /
         1 us step, phase 1's low side turns off at +12..+15 A for ~13 us,
         so the next phase-1 turn-on is hard (V_DS 17-19 V vs 3.9 V).
         **This is the root cause of A144 / A145's line-step overshoot
         (SH2 52-58 V).** Oracle "zvs" added in A148.
     64. Phase 1's low-side timing through steps (2026-10-06, mixed):
         [A148](../extensions/ml_design_assist/experiments/A148_rl_zvs_line_step/RESULTS.md).
         Volt-second law on phase 1's timed edge (cfg vff "vs_g", off
         bit-identical) against PPO. FAIL 3/7, not adopted. Load steps are
         fixed (s_p62 turn-on V_DS 11.5-12.2 -> 6.9-7.2 V on every phase;
         with loop + edges 36.1 -> 32.5 V at 50 pH). The rising step is
         not: rail 1 takes the whole step, phase 1 needs ~22 % more
         volt-seconds, the common period stretches 504 -> ~600 ns and Vo
         is back in 1 % after 42 us instead of 8; switch 41.8 -> 41.2 V at
         50 pH. Falling steps stay below start-up (36.9 / 42.6 V at 50 /
         100 pH). RL neither found nor beat the law: 8 of 9 policies fail
         the steady check (features downstream of the action close a loop).
     65. The control path for the package closed (2026-10-06, mixed):
         [A149](../extensions/ml_design_assist/experiments/A149_bo_rising_step_overshoot/RESULTS.md),
         [A150](../extensions/ml_design_assist/experiments/A150_gpbo_vo_priced_package/RESULTS.md).
         A149 (FAIL as registered, stop rule): D63 gains an SH_k block;
         post hoc the rail term alone keeps 50 pH <= 40 V (38.4 / 38.8 V)
         but Vo needs 42 us and +4.8 V / 5 us oscillates (325 / 223 A,
         A143's dt_pred). Charge balance: a held phase-1 valley stops the
         ladder until phases 2-4 dig deeper, an output deficit, so every
         ZVS-holding law measured needs 41.6-42.5 us. A150 (FAIL, counted
         as no): constrained GP-BO over (gr, gt) in cosim found the band its
         5 rows allow (gr 0.675-0.725, gt 0.175-0.35; 39.85 V), but the
         neighbouring slews and L x 1.3 oscillate (203-275 A) and Vo back
         is 31-52 us. **Not solvable by control at an acceptable Vo cost
         (scorecard T20). ML lesson: measure a family constraint on its
         worst member.**
     66. A slow hard turn-on (2026-10-06, mixed):
         [A151](../experiments/track_A_periodic_steady_state/A151_p24_slow_hard_turn_on/RESULTS.md).
         cfg edge didt_on < didt_off slows only the hard turn-on, the
         ring's excitation; the 72 A/ns turn-off and the controller stay.
         Every switch <= 40 V incl. start-up up to 150 pH: 50 pH at
         36 A/ns 37.1 V, 100 pH at 18 A/ns 36.4 V, 150 pH at 18 A/ns
         38.0 V; +0.12-0.36 W, load-step Vo +1.9 us. 9 A/ns is too slow; a
         5 us bus slew does not help. 4/5 (the single-edge harness
         underpredicts at >= 100 pH). Post hoc (A152): criterion 4 checked
         post-step peaks only; at 18 A/ns the start-up handover reaches
         224 A at 100 pH.
     67. The package drive specification (2026-10-06, mixed):
         [A152](../experiments/track_A_periodic_steady_state/A152_p24_drive_spec_robustness/RESULTS.md).
         Start-up fix, cfg only: ton_ns = 35.5 + 36 A / turn-on di/dt (open
         mode S loses on-time on slow hard turn-ons, Vo 0.958 V at the
         handover, and the loop's P term added 15 ns): 224 -> 155 A at
         100 pH, nothing else moves. S50 (50 pH, turn-on 36 A/ns, turn-off
         72, ton 36.5 ns) passes on 13 rows (falling, L x 0.7 / 1.3,
         +4.8 V at 2-10 us) and four modules: <= 37.6 V, start-up
         <= 198 A, post-step <= 180 A. S100 (100 pH, 18 A/ns, 37.5 ns) 4/5:
         6 late fires on -8 V / 10 us, no consequence. 300 pH fails at any
         turn-on rate: the 72 A/ns turn-off ring alone is 48.8 V steady, so
         above ~150 pH the turn-off must slow too (loss). Also fixed:
         gen_multi read "signed" as a port name, so no four-module build
         compiled between A148 and A152 (626a8f0). **Package spec: loop
         <= 50 pH (loss allows ~70 pH for 1 %), a separate turn-on drive
         <= 36 A/ns, start-up Ton compensated. EPC2067 is rated 40 V
         continuous, 48 V transient (EPC Phase 16: <= 120 % for <= 1 % of
         life). Questions for Mihai: P24's turn-on di/dt, his derating
         rule, P24's actual loop L, how P24 sets the start-up Ton.**
     68. The slow turn-on derived and tested (2026-10-07, mixed):
         [D68](../symbolic_derivations/03_P24_native/D68_P24_SLOW_TURN_ON.md),
         [A153](../experiments/track_A_periodic_steady_state/A153_p24_slow_turn_on_laws/RESULTS.md).
         From the node charge (2 + 3 EPC2067 at 12 V, Q0 ~ 162 nC): the
         turn-on ramp lasts sqrt(2 Q0 / di/dt) and ends when node swing +
         L di/dt reaches the rail, so the line-step overshoot depends on
         x = L * di/dt_on only (<= 40 V for x <= 3.2 V), and mode S loses
         on-time ~ (di/dt)^-1/2 (A152's 36 A / d was a 1/d fit to it).
         A153 (registered, points never run): 75 / 125 pH at 24-40 A/ns
         within -0.1..+0.6 V of the x-curve, the 40 V side right on 4 / 4,
         start-up 152-155 A; the sqrt law beats A152's rule at 24 / 6 A/ns.
         PASS 5/5.
     69. The turn-off side above 150 pH (2026-10-07, mixed):
         [A154](../experiments/track_A_periodic_steady_state/A154_p24_turn_off_large_loops/RESULTS.md).
         A slow turn-off peaks near V_rail + 2 L di/dt_off: x_off <= ~10 V
         holds 40 V to 300 pH (200 x 48 A/ns 36.5 V, 300 x 32 37.7 V; the
         control 300 x 48 48.4 V). Its V-I overlap costs channel loss:
         10.1 / 14.2 / 22.6 / 31.1 W per module at 200 / 48, 250 / 40,
         300 / 32, 300 / 24 against ~2.7 W at 72 A/ns. 2/4 as registered:
         the misses are a band row on the safe side, two post-step swing
         peaks 0.1 us outside the oracle's K4 window, and the control's
         190 A start-up. **A loop above ~200 pH costs several percent by
         drive alone: the package should bound the loop to ~150 pH.**
     70. The start-up on-time as one formula (2026-10-07, mixed):
         [A155](../experiments/track_A_periodic_steady_state/A155_p24_startup_ton_law/RESULTS.md).
         A least-squares law over 27 package runs: Vo before the handover
         loses 0.0283 V per ns, 15.8 (d_on)^-1/2 ns, 6.0 ns per nH of loop,
         and gains 9.8 (d_off)^-1/2 ns from a slower turn-off (LOO 4.4 mV).
         Registered at 175-300 pH drives never run: Vo 1.010-1.023 V,
         start-up 151-152 A; without the L term 0.995 V and 162 A. PASS 4/4.
         **The drive spec is now formulas in (L, di/dt) (D68 Section 9).**
     71. The formula spec at its limit (2026-10-07, mixed):
         [A156](../experiments/track_A_periodic_steady_state/A156_p24_formula_spec_at_the_limit/RESULTS.md),
         [D69](../symbolic_derivations/03_P24_native/D69_P24_GATE_RESISTORS.md).
         125 pH x 24 A/ns (x_on 3.0 V) on A152's 13 rows and four modules:
         every switch <= 40 V (worst 39.5 V at L x 1.3). 4/5 as registered:
         late fires on -8 V / 10 us grow with the loop (0 / 6 / 16 at 50 /
         100 / 125 pH) and two clock-boundary duplicate records, without
         consequence; the adopted turn-on stays at x_on <= 1.8 V, the
         voltage limit is 3.0 V (checked) to 3.2 V. D69 (estimate from the
         datasheet's gate charge): turn-on 36 / 18 A/ns ~ 4.5 / 10 Ohm,
         turn-off 72 A/ns ~ 1.2 Ohm per device; no sink resistor gives
         ~160 A/ns, which alone limits the loop to ~60 pH.
     72. Loop damping is a spec item (2026-10-07, mixed):
         [A157](../experiments/track_A_periodic_steady_state/A157_p24_loop_damping/RESULTS.md).
         Every package run used ring Q 7. At S50 Q 15 / 30 change nothing
         (37.3 / 37.2 V, 0 late fires); undamped, at S50, S100 and 125 pH,
         the valley tracking is lost from start-up on (8600-8960 late
         fires on all phases, 58-69 V), as A144 found with instantaneous
         edges: the slow turn-on does not remove the ring after every
         edge. **Spec adds ring Q <= 30 (ideal parallel damper); the loop's real damping is a
         question for Mihai.**
     73. The damping boundary (2026-10-07, mixed):
         [A158](../experiments/track_A_periodic_steady_state/A158_p24_damping_boundary/RESULTS.md).
         Q 15 / 30 hold at 100 pH too (0 late fires, 36.7 / 36.9 V); Q 100
         and 300 lose the tracking at 50 and 100 pH (2400-7200 late
         fires). The boundary lies between Q 30 and 100 whatever L; the
         harness's ring residual does not predict it (300 pH at Q 7 holds
         with 7.5 V left). 0/2 as registered: both misses are the post-step
         swing peak 0.05 us after the oracle's K4 window (A154's case).
     74. The recommended loop bound is 125 pH, not 150 (2026-10-07, mixed):
         [A159](../experiments/track_A_periodic_steady_state/A159_p24_spec_at_150ph/RESULTS.md).
         At 150 pH with the adopted x_on 1.8 V (12 A/ns) every switch stays
         <= 38.0 V, but the slow turn-on costs regulation: load-step dip
         -16.1 mV (ideal -11.9), +4.8 V / 10 us back after 46.2 us, 33 late
         fires on -8 V / 10 us. 2/5 as registered (NEW flags are the oracle's
         K4-window timing again). By the registered rule the bound comes
         down to 125 pH (A156) - item 69's "~150 pH" is superseded. At large
         L the overshoot (di/dt <= x / L) and the transient response pull
         the turn-on rate in opposite directions.
     75. The oracle's K4 window (2026-10-07, analysis):
         [A160](../experiments/track_A_periodic_steady_state/A160_p24_oracle_k4_window/RESULTS.md).
         A 2 us window (instead of 1 us after a ramp) would clear the
         slow-turn-on swing peaks of A154 / A158 / A159 and hide nothing
         traced (25 events, all spikes below their run's post-step peak),
         but it also clears A151's single 9 A/ns "NEW" event, which the
         registration had wrongly listed as traced: it is the same swing
         peak. FAIL as registered, K4 stays 1 us; A151's "9 A/ns too slow"
         now rests on its Vo evidence alone (post hoc note).
     76. The turn-on window and the loop bound (2026-10-07, mixed):
         [A161](../experiments/track_A_periodic_steady_state/A161_p24_150ph_faster_turn_on/RESULTS.md).
         150 pH with a 20 A/ns turn-on (x_on 3.0 V): matrix and four
         modules <= 39.4 V, regulation back (dip -14.8 mV), 0 NEW, late 28.
         4/5 as registered. Voltage wants di/dt_on <= 3.0 V / L, regulation
         >= ~20 A/ns; the window closes near 150 pH: a candidate bound in the tested model (D70)
         (item 74's 125 pH is the margin value). Late fires follow L, not
         x_on, so item 71's adoption of x_on <= 1.8 V is superseded.
     77. The late fires located (2026-10-07, RTL cfg diagnostic):
         [A162](../experiments/track_A_periodic_steady_state/A162_p24_late_fire_timing/RESULTS.md).
         cfg late_log (bridge, off = unchanged; identity bit for bit) puts
         every late fire of -8 V / 10 us at 2-17 us after the ramp, on
         phases 2 and 4, none in steady state: a bounded settling
         transient that lasts longer with a larger loop. PASS 2/2; no
         consequence observed, the late edge's type not identified, and
         A161's criterion 3 stays failed.
     78. Efficiency when hot (2026-10-07, math):
         D62's budget on A124's p125_n0 waveforms (25 °C: 90.61 % again):
         88.1 % with the switches at 125 °C (R_on x 1.59, A90), 87.5 % with
         the inductor copper 100 K hotter too. First order: the waveforms
         are the 25 °C ones (A90: the module still works at 125 °C).
     79. The package model's boundary (2026-10-07, audit):
         [D70](../symbolic_derivations/03_P24_native/D70_P24_PACKAGE_MODEL_BOUNDARY.md).
         After an external review: a ledger of what the plant holds (loop
         L with an ideal parallel damper, linear-ramp edges, Coss, reverse
         conduction, ideal Cs / Co, modules joined at one ideal node), what
         only the budgets hold (lateral copper, vias, Cs ESR, R_on, inductor
         R/L) and what is missing (output-path R / L, Cs ESL, core loss,
         gate dynamics, thermal). The lateral copper's one-way estimate is
         invalid at 35 um (12 % drop) and holds for >= ~215 um; a path
         resistance changes four-module sharing by ~1 % only; Q 7 needs
         ~20-30 mOhm series at the ring frequency, Q 30 ~4-8 mOhm; no
         double counting. Package-inclusive efficiency 85-89 % (86-429 um).
         The loop bound, Q <= 30, efficiency and late-fire statements now
         carry their conditions. Next dynamic element: the per-module
         output path (R and L).
     80. The output path, decided without the plant (2026-10-07, math):
         [D71](../symbolic_derivations/03_P24_native/D71_P24_OUTPUT_PATH.md).
         Fig. 5's lateral Vo path is 63-628 pH per module (glass thickness
         missing). Module-against-module motion (93-294 kHz, Q 0.2-9) is
         driven only by current mismatch: <= ~1 mV. The common motion is
         an inductive drop at the load, L/4 x di/dt = 16-157 mV at 1 kA/us
         with the capacitors at the modules, faster than the loop. No plant
         change; two interface requirements: sense Vo at the common strip,
         and processor-side decoupling / load slew covering L/4 di/dt (a
         250 A step >= 0.4-4 us for 1 %). The co-simulated load-step Vo is
         at the modules' joined node, not at the processor.
     81. The inductor as a buildable array (2026-10-07, math):
         [D72](../symbolic_derivations/03_P24_native/D72_P24_INDUCTOR_ARRAY.md).
         D62's middle R/L (79 uOhm/nH, A124's 90.61 %) is the 500 nH HBS1
         unit's: ~170 units per phase (P24: 12). With units sized for the
         current (>= 5 A each, 29-40 per phase) and R/L following the unit
         size (power law through P24 Table 2's two HBS1 points), the design
         records give 2.5 MHz 86.6-87.7 %, 5 MHz 86.4-87.1 %, 1 MHz
         85.7-87.1 %: 2.5 MHz stays, by 0.2-0.6 points. Estimated
         efficiency ~87 %, package-inclusive ~81-86 %. Fit and core loss
         are open; heat is a requirement (39-58 W per 1 cm^2 module).
     82. An electrothermal closure in the team's framework form (2026-10-07,
         math): [D73](../symbolic_derivations/03_P24_native/D73_P24_ELECTROTHERMAL.md).
         The loop of Krishnakumar et al. 2026 (Fig. 4) and Choi et al. 2025
         (losses -> temperature -> losses, 85 C threshold) with one lumped
         node per module on D72's losses: at 85 C the 2.5 MHz converter is
         83.9-86.3 % (package-inclusive 78-84 %) if each module's path to a
         25 C coolant is <= 0.8-1.0 K cm^2/W (0.5-0.7 at 45 C; hottest
         module). Coupling raises the loss 8-25 % (the team: 13.5-15.8 %).
         The inductor array makes 28-44 % of the heat inside glass 2, away
         from the dies' spreader: its path binds. Stable (runaway above
         5 K cm^2/W); 2.5 MHz leads 5 MHz by 0-0.5 points hot. 125 C is now a
         bound, not the design point.
     83. The module stack as a 3D conduction model (2026-10-07, math):
         [D74](../symbolic_derivations/03_P24_native/D74_P24_THERMAL_STACK.md).
         Finite-volume solver verified against closed forms (slab, layered
         1D exact, Muzychka / Yovanovich flux channels to 0.07-0.2 %,
         resolved vias vs effective medium), convective cooling face under
         the GaN spreader, per-die electrothermal loop; revised with D75's
         copper and D76's core loss. The inductor layer is the hottest part
         in all 656 solves and glass 1 is the barrier: at h 2e4 W/(m2 K),
         25 C coolant, kappa 1, no via copper, inductor 96.6 C vs junction
         42.9 C, glass 1 takes 35 of the 72 K. About 2 % copper fill under
         the columns (~5,700 vias of 30 um per module) holds 85 C to a 45 C
         coolant at kappa 1; kappa 4 needs ~4 % and h >= 5e4. Conditions:
         vias land on copper on both glass faces, every ABF dielectric
         >= 1-2 % copper. The inductor then stays ~12 K above the junctions.
     84. The module footprint (2026-10-07, math):
         [D75](../symbolic_derivations/03_P24_native/D75_P24_MODULE_FOOTPRINT.md).
         20 EPC2067 (185 mm^2) do not fit a 10 x 10 mm site (P24's own 12:
         111 mm^2); a 250 W module takes two sites (10 x 20 mm), 1.25 A/mm^2.
         Lateral copper halves (86 um: 6.2 W), the one-way estimate holds
         from ~107 um, package-inclusive ~83-87 % before core loss.
     85. The inductor array's core loss (2026-10-07, math):
         [D76](../symbolic_derivations/03_P24_native/D76_P24_CORE_LOSS.md).
         HBS1's R_acx metric (P24's ref. [10]; curves digitised from Murali
         et al. ECTC 2022), loss kappa R_acx L I_ac^2, independent of the unit
         count: 7.5 / 15 / 30 W per module at kappa 1 / 2 / 4 (2.5 MHz design,
         measured 1.98 MHz). Converter 84.4-85.4 % to 78.4-79.3 % at 25 C;
         85 C with package 78.2-82.2 % to 73.1-76.6 %. Core loss grows as
         f^0.55: 5 MHz falls 1.4-4.5 points behind, 1 MHz ties 2.5 MHz within
         ~1 point; 2.5 MHz stays for valley margin and the frozen controller.
     86. A microchannel coolant model (2026-10-07, math):
         [D77](../symbolic_derivations/03_P24_native/D77_P24_COOLANT.md).
         Shah-London Nu / f Re, fin efficiency, the coolant in the linear
         system (upwind, GMRES). Copper channels give h_eff 3.8e4-2.6e5; the
         coolant's own rise then sets the flow: per module >= 0.44 g/s at a
         25 C inlet, 1.12 g/s at 45 C (kappa 1, 2 % fill); kappa 4 1.15 g/s at
         25 C, a 45 C inlet only with 19.6 % fill (2.3 g/s). The framework's
         1.6 g/s over four modules gives 88 C. Pumping < 0.5 W per package.
     87. The processor-side face (2026-10-07, math):
         [D78](../symbolic_derivations/03_P24_native/D78_P24_PROCESSOR_SIDE.md).
         Linked through the package substrate (1.2-12 K cm^2/W) to the
         processor's temperature (45-95 C): a second path when cooler than
         the IVR's top face, a source when warmer (up to ~33 W out / ~39 W in
         per module). At kappa 1 with h >= 2e4 it does not bind (85 C holds
         to a processor side of 85-95 C); at kappa 4 with a 45 C coolant it
         decides (processor side <= 55-83 C needed).
     88. The gate drive at gate level (2026-10-07/08, mixed):
         [D79](../symbolic_derivations/03_P24_native/D79_P24_GATE_DRIVE.md),
         [A163](../experiments/track_A_periodic_steady_state/A163_p24_gate_driven_edges/RESULTS.md).
         EPC's EPC2067 model (outside the repository) drives the plant's
         high-side edges. It matches the datasheet and LTspice; off, the
         plant is unchanged bit for bit. A163 (2.5 / 0.3 ohm, 29 runs) is a
         FAIL as registered:
         - nominal devices hold (<= 36.4 V, edge power 2.4 W per module);
         - the spread breaks the frozen controller three ways: the
           open-loop start-up on-time; the valley-timing limit (gate delay
           <= ~5.5 ns on phase 4, because dt_pred >= 0); the driver at
           -30 % (40.6 V);
         - D79's +1.5 V / C_ISS x 1.5 corners are outside the datasheet
           (now +1.0 V / Q_G x 1.29);
         - the ramp model's peaks (A145-A162) were command-time currents;
           the physical peaks are 5-8 A higher.
     89. The drive spec over the spread (2026-10-08, mixed):
         [A164](../experiments/track_A_periodic_steady_state/A164_p24_gate_drive_spread/RESULTS.md).
         Spec tested: 3.0 / 0.3 ohm with +-20 %, an 8 ns high-side turn-on
         lead (bridge driver option, off = unchanged) and a per-board
         start-up trim (Vo 1.035 V at the handover). FAIL as registered,
         but 10 of 17 rows and four modules pass:
         - peaks and V_DS hold at every corner (fast 38.5 V);
         - the lead is needed even at nominal;
         - misses: L x 0.7's handover (218.6 A, a lead-made on-time step),
           the slow corner's late fires after the handover and rising
           steps, ff -8 V Vo +0.6 mV;
         - +-30 % has no single-resistor window (pre runs);
         - a fixed lead removes the dt_pred >= 0 interlock: shoot-throughs
           in pre runs when dt_pred collapsed.
     90. The form of the lead (2026-10-08, mixed):
         [A165](../experiments/track_A_periodic_steady_state/A165_p24_gate_lead_pulse/RESULTS.md),
         [A166](../experiments/track_A_periodic_steady_state/A166_p24_gate_lead_per_board/RESULTS.md),
         [A167](../experiments/track_A_periodic_steady_state/A167_p24_gate_lead_ramp/RESULTS.md).
         - A165 moves the whole pulse (a signed dt_pred, emulated in the
           bridge): handovers are lower everywhere, but L x 0.7 reaches
           211 A after +4.8 V, because the RTL's phase-1 timeline does not
           move. Not adopted.
         - A166 uses an interlock-safe lead per board (shortest delay - 1
           ns): 0 shoot-throughs, but 19-85 late fires after rising steps
           and 208 A at L x 0.7. Not adopted.
         - A167 ramps A164's 8 ns lead in over 20 us after the handover:
           L x 0.7 handover 191.5 A, post-step as A164 (195 A). ADOPTED.
         Spec: 50 pH, 3.0 / 0.3 ohm +-20 %, the 8 ns ramped lead,
         per-board start-up trim.
         Open:
         - the slow corner's transient late fires (no peak or V_DS
           consequence);
         - the L x 0.7 open-loop start at 202 A;
         - an interlock by construction needs a controller-side lead that
           follows each edge's V_DS (RTL change).
     91. Loop bound, gate-driven low sides, driver interlock (2026-10-08,
         mixed): [A168](../experiments/track_A_periodic_steady_state/A168_p24_gate_loop_bound/RESULTS.md)-[A172](../experiments/track_A_periodic_steady_state/A172_p24_final_gate_plant/RESULTS.md),
         D79 Section 6.
         - A168: the loop bound is 50 pH. 60 pH at 3.0 ohm gives the fast
           corner 40.3 V; at 3.5 ohm the slow corner and L x 0.7 lose a few
           amperes. 75 pH at 4.0 ohm loses line-step Vo (12.6 mV, 46 us) and
           the slow corner's timing.
         - A169: with gate-driven low sides (turn-off <= 2.9 ns + 1.8 ns),
           A167's drive shoots through where dt_pred collapses (L x 0.7,
           slow corner). A lead bound cannot fix it.
         - A170: an interlock that holds the gate at 0 V until the
           complement stops removes the shoot-throughs but serialises the
           delays (L x 0.7 214 A, slow corner 4906 late fires). Not adopted.
         - A171 / A172: an interlock that lets the gate charge and holds
           only a channel about to start against a conducting complement
           (threshold form, 0.5 ns) passes every row. Four modules: 184.2 A,
           0 late. L x 0.7 re-trimmed: 199.7 A after the step (0.3 A
           margin).
         Spec: item 90's plus gate-driven low sides (sink <= 0.3 ohm) and a
         threshold-form driver interlock; loop <= 50 pH. The RTL stays
         frozen; item 90's interlock item is closed.
         Open: the L x 0.7 open-loop start (200-202 A) and its 0.3 A
         post-step margin; the slow corner's late fires (194, no
         consequence).
     92. External review of D70-D79 / A163-A172, and the final plant's
         coverage (2026-10-09, mixed): D80, A173-A178,
         [reports/FINAL_SPEC_COVERAGE.md](FINAL_SPEC_COVERAGE.md).
         - The review found item 91's "passes every row" true only for
           +4.8 V / 1 us: the other rows and four-module cases had run on
           V2 (ideal low sides, no interlock). It also found the interlock
           reported as solved although it is an idealised function, and a
           0.3 A margin reported as a pass. A172 RESULTS Section 3 and D79
           Section 6 now say so.
         - A173 (17 rows on the final plant): 13 pass, no row above 200 A
           or 34.1 V. Misses: the slow corner's Vo dips 3-5 mV deeper than
           V2 after line ramps; ff -8 V one spike; four modules ss 8 NEW
           spikes (4 = A160's K4 artefact). Four modules with C14's ±5 %
           inductor spread: 196.5 A.
         - A174: L x 0.7 over five step phases 199.5-201.5 A, so it
           exceeds 200 A at one phase. A fixed 1.0 V interlock reference
           (8.3 ns at ss) holds peaks but adds 26-90 % late fires at the
           slow corner (four modules ×2, NEW 8 -> 82).
         - A177: a per-board reference (1.4 ns) comes close to 0.5 ns (four
           modules late 792 vs 803) but passes 2 of 5 slow-corner rows as
           registered. No delay 0.5-8.3 ns changed a peak or V_DS; the
           release time is a timing spec, < 1.4 ns wanted at the slow corner
           (A179 refines it to <= 1.0 ns, item 93).
         - A178: L x 0.75 / 0.8 <= 198.3 / 194.7 A at five step phases;
           the inductor tolerance for 200 A is -25 % (L x 0.7 201.5 A;
           nominal devices, tested points - see FINAL_SPEC Section 5).
         - A175: at nominal devices the final plant has run A152's whole
           13-row matrix; 12 pass, -4.8 V / 1 us restarts (oracle events).
         - A176: the variants support the lead and the gate-driven low
           sides together as the cause of those falling-step restarts
           (A169's mechanism without a shoot-through; one step position
           per variant). A valley-aware lead would remove them (RTL).
         - D80: the thermal model with the final plant's edge losses and the
           50 pH loop. The published thermal numbers are conservative (T_max
           -0.7..-1.3 K). The edges add 1.7 W (nominal) to 3.9 W (ss) per
           module: about -0.5 / -1.0..-1.2 points of efficiency (corrected
           2026-10-09: first written as 0.7 / 1.6 points, which are the
           losses as % of the output).
         Spec unchanged; its statement now carries the coverage table and
         these limits.
     93. Interlock release time and the paper map (2026-10-09 afternoon,
         mixed):
         - A179 (slow corner, three step positions per delay, step at
           500 us - exact against A173 / A177 before the step): after the
           -8 V ramp the late fires stay <= 32 up to 1.0 ns and reach 51 /
           47 at 1.4 ns at 2 of 4 positions -> release <= 1.0 ns. Four
           modules pass at 1.4 ns (A177's NEW miss was position scatter).
           The load step's one-period spike count scatters 7-27 at
           >= 1.0 ns without a trend: open. FAIL as registered, accepted
           with 3 documented exceptions (accepted = documented, not
           passed).
         - reports/PAPER_REPRODUCTION_MAP.md: P24 / P25 item by item. P24:
           5 of 10 checkable items agree, 2 differ at this design point,
           3 do not hold as printed (1-2 % for ZVS, frequency free of
           switching loss, Table I L_crit). P25: ZVS and the single sensor
           are consistent with its own point (A67; D41 near-closed, strict
           return only at 4 mOhm; A69); duty typo and an
           inductance / peak inconsistency; hardware not reproduced.
     94. Math-model acceptance after an external review (2026-10-09
         evening, math; D81):
         - Floquet moduli of D45-D51 came from Newton's chord matrix.
           Recomputed at all 36 orbits (fresh central differences, five
           steps, event order checked): changes <= 8.1e-4, every orbit
           inside the unit circle (worst 0.9959). Steps of 1e-6 / 1e-7
           carry up to 4e-3 of integrator noise; 1e-3..1e-5 agree to
           4e-5. Solver, D45 / D46 scripts and the D47-D51 gate use
           section_jacobian now.
         - D63 says when it leaves its range: record flags (ith_rail,
           past_level, von_grid, sh_grid), inf for unreachable levels,
           R = 0 limit, steady_ton acceptance, steady_check after the
           warm-up. Archived outputs reproduced except 4 + 2 rows that
           had diverged (the old code's negative periods); thresholds
           below 8 V move peaks <= 0.56 A, no outcome class changes;
           D63's "<= 4.7 A" crossing is <= 5.5 A.
         - D60 scope note (A142 / A143 counterexamples), D71 reworded,
           evidence-class table (D81 Section 4).

        **Next at this level, one at a time** (superseded by item 26; kept as the record) (after the code clean-up
        agreed on 2026-10-01: one shared adopted version per component,
        bit-identical gates, the fast plant):
        - the adoption decision for A100: the priorities and phase 1's ZVS
          limit in TRADEOFF_SCORECARD Section 6, then the standard matrix
          (m ≠ 0, line steps);
        - the voltage loop: done for the comparator design (A104); with the timed turn-off (dlo) not yet;
        - a filtered (PLL-type) or predicted slot timebase (Huber et al.
          2009; Zhou et al. 2025) for the remaining phases 2-4 on-time
          share;
        - Coss spread;
        - gate-drive loss and gate dynamics (driver ramp);
        - the 2% target in the Verilog co-simulation (done: soft, see item 21);
        - load and line steps.
     3. RTL:
        - a predictive phase-1 turn-off, to remove the 4 ns jitter;
        - start-up: the sequence is done (A103); a regulated mode S for a light boot load is open.

     After that, the four-phase mathematical model with the valley
     trigger.
   - **Open.** Track B's LTspice ramp-only run (R04E16) ended at ~55% of
     the ladder level. It has no diodes, so this defect does not explain it.
4. **Device realism (physical model).** Repeat A69 with nonlinear GS61008T
   Coss (datasheet) and, if a public vendor model exists, with it. The
   question is whether ZVS margin and stability survive.

The synthetic F/H/s fixture stays a regression fixture only. Its failures
are scale effects (A67/A68), so it is not a candidate operating point. Fixed design-peak references are an explicit
project policy; measured-peak feedback still needs its own observer contract.
Finite-grid event scans are not certified interval root coverage.
P24 transfer remains a separately declared topology/sequence branch.

## 中文汇报提纲（2026-10-07，P24 主线）

1. **问题和结论：** P24 的拓扑、时序和器件假设能否同时成立？不能原样成立：用它自己的参数，1–2 % 负电流给不了高侧 ZVS
   （约需 27 %）。设计改用 12.5 % 负电流、高侧部分软开通，用“谷底裕量”解释为什么停在这里。
2. **做出的东西（仿真层面）：** Verilog 控制器接电路模型的联合仿真，四模块 1 kW 从零启动到闭环稳压；2.5 MHz 设计估算效率约
   87 %（损耗模型，25 °C，按可实现的电感单元阵列，不含磁芯损耗；按 HBS1 自己的 R_acx 指标加上磁芯损耗是 78–85 %，D76；
   按 P24 最大单元的 R/L 是 90.6 %，但那要每相约 170 个单元，D72）；单模块和四模块控制器经随机测试后冻结；数学模型（D63、D68）与联合仿真互相检验。
3. **一个有价值的发现链：** 异常检测器找到线电压阶跃后的 ZVS 丢失 → 控制修不了（串联电容的电荷平衡）→ 单独放慢开通解决 →
   从节点电荷推出“过冲只取决于 L × 开通 di/dt”，在没跑过的点上事前预测并验证。
4. **封装层的结论要带条件讲：** 在所测模型（理想并联阻尼 Q 7、25 °C、标称 Cs、线性边沿）里，开通 di/dt 的窗口
   （约 20 A/ns 到 3.0 V / L）在 150 pH 附近闭合，最坏角落离 40 V 只有 0.6 V：这是布局的候选上限，不是硬件极限。阻尼
   Q ≤ 30 是理想阻尼器下的结果，物理来源未定。横向铜只在损耗预算里；20 片芯片放不进 10×10 mm，一个模块占 P24 的两个位置
   （D75），横向铜损减半，含封装的估算效率约 83–87 %（不含磁芯损耗），含磁芯损耗约 75–85 %。
   磁芯损耗（D76，HBS1 的 R_acx 指标，大信号系数 κ 1–4）每模块 7.5–30 W，让 2.5 MHz 在效率上不再领先 1 MHz，5 MHz 落后
   1.4–4.5 个点；2.5 MHz 仍保留（谷底裕量、控制器已冻结）。高温 85 °C 含封装约 73–82 %。
   热（D74，三维导热、解析解验证）：电感层就是最热处，玻璃 1 是瓶颈（κ 1、h 2×10⁴、不加铜时电感比结温高约 54 K）；
   玻璃 1 里约 2 % 的铜过孔（每模块约 5,700 个 30 µm 孔，落在铜层上、ABF 有 1–2 % 微孔）能解决，κ 4 要约 4 %。
   冷却液（D77，微通道）：h 不再是限制，冷却液温升才是；每模块 ≥ 0.44 g/s（25 °C 进口）/ 1.1 g/s（45 °C），泵功不到 0.5 W。
   处理器面（D78）：比 IVR 顶面冷时是第二条散热路径，热时是热源；κ 1 时不构成限制，κ 4 加 45 °C 冷却液时要求处理器侧 ≤ 55–83 °C。
5. **边界和缺口：** 没有硬件；封装数值（回路 L、阻尼、铜厚、电感工艺）P24 没给，用扫描和公式覆盖，真实值是要问 Mihai 的
   问题；动态模型里还没有模块输出路径的 R / L（D70 的清单）；磁芯损耗只有基于 R_acx 指标的估算（κ 未实测）；热场有 D74 / D77 /
   D78 的稳态模型（叠层尺寸都是假设值），没有瞬态。
