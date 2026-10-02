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

        **Next at this level, one at a time** (after the code clean-up
        agreed on 2026-10-01: one shared adopted version per component,
        bit-identical gates, the fast plant):
        - the adoption decision for A100: the priorities and phase 1's ZVS
          limit in TRADEOFF_SCORECARD Section 6, then the standard matrix
          (m ≠ 0, line steps);
        - the voltage loop, designed together with dlo (scorecard T6);
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
