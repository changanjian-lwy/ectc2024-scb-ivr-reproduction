# Experiment registry and reuse boundaries

`SUCCESS` means only that the stated local acceptance test passed. It never
means that the 2024 converter, startup, ZVS, loss or hardware has been fully
reproduced.

| Experiment | Status | What it established | May be reused for | Must not be used to claim |
|---|---|---|---|---|
| Step 01 analytical audit | `PASS_EQ1_EQ2_EQ3 / CONFLICT_EQ4_TABLE1` | Duty, on-time and peak-current equations transcribed; inductance conflict exposed | Locked analytical inputs and two-branch L tests | Circuit, startup or ZVS reproduction |
| Step 02 topology/mode lock | `DOCUMENTED / PUBLICATION_SPICE_BLOCKED` | Canonical nodes and P24/P25 mode sequence | Netlist connectivity and state names | Numeric commutation timing |
| Step 03 source scan | `CANDIDATES_CLASSIFIED` | Startup, commutation and controller source roles | Selecting detachable candidate modules | Treating cross-topology values as P24 data |
| R00 zero start | `FAILED_ZERO_START_BASELINE` | Direct zero-state fixed PWM is not justified | Negative baseline only | Any electrical success |
| R01 family | `FAILED/INTERRUPTED_CONTROLLER_MODELS` | Instantaneous comparators chatter; several startup paths were unsupported | Numerical/controller lessons only | Power-stage failure or successful startup |
| R02A | `FAILED_PRECHARGE_ESTABLISHMENT` | Unmodified IPEC divider does not establish the required four-level ladder | Negative transfer result | P24 startup conclusion |
| R02B | `COMPLETED_FEASIBLE_TREND / NO_PASS` | Passive-divider capacitance/ramp sensitivity changes physically generated ladder | Choosing an explicitly labelled exploratory precharge point | P24 capacitor/ramp values or startup proof |
| R02C | `PASS_TIMING_LAW / NOT_HARDWARE_VALIDATED` | Literature active-current precharge timing equation behaves as expected | Equation-level startup module | Four-capacitor P24 implementation |
| R03A | `FAILED_FIXED_PWM_TAKEOVER / NUMERICALLY_COMPLETED` | Physically generated ladder survives briefly, but fixed PWM accumulates current | Motivation for boundary-aware takeover | Steady operation or safe current |
| R03B | `FAILED_NUMERICAL_ZCD_CHATTER` | Instantaneous algebraic ZCD is not executable | Requirement for state memory | Electrical behavior |
| R03C | `FAILED_NUMERICAL_COMMUTATION` | Ideal-diode substitution does not close the full commutation problem | Negative numerical lesson | Physical low-side operation |
| R03D | `PARTIAL_SUCCESS_OUTPUT / FAILED_CURRENT_BOUNDARY` | EPE2019 duty ramp controls output and source shock | Soft-start concept only | Phase-current safety, ZVS or P24 reproduction |
| R04A | `PASS_LOCAL_STATE_SEQUENCE / MODULAR_REGRESSION_RECONFIRMED` | Latched sequence works; Eq.(4) L gives 125 A, while Table-I L gives 68.5 A; modular rerun reproduced both | P24 local sequence, state-memory pattern and recalculated 1.4667-nH main value | Propagating the 2.68-nH table discrepancy, four-phase balance, startup or ZVS |
| R04B/R04B-LONG | `REJECTED_NON_P24_COMPLEMENTARY_PWM_BASELINE` | Ordinary per-leg complementary PWM can show near-1-V output while FC charge and phase currents remain unbalanced | Numerical anti-pattern only | Any P24 electrical conclusion, valid steady state, balance, startup or ZVS |
| R05A | `QUARANTINED_CROSS_PAPER_EXPLORATION` | Under its stated P25-assisted sequence and external Coss assumptions, the local threshold lies between 9.4% and 9.5% | Numerical lessons and later P25-branch comparison only | P24 sequence reproduction, startup, periodic balance, loss, or any judgment of P24's 1%-2% statement |
| A40 analytical audit | `PASS_ANALYTICAL_BOUNDARY / MISSING_MODE5_TIME_BUDGET_AND_CAP_PARTICIPATION` | P24 125 A is the zero-admission lossless rise; P25 Eq. (13) gives 7.392/3.696 ns for 385 pF at P24 1%/2%, but no unique C ceiling without an allowed Mode-5 time | Defining the A41 snubber-sweep axes, direction and acceptance metrics | Unique CH/CL values, complete four-phase ZVS, periodic closure or hardware behavior |
| A41 local snubber sensitivity | `28/28 NUMERICALLY COMPLETE / 0 ZVS / 28 GUARD_PASS` | At exact P24 1%-2% release, 0-2 nF positive added capacitance does not create high-side ZVS; it monotonically raises minimum post-release Vds and delays its minimum | Rejecting a wider passive-capacitance search; defining a zero-snubber negative-current threshold experiment | P24 periodic reproduction, hardware snubber need, four-phase closure, startup, or unpublished device values |
| A42 zero-snubber current threshold | `LOCAL_THRESHOLD_BRACKETED_7.76_TO_7.77_PERCENT` | With A41's zero-snubber state fixed, 7.76% leaves 13.924 mV and 7.77% first reaches Vds=0 after 2.155 ns | Separate P25-device-augmented mechanism branch and a concrete capacitance/path question for Mihai | Replacing P24 1%-2%, P24 periodic reproduction, full handoff, startup, loss, or hardware threshold |
| A43 7.77% full-machine transplant | `LOCAL_EVENT_PROGRESS / H2_ZVS_FAIL / GUARD_PASS` | With every A37 state coordinate and rule fixed, 7.77% reaches P1_M5 but H2 Vds bottoms at 1.418 V; the machine blocks H2 and all downstream phases | Demonstrating that A42's local threshold is state-dependent; defining a fixed-state 7.77%-9% H2 boundary scan | A periodic state, P24 1%-2% operation, complete handoff, startup, or hardware behavior |

## Reuse rule

Before a downstream experiment imports any result above, its header must name
the source experiment and copy both the permitted use and the prohibited claim.
Raw waveforms alone are never a parameter source.
