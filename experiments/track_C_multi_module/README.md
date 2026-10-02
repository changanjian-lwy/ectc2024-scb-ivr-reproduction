# Track C - multi-module (the level after the single module)

Started 2026-10-02, after the single-module level closed:
- A105 passed the standard matrix;
- `reports/SINGLE_MODULE_SUMMARY_2026-10-02.md` was written;
- D61 checked multi-module readiness;
- D62 gave the loss budget.

## 1. Module count: 4 (16 phases, 1 kW)

- **Our module is P24 Table 1's row** for 4 phases with IL_peak = 2 Io / (nP · nM) = 125 A, at Io = 1000 A. That makes nM = 4 at
  250 W per module, and Eq. (4)'s Lcrit 1.4667 nH.
- **P24's package section (Table 3, Figs. 5-6) uses 8 modules.** That is a different design point (1 MHz, MPC magnetic inductors) and
  does not match this reproduction's parameters.
- **Development and gates use 2 modules first** (cheaper), then 4.

## 2. Consistency with P24

| point | P24 (where) | here | tag |
|---|---|---|---|
| modules in parallel on one output, interleaved to reduce the output current ripple, 1 kW | Sec. III-B, Fig. 3 | M modules on one output node; uniform interleave of all M·N phases (T / (M·N) apart) | P24_EXPLICIT (parallel, interleaved); the uniform T/(M·N) shift is our reading, P24 gives no number |
| all high sides at the same frequency and duty cycle; the same for the low sides | Sec. III-B | one shared Ton for every module (D61's baseline); the period follows Ton | consistent |
| IL_peak per phase = 2 Io / (nP · nM) | Eq. / Table 1 | 4 × 4, 125 A | P24_EXPLICIT |
| current sharing between phases and modules is "the primary challenge" | Sec. III-B | no method in P24; ours: a shared loop and common Ton, sharing error = inductor tolerance (D61); option: negative-current trim | PROJECT_DECISION |
| the controller, synchronisation, start-up | not described | the single-module controller per module (A105's I2); slaves' phase 1 slot-timed from the master's period (the A97 mechanism, extended); the voltage loop at the system level | PROJECT_DECISION, from the CRM-PFC interleaving literature |
| output capacitance | conceptual only | the init run's 4.672 mF per module (EPE2019's bank, flagged since A72) × M | inherited, flagged |
| the mode itself: fixed Ton and frequency at the CCM/DCM boundary | Sec. III | boundary conduction with a fixed negative current and a period that follows it (P25's mode; A78-A105) | **DEVIATION, carried from the single module.** P24's fixed-frequency analysis does not reach soft switching in this circuit (A78-A86). The negative current is P25's 5%, not P24's 1-2% (D57: ≥ 5.3% is needed) |

## 3. Plan (each step with a bit-identical gate)

- **C1. Bridge refactor, no behaviour change.**
  - One module's state and signal handling become a class; the
    controller's signals go through an adapter.
  - Gate: `--full` regression identical (M = 1).
- **C2. RTL, opt-in.** Two new controller inputs:
  - an external Ton;
  - phase 1 as a slave, with an external slot time.
  - A generated M-module wrapper.
  - Gates: unit tests, synthesis, regression.
- **C3. The multi-module bridge.**
  - M single-module plants (each the bit-identical plant, with Co/M and
    its share of the load). Their output nodes are joined by charge
    conservation at every 4 ns window; the equalisation error is
    recorded.
  - A system controller: the shared voltage loop on the master's sample,
    the slaves' phase-1 slots.
  - Gates: M = 1 reproduces the single module; then M = 2.
- **C4. M = 4 on the standard matrix**, with inductor tolerances, against
  D61; the system-level start-up and line feed-forward.
