# Current Work Status

Updated: **2026-09-29**. This is the current navigation summary; dated reports
remain historical snapshots. No experiment parameters were changed for this
repository presentation update.

The project runs two models in parallel on purpose, each checking the other:
the **mathematical model** (native P25 event model, Section 1) and the
**physical model** (Track A circuit simulations, Section 2). Since
2026-09-29 both are maintained by one session. The mathematical-model
session's work was committed unchanged as the baseline (`0f50511`).

## 1. Mathematical model — native P25, three phases / one module

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

[Track B](../experiments/track_B_zero_start_extension/README.md) and the
[startup model audit](../results/ZERO_START_BOUNDARY_AND_MATH_MODEL_AUDIT.md)
record startup assumptions and mathematical construction. Fixed-PWM
startup/convergence studies do not demonstrate a paper-consistent handoff to
event-controlled ZVS. A prescribed periodic-state voltage ladder must never
be reported as self-established startup balance.

## Verification and next step

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
           minimum slew is not a spec. Falling -4.8 V at nominal L / Cs:
           173.5 A at 1 us, 192.2 A at 2.3 us, 172.2 A at 5.1 us (A130
           tested 1 and 5 us); rising at L x 0.7: +4.8 V 185.2 / 188.6 /
           205.9 A at 1 / 5 / 20 us; nominal +8 V 197-209 A at every slew.
           A139's certified table (95 % bound) is the spec under tolerance.
           A138's own bands failed (GP noise collapse, budget to one
           direction); A139 measured the scatter (heavy-tailed: one step
           position in six adds +14 A) and passed 3/3.
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

## 中文汇报提纲

1. **先讲拆分方法：**纵向分成来源、方程、事件控制、器件、实验和验证；横向按一相的物理事件拆周期。
2. **再讲做出的东西：**共享节点模型、可复用控制与事件模块、15模态代数组装、独立SPICE交叉验证，以及器件/损耗敏感性实验。
3. **讲一个有价值的失败：**局部SH2换流还没完成，另一相电流已先过零；用同一条轨迹的伏秒与电荷积分解释，而不是任意改初始电流。
4. **最后讲边界和缺口：**P25三相数学模型与P24四相实验分开。P25量级下的周期解已经闭合（D41），加阻尼后稳定（D42），并经独立电路仿真验证（A69）；但它仍是开环、理想器件的结果，零启动衔接和闭环调节尚未验证，不能说已经完整复现论文。
