# Current Work Status

Updated: **2026-09-29**. This is the current navigation summary; dated reports
remain historical snapshots. No experiment parameters were changed for this
repository presentation update.

## 1. Mathematical core — native P25, three phases / one module

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

## 2. Engineering experiments — separate four-phase track

These cases investigate periodic states and device/timing trade-offs. Their
boundaries differ from the strict native P25 core and from one another.

| Reading group | Question | Starting point |
|---|---|---|
| A49–A52 | Can a coupled periodic state be solved and cross-checked? | [A52](../experiments/track_A_periodic_steady_state/A52_spice_crosscheck_reduced_load_zvs/RESULTS.md) |
| A53–A56 | How do inductance, actual switch currents and equal delivered power change the comparison? | [A56](../experiments/track_A_periodic_steady_state/A56_equal_power_regulated_loss_comparison/RESULTS.md) |
| A57–A59 | What changes with reverse conduction, separate dead times and nonlinear capacitance? | [A59](../experiments/track_A_periodic_steady_state/A59_nonlinear_coss_epc2067/RESULTS.md) |
| A60–A63 | How conditional is the result on temperature, winding loss, load and flying capacitance? | [A60](../experiments/track_A_periodic_steady_state/A60_temperature_ron_sensitivity/RESULTS.md), [A61](../experiments/track_A_periodic_steady_state/A61_inductor_loss_break_even/RESULTS.md), [A62](../experiments/track_A_periodic_steady_state/A62_load_sweep_fixed_deadtime/RESULTS.md), [A63](../experiments/track_A_periodic_steady_state/A63_flying_capacitor_sensitivity/RESULTS.md) |

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

On 2026-09-29, **505 portable checks** and **524 full local checks** passed.
The extra local checks use generated LTspice logs; all are software/model
regressions, not independent physical experiments.

Three-phase event orchestration and a conditional return-check interface are
implemented. The next mathematical question is admissible full-cycle
reachability under a frozen parameter/control contract, before solving
periodic closure. Candidates must first satisfy D33's negative-current return
direction, as well as the existing voltage/current entry constraints.
D29 does not justify endlessly tuning a synthetic fixture
or treating it as paper hardware. Fixed design-peak references are an explicit
project policy; measured-peak feedback still needs its own observer contract.
Finite-grid event scans are not certified interval root coverage.
P24 transfer remains a separately declared topology/sequence branch.

## 中文汇报提纲

1. **先讲拆分方法：**纵向分成来源、方程、事件控制、器件、实验和验证；横向按一相的物理事件拆周期。
2. **再讲做出的东西：**共享节点模型、可复用控制与事件模块、15模态代数组装、独立SPICE交叉验证，以及器件/损耗敏感性实验。
3. **讲一个有价值的失败：**局部SH2换流还没完成，另一相电流已先过零；用同一条轨迹的伏秒与电荷积分解释，而不是任意改初始电流。
4. **最后讲边界和缺口：**P25三相数学模型与P24四相实验分开；完整事件周期和零启动衔接尚未验证，不能说已经完整复现论文。
