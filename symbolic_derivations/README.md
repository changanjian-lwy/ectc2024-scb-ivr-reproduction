# Symbolic and Event-Driven Analysis

This directory keeps the equation-first analysis separate from LTspice
experiments. It contains three evidence branches; none may silently borrow a
rule from another branch.

## Reading order

First isolated definition module:
[`D01_TIMING_DEFINITION_CONTRACT.md`](D01_TIMING_DEFINITION_CONTRACT.md)
— typed command/gate/nominal/event timing, 9 synthetic unit tests passed.
Not yet connected to the solver; paper-label adapters remain to be audited.

P25 native physical-event specification:
[`02_P25_native/D02_PHYSICAL_EVENT_CONTRACT.md`](02_P25_native/D02_PHYSICAL_EVENT_CONTRACT.md)
— first three-phase handoff, source-checked gate states, unresolved printed
time-label conflicts, 16 synthetic tests. No four-phase extension or new circuit run.

P25 shared-node derivation:
[`02_P25_native/D03_SHARED_NODE_EQUATIONS.md`](02_P25_native/D03_SHARED_NODE_EQUATIONS.md)
— full capacitor network, M2/M5 Schur reductions, dynamic output port,
power identity and no-impulse state continuity. Constant-capacitance/ideal-gate
derivation only; reverse clamp and event integration remain unimplemented.

P25 state-based guard interfaces:
[`02_P25_native/D04_STATE_EVENT_GUARDS.md`](02_P25_native/D04_STATE_EVENT_GUARDS.md)
— separate brackets from located roots, recheck Vds at gate request, report
negative-current overshoot, and keep absent reverse thresholds unresolved.

P25 reverse-channel mathematical branches:
[`02_P25_native/D05_REVERSE_COMPLEMENTARITY.md`](02_P25_native/D05_REVERSE_COMPLEMENTARITY.md)
— declared ideal/constant-drop complementarity, all-phase current-sign domains,
local active-set checks and explicit degeneracy. Not a measured GaN model or
an integrated hybrid-cycle solver.

P25 ideal control memory:
[`02_P25_native/D06_IDEAL_CONTROL_MEMORY.md`](02_P25_native/D06_IDEAL_CONTROL_MEMORY.md)
— three-phase event ring, explicit common Ton, causal peak references and
latched negative targets; electrical-state identity resets. Control tests only,
not an integrated electrical trajectory or a zero-start solution.

P25 root location and event ordering:
[`02_P25_native/D07_ROOTS_AND_SIMULTANEOUS_EVENTS.md`](02_P25_native/D07_ROOTS_AND_SIMULTANEOUS_EVENTS.md)
— double-tolerance bracket refinement, conservative uncertain-time ordering,
and one explicit ideal zero-drop gate/reverse-boundary batch. General coincident
events and start-on-zero arming remain separate unresolved assembly tasks.

P25 event coverage and full-state section:
[`02_P25_native/D08_WATCHES_AND_PERIODIC_SECTION.md`](02_P25_native/D08_WATCHES_AND_PERIODIC_SECTION.md)
— explicit watch coverage and capacitor/current/control-memory return with
unit-scaled residuals. Endpoint return is not a periodic-orbit certificate;
external forcing and continuous-path validity must still be established.

P25 paper-versus-topology equation audit:
[`02_P25_native/D09_PAPER_MODE_EQUATION_AUDIT.md`](02_P25_native/D09_PAPER_MODE_EQUATION_AUDIT.md)
— matched-boundary M1–M6 comparison; capacitor reduction assumptions and
printed equation discrepancies are separate from implementation errors. No new circuit run.

P25 constant-port local state propagation:
[`02_P25_native/D10_LOCAL_AFFINE_FLOW.md`](02_P25_native/D10_LOCAL_AFFINE_FLOW.md)
— full-network matrix-exponential continuation and conditional all-phase
commutation screening. Root-at-entry and sampled root completeness remain
explicit limitations; no gate actions or paper operating-point claim.

P25 three-phase single-module entry direction:
[`02_P25_native/D11_SINGLE_MODULE_ENTRY_DIRECTION.md`](02_P25_native/D11_SINGLE_MODULE_ENTRY_DIRECTION.md)
— analytic first-derivative classification for exact-zero reverse gaps;
conditional D10 scan connection without epsilon steps or electrical resets.
Not a four-phase controller, clamp solver or complete handoff certificate.

P25 connected first handoff:
[`02_P25_native/D12_CONNECTED_FIRST_HANDOFF.md`](02_P25_native/D12_CONNECTED_FIRST_HANDOFF.md)
— synthetic continuous M1-to-M4-entry trajectory, joint low-side zero event,
pre/post complementarity and causal peak blocking. Conditional sampled coverage,
not a paper operating point, complete cycle or four-phase extension.

P25 negative target and next-high admission:
[`02_P25_native/D13_NEGATIVE_TARGET_AND_HIGH_HANDOFF.md`](02_P25_native/D13_NEGATIVE_TARGET_AND_HIGH_HANDOFF.md)
— continuous D12 fixture reaches M5 but hits iL3=0 before SH2 admission;
independent positive M6 test is not substituted for that failed chain.
Fixed exact ON-constraint derivative identities without projecting state.

P25 freewheel margin and seed scope:
[`02_P25_native/D14_FREEWHEEL_MARGIN_AND_SEED_SCOPE.md`](02_P25_native/D14_FREEWHEEL_MARGIN_AND_SEED_SCOPE.md)
— integrated full-state volt-second/charge accounting of the unchanged failed
fixture; endpoint margin is not first-event or full-period feasibility proof.

P25 all-three-phase mode assembly:
[`02_P25_native/D15_THREE_PHASE_MODE_ASSEMBLY.md`](02_P25_native/D15_THREE_PHASE_MODE_ASSEMBLY.md)
— M1–M15 gate/event mapping and fixed-topology continuous derivatives;
individual mode tests are not a connected cycle. First-handoff scheduler
restrictions remain explicit until event assembly is extended.

Current definition audit (2026-09-27):
[`MATHEMATICAL_DEFINITION_AUDIT_2026-09-27.md`](MATHEMATICAL_DEFINITION_AUDIT_2026-09-27.md)
distinguishes command/gate/clamp timing, threshold versus observed negative
current, dimensionally consistent periodic residuals, rank of `I-M` versus
`M`, and conditional energy bounds. It records unresolved implementation
gates; historical solver passes are not automatically passes of this stricter
contract. No new simulation or controller change accompanies that audit.

1. [`00_Common_Symbols_and_Boundaries.md`](00_Common_Symbols_and_Boundaries.md)
   — shared notation and non-negotiable boundaries.
2. [`01_P24_native/DERIVATION.md`](01_P24_native/DERIVATION.md) — 2024-native
   topology and explicitly reported operations only.
3. [`02_P25_native/DERIVATION.md`](02_P25_native/DERIVATION.md) — native
   three-phase, six-mode calibration.
4. [`02_P25_native/30_P25_NATIVE_METHOD_CALIBRATION.md`](02_P25_native/30_P25_NATIVE_METHOD_CALIBRATION.md)
   — fixed-slot, event-timed and periodic-shooting comparisons.
5. [`02_P25_native/31_P25_INDUCTANCE_OPERATING_POINT_CLOSURE.md`](02_P25_native/31_P25_INDUCTANCE_OPERATING_POINT_CLOSURE.md)
   — independent 22 nH / 500 ns / peak-current consistency audit.
6. [`02_P25_native/32_STRICT_JOINT_OPTIMIZATION.md`](02_P25_native/32_STRICT_JOINT_OPTIMIZATION.md)
   — hard-gated joint feasibility analysis.
7. [`03_P24_primary_P25_supplement/DERIVATION.md`](03_P24_primary_P25_supplement/DERIVATION.md)
   — P24 four-phase topology with each P25-derived supplement labelled.
8. `03_P24_primary_P25_supplement/01_...md` through `29_...md` — the detailed
   derivation and numerical-audit sequence in chronological order.

## Branch boundaries

Latest local continuation:
[D16 — three-phase commutation guards](02_P25_native/D16_THREE_PHASE_COMMUTATION_GUARDS.md)
extends sampled event detection to M2/M5/M7/M10/M12/M15. This is guard
coverage, not an assembled periodic trajectory.
[D17 — three-phase handoff execution](02_P25_native/D17_THREE_PHASE_HANDOFF_EXECUTION.md)
then extends low admission, next-current zero, negative-target and high
admission to all three handoffs. High-on interval orchestration and complete
cycle closure remain open.
[D18 — high-on competing events](02_P25_native/D18_HIGH_ON_COMPETING_EVENTS.md)
adds the original on-time endpoint with competing reverse/current guards.
[D19 — single-period attempt](02_P25_native/D19_SINGLE_PERIOD_ATTEMPT.md)
assembles all stages with continuous state transfer and first-failure records.
The old synthetic seed still stops in M5; no periodic solution is implied.
[D20 — fixed-boundary shooting contract](02_P25_native/D20_FIXED_BOUNDARY_SHOOTING_CONTRACT.md)
defines six electrical seed coordinates and freezes devices, timing, ports and
design-peak references. Measured-peak control still requires an observer.
[D21 — seed feasibility versus state return](02_P25_native/D21_SEED_FEASIBILITY_VS_RETURN.md)
keeps blocked trajectories separate from defined periodic residuals. Three
synthetic i3-entry perturbations remain blocked in M5; no global claim follows.
[D22 — all-low current-order bound](02_P25_native/D22_ALL_LOW_CURRENT_ORDER_BOUND.md)
derives a necessary common-volt-second inequality without assuming constant Vo.
The old third-phase margin is 3 V·s at the negative target, not a ZVS guarantee.
[D23 — commutation charge deficit](02_P25_native/D23_COMMUTATION_CHARGE_DEFICIT.md)
accounts for the same M5 failure with the full affine network: only about 5.2%
of its required normalized commutation charge is supplied before i3 crosses zero.
Synthetic units only; not device Qoss or a paper operating point.
[D24 — phase-specific closed forms](02_P25_native/D24_PHASE_SPECIFIC_COMMUTATION_FORMULAS.md)
derives three distinct capacitor-network transfer expressions and checks them
against the unchanged full KKT network, including asymmetric banks.
[D25 — forced commutation ODE](02_P25_native/D25_FORCED_COMMUTATION_ODE.md)
keeps dynamic Vo and winding R, distinguishing target-voltage capacitance
normalization from switch-node capacitance and isolated-LC approximations.
[D26 — five-state coupled commutation](02_P25_native/D26_FIVE_STATE_COMMUTATION_MODEL.md)
independently propagates target Vds, all currents and dynamic Vo. It agrees
with the full local flow but cannot yet replace all-node reverse-guard checks.
[D27 — full-node reconstruction](02_P25_native/D27_FULL_NODE_RECONSTRUCTION.md)
recovers all node and switch voltages from the reduced trajectory; the main
event scanner remains unchanged.
[D28 — accepted-trace integral ledger](02_P25_native/D28_ACCEPTED_TRACE_INTEGRAL_LEDGER.md)
checks all accepted segments' output charge, inductor flux and capacitor
charge changes without treating failed trial endpoints as accepted states.
[D29 — frozen seed neighborhood](02_P25_native/D29_FROZEN_SEED_NEIGHBORHOOD.md)
records a 13-point synthetic one-coordinate audit at two grid resolutions:
all remain blocked at the same M5/i3 boundary, with no global infeasibility claim.

| Branch | Topology and timing source | Limitation |
|---|---|---|
| `01_P24_native` | P24 native structure and stated operations | Unreported states remain unknown |
| `02_P25_native` | P25 native three-phase structure and six modes | Never presented as a P24 result |
| `03_P24_primary_P25_supplement` | P24 four-phase structure; missing details explicitly supplemented from P25 | Four-phase extension is an assumption under test |

The analysis does not pre-impose 36/24/12 V as a zero-start result, alter a
paper rule to force closure, or treat a local ZVS event as a full-period proof.
`nP` and `nM` remain explicit, and single-module equations are not presented as
multi-module validation.

Raw optimizer traces are intentionally ignored by Git. The concise Markdown
reports, model source and acceptance tests are tracked and are sufficient to
audit or regenerate the reported calculations.
# Latest mathematical necessity check

[D38: ZVS admission versus next-phase rise](02_P25_native/D38_A2_OFFSET_ZVS_VS_RISE.md)
derives a new a2 seed without changing devices/control; a continuous first
high-side handoff passes but the next rising-current mode does not.

[D37: same-path negative-target budget](02_P25_native/D37_SAME_PATH_NEGATIVE_TARGET_AND_COMMUTATION.md)
separates failure before the negative target from failure during high-side
commutation, and rejects a bound whose output-voltage premise no longer holds.

[D36: two-voltage initial-state grid](02_P25_native/D36_TWO_VOLTAGE_SEED_GRID.md)
finds local M2 passage under the same devices/control; the later M4/M5 failures
remain explicit and no complete-cycle success is reported.

[D35: low-side commutation charge](02_P25_native/D35_DOWN_COMMUTATION_CHARGE_ACCOUNTING.md)
explains D34's two M2 diagnostic trajectories using full-network charge accounting,
without accepting the failed interval or changing a parameter.

[D34: negative-return seed diagnostic](02_P25_native/D34_NEGATIVE_RETURN_SEED_DIAGNOSTIC.md)
keeps devices/control frozen and records M1/M2 obstacles, distinguishing
search-horizon exhaustion from observed competing events.

[D33: periodic-section direction correction](02_P25_native/D33_PERIODIC_SECTION_DIRECTION_AUDIT.md)
identifies why the old positive-i1 diagnostic seed cannot itself be a periodic
fixed point of the declared M15→M1 event sequence.

[D32: accepted-trace energy ledger](02_P25_native/D32_ACCEPTED_TRACE_ENERGY_LEDGER.md)
audits source/load/storage/winding energy and explicit ON-residual work;
failed intervals are excluded and no periodicity claim is made.

[D31: residual-preserving bound](02_P25_native/D31_RESIDUAL_PRESERVING_CHARGE_BOUND.md)
explains the unchanged synthetic M5 obstruction without zeroing node residuals;
it does not certify exact ideal-switch admissibility or accumulated solver error.

[D30: charge/flux necessary bound](02_P25_native/D30_CHARGE_FLUX_NECESSARY_BOUND.md)
adds an explicitly conditional analytical obstruction; it does not certify
the earlier sampled failure or demonstrate a complete periodic orbit.
