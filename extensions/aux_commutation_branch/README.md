# Extension: an auxiliary commutation branch for the high side's zero-voltage turn-on

**This is our extension, not part of the P24 / P25 reproduction.** Neither paper has this branch. It adds hardware
to P24's topology: per phase, an inductor Lr and a bidirectional switch to a capacitor Cm. The main reproduction line
does not depend on anything here.

**Status (2026-10-02): built and evaluated as cases; not adopted.** The adoption decision is open for Mihai's
evaluation (Section 3).

## 1. What is here

| item | path |
|---|---|
| A101: the branch in the Verilog co-simulation (first designs) | `experiments/A101_aux_commutation_branch/` |
| A102: the branch over its assumed values (enable, load steps, 2%, realism) | `experiments/A102_aux_branch_scenarios/` |
| D56: single-phase edge and cycle model (Chinese) | `derivations/D56_P24_AUX_COMMUTATION.md` |
| D57: scenarios - P24's 1-2%, losses, area, enable, load (Chinese) | `derivations/D57_P24_AUX_SCENARIOS.md` |
| D56 / D57 records | `derivations/diagnostics/` |
| scripts | `scripts/p24_aux_commutation.py` (D56), `scripts/p24_aux_scenarios.py` (D57) |
| Python modules | `src/scb_ivr/extensions/p24_aux_commutation.py`, `p24_aux_scenarios.py` |
| tests | `tests/extensions/` (11) |

**Run from the project root:**

```
python3 extensions/aux_commutation_branch/scripts/p24_aux_commutation.py
python3 extensions/aux_commutation_branch/scripts/p24_aux_scenarios.py
python3 extensions/aux_commutation_branch/experiments/A101_aux_commutation_branch/a101_analyze.py
python3 extensions/aux_commutation_branch/experiments/A102_aux_branch_scenarios/a102_analyze.py
PYTHONPATH=src python3 -m scb_ivr.cosim.run extensions/aux_commutation_branch/experiments/A102_aux_branch_scenarios/cosim/cfg_<name>.json
```

**What stays in the shared code.** The branch support is an opt-in part of the shared co-simulation plant
(`src/scb_ivr/cosim/`: circuit, plant, C kernel, bridge; cfg key `aux`; CHANGELOG entries A101 and A102). Without
`aux` every matrix and result is as before (`--full` regression bit-identical). Moving it out would mean a second
plant; it stays shared.

**What the main line keeps from this work** (main-line results that were computed here):
- **P24's 1-2% claim.** With P24's own inductor values and node compositions, full high-side zero voltage
  without a branch needs at least 5.3% (D57 Section 2).
- **The hard turn-on loss.** D56's central estimate is the energy balance's minimum (Qoss·V for identical
  devices), 9.3 W for four phases at 5%; A91's lower bound is not reachable (D57 Section 3).
- **The 2% target in the Verilog co-simulation.**
  - The adopted design without a branch (A102 `ref_2pct`) is soft and matches D51's 2% orbit within 0.05 V.
  - The orbits `D50/D51_orbit_2p0pct_m0p0.json` stay in `symbolic_derivations/03_P24_native/diagnostics/`.

## 2. Results

**The branch.** Lr and a bidirectional switch (two dies of α × EPC2067 in common source) from x_k to a
self-balanced Cm (Vm 8-9.5 V). It is commanded as the low side's complement and opens at zero current.

**Why a capacitor and not Vo.** P24's 1.47 nH filter inductor needs about 33 A at the turn-off for any branch to
0 V or Vo. A source above half the rail needs no boost (D56).

**Conditions:** P24 single module, 48 V → 1 V, ~250 A resistive load, 25 C, 5% negative current unless stated;
Verilog RTL with A88's plant (kernel2) and the adopted design (A92 + A97); D56 / D57 as the mathematical model.

| result | value |
|---|---|
| high-side turn-on V_DS | Lr 0.75 nH: zero (−0.7 V); 1.25 nH: 2.1 V; no branch: 9 V |
| low side | zero voltage kept; ripple 1-2% lower |
| net loss, four phases (central model, measured) | −4.4 W (0.75 nH), −5.0 W (1.25 nH) |
| net with air-core Lr, 50% gate supply and 5 A residual together | −2.6 to −3.4 W; 1-2% of the output |
| area against the main stage | dies +10-12%, Lr +3.6-3.8% (peak stored energy), Cm +1-5.5%, four more floating drivers per module |
| enable after the handover (200 µs) | stable, settles in 24-32 µs; **Vo to 1.09-1.11 V** (Ton must fall 16-19%) |
| ±62.5 A load steps | all criteria met; Vo extremes as without a branch |
| 2% with a branch | within 0.3 W of 5% with a branch |
| D57 against the co-simulation | within 0.15 V (Vm) and 0.21 V (V_DS), except past-the-rail turn-ons |

**Trade-offs** (moved here from `reports/TRADEOFF_SCORECARD.md`, where they were T9-T11):

| | trade-off | state |
|---|---|---|
| T9 | hard turn-on loss ↔ branch losses and area | resolved as cases: −2.6 to −5.2 W against the area above |
| T10 | branch saving ↔ jitter of phases 2-4 | at 30 ps, turn-off-current spread 0.6 → 0.9-1.3 A, period spread 0.58 → 0.76-0.84 ns; not resolved |
| T11 | branch enable ↔ Vo | Vo to 1.09-1.11 V at the enable; to be folded into the start-up design |

## 3. Open, for evaluation

- **Adopt or not:** 1-2% of the output against the area and four more floating drivers per module.
- **Which design:**
  - 1.25 nH: 2 V, robust to load;
  - 0.75 nH: zero voltage, 0.3-0.4 V at light load.
- **Enable:** the Vo transient, to be designed with the main line's start-up (not as a separate patch).
- **Jitter (T10).**
- **A real bidirectional switch:**
  - a ~12 V die;
  - its floating gate supply;
  - its zero-current detection.

## 4. Path map (moved 2026-10-02)

A101's and A102's BOUNDARY and RESULTS are registered records and keep the paths they were written with:

| written as | now |
|---|---|
| `experiments/track_A_periodic_steady_state/A101_aux_commutation_branch/` | `extensions/aux_commutation_branch/experiments/A101_aux_commutation_branch/` |
| `experiments/track_A_periodic_steady_state/A102_aux_branch_scenarios/` | `extensions/aux_commutation_branch/experiments/A102_aux_branch_scenarios/` |
| `symbolic_derivations/03_P24_native/D56_P24_AUX_COMMUTATION.md`, `D57_P24_AUX_SCENARIOS.md` | `extensions/aux_commutation_branch/derivations/` |
| `symbolic_derivations/03_P24_native/diagnostics/D56_aux_commutation_5p0pct.json`, `D57_aux_scenarios.json` | `extensions/aux_commutation_branch/derivations/diagnostics/` |
| `scripts/p24_aux_commutation.py`, `scripts/p24_aux_scenarios.py` | `extensions/aux_commutation_branch/scripts/` |
| `src/scb_ivr/p24_aux_commutation.py`, `p24_aux_scenarios.py` (`scb_ivr.p24_aux_*`) | `src/scb_ivr/extensions/` (`scb_ivr.extensions.p24_aux_*`) |
| `tests/test_p24_aux_*.py` | `tests/extensions/` |

- The run records' provenance keeps the configuration paths they ran with.
- After the move, the analyses and both scripts were rerun from the new places, and every output equals the
  committed one.

## Erratum (2026-10-02, found in D62)

D57's Lr technology "as_main_inductor" (0.54 mΩ per 1.4667 nH) is not the main
inductor's resistance. It is the plant's duty-weighted switch on-resistance
(A72). The main inductor's DCR is 0 in this model.
- **Effect on the branch's nets:** small. That case gives 0.28-0.46 mΩ
  against the fixed 0.2 mΩ; the Table 2 cases are unaffected.
- **Real inductor technologies:** see the main line's D62.
