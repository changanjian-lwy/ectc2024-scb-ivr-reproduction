# Current Work Status

Updated: **2026-09-28**. This is the current navigation summary; dated reports
remain historical snapshots. No experiment parameters were changed for this
repository presentation update.

## 1. Mathematical core — native P25, three phases / one module

**Purpose:** define a coupled switching model before claiming a periodic
solution. No P24 fourth phase or module coupling is implicit.

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

**Still open:** extend first-handoff event orchestration to all three handoffs,
then solve and validate the complete periodic map. Fifteen independently
tested modes are not yet a connected physical cycle.

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

On 2026-09-28, **416 portable checks** and **435 full local checks** passed.
The extra local checks use generated LTspice logs; all are software/model
regressions, not independent physical experiments.

The mathematical next step is complete three-phase event orchestration,
followed by a state-and-controller periodic return check. It is not to adjust
a failed local fixture until the desired waveform appears. P24 transfer
remains a separately declared topology/sequence branch.

## 中文汇报提纲

1. **先讲拆分方法：**纵向分成来源、方程、事件控制、器件、实验和验证；横向按一相的物理事件拆周期。
2. **再讲做出的东西：**共享节点模型、可复用控制与事件模块、15模态代数组装、独立SPICE交叉验证，以及器件/损耗敏感性实验。
3. **讲一个有价值的失败：**局部SH2换流还没完成，另一相电流已先过零；用同一条轨迹的伏秒与电荷积分解释，而不是任意改初始电流。
4. **最后讲边界和缺口：**P25三相数学模型与P24四相实验分开；完整事件周期和零启动衔接尚未验证，不能说已经完整复现论文。
