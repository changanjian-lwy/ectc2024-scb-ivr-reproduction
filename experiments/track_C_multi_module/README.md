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
| modules in parallel on one output, interleaved to reduce the output current ripple, 1 kW | Sec. III-B, Fig. 3 | M modules on one output node; the aim is a uniform interleave of all M·N phases (T / (M·N) apart) | P24_EXPLICIT (parallel, interleaved); the uniform T/(M·N) shift is our reading, P24 gives no number. **DEVIATION found in C01:** phase 1 of each module sat one valley delay (9.44 ns) early (A93/A97's slot reference), gaps 4.4-23.9 ns for 14.5 ns, output current ripple 45.9 A rms. **Corrected in C02** (`slot_lo`): mean gaps 14.49-14.54 ns (each cycle within 0.6 ns; 2 ns through steps), 6.75 A rms, switching ripple 162.8 → 31.0 A pk-pk per period |
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

## 4. Experiments

**The level is closed:** `../../reports/MULTI_MODULE_SUMMARY_2026-10-02.md` (corrected 2026-10-03, its Section 7).
**Acceptance gate:** `python3 scripts/acceptance.py` (every registered criterion: pass, documented miss or fail).

| experiment | one factor | result |
|---|---|---|
| [C01](C01_four_modules_baseline/RESULTS.md) | module count 1 → 4 (A105's I2, D61 scheme A) | works as D61 predicts: locked periods, ±5% L → ±4.7% sharing, steps and start-up equal to one module. Flagged: the interleave is not uniform (ripple ×7 in rms); the slaves' valleys are unregulated |
| [C02](C02_uniform_interleave/RESULTS.md) | the interleave reference: phases 2-4 and the slaves slotted from phase 1's low-side turn-off (`slot_lo`) | uniform: mean gaps 14.49-14.54 ns (each cycle ≤ 0.6 ns); ripple 45.9 → 6.75 A rms; soft switching, sharing, steps and start-up unchanged (one module identical to A105 up to the handover). Misses as registered: the window pk-pk (Ton limit cycle), slave 1's late fires < 0.2 ns in j30 (reference latency while the master learns). Recommended for the design from C03 on |
| [C03](C03_four_module_standard_matrix/RESULTS.md) | the four-module standard matrix with `slot_lo` (16 rows) and slave 1 at +5% / +10% L | passes as the single module: no overlap in 72 module-runs, steps within 8% of the single module's, mean gaps T/16 ± 0.05 ns (each cycle ≤ 0.62 ns; ≤ 2 ns through steps). A slave at +10% L: −8.6% current, valleys ≤ −3.9 A, low side at zero voltage, high side at its valley (≤ 9.62 V). Open: l_p48_1us 207 A (single-module, A108), rare late fires (< 10 per run) |
| [C04](C04_module_spread/RESULTS.md) | module-to-module spread: Cs ±20%, R ±30%, all with L ±5%, and a load step | holds: no overlap, mean gaps T/16 ± 0.05 ns (each cycle ≤ 0.61 ns), valleys ≤ −3.6 A, low side at zero voltage. Cs ±0.4%, R ±1.3% (slaves act as ~3.3 mΩ sources), all together −5.2 / +6.1% |
| [C05](C05_four_module_final_design/RESULTS.md) | the final single-module design (A124 2.5 MHz + A129 Vin feed-forward) on four modules, C03's matrix | steady state, load / line steps and ±10% slave L pass; m1n, m3n, j100 fail after the handover: a slave's unregulated phase-1 valley runs away (−96 / −130 A), Ton to its cap (RESULTS 0b) |
| [C06](C06_slave_floor/RESULTS.md) | A118's floor on a slave's phase 1 (cfg `slave_floor`, RTL + bridge) on C05's 18 rows | 18/18 without overlap, ≤ 185 A, locked; m1n 184 A, j100 completes; adopted with residuals: transient late fires (m1n 19, m3n 68), l_m48_1us +14% Vo / 11.1 µs, per-cycle spacing up to 65 ns through line steps |
| [C07](C07_module_spread_final/RESULTS.md) | C04's module spread (Cs, R, L) on the final design, floor on / off | floor on: ≤ 193 A, locked, valleys ±1.7 A; floor off 265 A; steady state unaffected by the floor (0.03-0.053 A) |
| [C08](C08_relative_cap_four_modules/RESULTS.md) | A136's relative phase-1 cap (vff rel_q8 320, rel_lp 1) on four modules, C06's rows + L × 1.2 | L × 1.2 locks with the absolute cap, holds with A136's; hard limits kept; new handover late fires, m3n sd 0.11 A, s_m25 +7.3 A |
| [C09](C09_seed_four_modules/RESULTS.md) | A137's restart (vff seed 1) on C06's 18 rows | not adopted: slaves seed after the master's first ADC sample moved Ton (1136 → 683) and lock ~35 µs (rail 1 13.8-15.4 V, peaks to 203.5 A); s_m25 +7.3 A = step offset; m3n sd = ADC limit cycle |
| [C10](C10_seed_before_entry/RESULTS.md) | vff seed 2 (every module seeds with the Ton before mode P; scb_vff tpre) on C06's 18 rows + A137's 18 single-module rows | adopted (user decision): slave rail 1 ≤ 12.36 V, steady ≤ 180 A, post-step within 4.2 A of C06 (≤ 188.7 A); single module identical 18/18; residual: one late fire on s_m62. Final design = C06 + vff {rel_q8 320, rel_lp 1, seed 2} |
