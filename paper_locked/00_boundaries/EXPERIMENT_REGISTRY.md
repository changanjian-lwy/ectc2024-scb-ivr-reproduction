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

## Reuse rule

Before a downstream experiment imports any result above, its header must name
the source experiment and copy both the permitted use and the prohibited claim.
Raw waveforms alone are never a parameter source.
