# A90 - junction temperature 125 C in the P24 module (RESULTS)

Track A, `CROSS_PAPER_EXTENSION` + `EXTERNAL_DEVICE_DATA`.

**Boundary:** `BOUNDARY.md`, written before any run and unmodified.

**Records:**
- `run_*.json`;
- `a90_summary.json`;
- `gate_pairs.json`;
- `epc2067_fig9_rdson_vs_tj.csv` with `epc2067_fig9_digitization.json`;
- `a90_fig9_vs_epc_model.json`.

**Model: the physical model** (A88's simulator, adopted controller, with a
uniform junction temperature).

**The mathematical-model counterpart is D48**
(`symbolic_derivations/03_P24_native/D48_P24_HOT_JUNCTION_EVENT_MAP.md`).

## 0. Verdict

1. **At TJ = 125 C the adopted module still works.**
   - At 2%, 3%, 5% and 7.5% every phase turns on predictively once per
     cycle, with no restart.
   - The reverse-conduction loss stays 0 W.
   - Vo is regulated to 1.0000 V and settles 68.5-70.0 us after the
     handover, as at 25 C.
   - Criterion 2 passes at 2%, 3% and 5%. At 7.5% the dither is 1.09 A,
     the same margin question as at 25 C (1.14 A in A88).
2. **The cost is conduction loss:**

   | | 25 C | 125 C |
   |---|---:|---:|
   | P_cond, 2-7.5% | 12.2-12.7 W | **19.4-20.2 W** |
   | conduction + turn-on proxy | about 22 W | about 30 W |
   | proxy efficiency at 250 W | about 92% | about 89% |

   The increase is the RDS(on) factor, x 1.59.
3. **The operating point moves only slightly.**
   - Ton rises by 0.16-0.18 ns.
   - The period shortens by 2.3-2.4 ns: with the larger R the freewheeling
     current falls faster, and phase 1 reaches its target sooner. This is
     an interpretation, not tested separately.
   - Phase 4's current at its turn-off moves by at most -0.13 A (2%: -1.85
     to -1.98 A), and its turn-on voltage by at most -0.03 V.
4. **The timed low side keeps its margin.**
   - The learned dead time is 0.93-1.23 ns.
   - The free window after the zero crossing narrows slightly with the
     reverse threshold (2.09 to 1.95 V), measured in D48 at 3%:

     | | 25 C | 125 C |
     |---|---:|---:|
     | phases 1-3 | below 0.23 ns | below 0.21 ns |
     | phase 4 | below 0.17 ns | below 0.16 ns |

5. **The two models agree** (D48 at matched parameters):

   | quantity | difference |
   |---|---:|
   | Ton | within 0.02 ns |
   | period | within 0.18 ns |
   | phase-4 current | within 0.04 A |
   | turn-on voltage | within 0.03 V |

## 1. The temperature data (BOUNDARY Section 2)

| | 25 C | 125 C | sources, and check |
|---|---|---|---|
| RDS(on) factor | 1 | 1.5858 | Fig. 9 (digitised here; tick residual 1.06 C / 0.004). The EPC SPICE model gives 1.5818 and agrees within 0.25% over 0-150 C. |
| per-phase R (all RDS(on), A72) | 0.54 mOhm | 0.8563 mOhm | A72 x factor |
| reverse drop per device | Vf 2.0894 V, 6.013 mOhm | Vf 1.9483 V, 8.948 mOhm (error at most 38 mV over 10-100 A) | Fig. 8 (A57). Within 35 mV of the EPC model at 125 C (A87). |
| Coss(V) | Fig. 5a | unchanged | The datasheet gives 25 C only, and the EPC model's 6 capacitance expressions have no temperature term. |

The EPC model's own RDS(on) at 25 C is 1.280 mOhm, against the printed
typical 1.3 mOhm.

## 2. Runs (last 50 cycles)

All runs use the adopted controller:
- predictive valley high side, learning at restarts;
- timed low side;
- trim 0.5;
- restart 20 / 400 ns;
- ki 0.25 ns/V;
- t_d 10 ns;
- datasheet Coss(V) and reverse drop.

In brackets: A88 at 25 C.

| run | target | TJ | phase 4 at turn-off, mean [min, max]; Vds at turn-on | phases 1-3 Vds at turn-on | Ton | period | dither | P_cond | P_rev | P_on proxy | peak Vds / current | criterion 2 |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| r0 (gate) | 3% | 25 C | -3.19 [-3.59, -2.78] A; 9.90 V | 9.61-9.63 V | 17.519 ns | 226.38 ns | 0.86 A | 12.23 W | 0 | 9.98 W | 26.68 V / 176 A | pass (= A88 r1) |
| r2 | 2% | 125 C | -1.98 [-2.41, -1.56] A; 10.21 V (-1.85; 10.24) | 9.87-9.90 V | 17.604 (17.442) ns | 222.09 (224.41) ns | 0.93 (1.01) A | 19.37 (12.17) W | 0 | 10.77 W | 26.59 V / 175 A | pass |
| r1 | 3% | 125 C | -3.28 [-3.64, -2.91] A; 9.88 V (-3.19; 9.90) | 9.61-9.64 V | 17.684 (17.519) ns | 224.04 (226.38) ns | 0.80 (0.86) A | 19.48 (12.23) W | 0 | 10.04 W | 26.59 V / 174 A | pass |
| r3 | 5% | 125 C | -5.80 [-6.20, -5.40] A; 9.10 V (-5.75; 9.11) | 8.94-8.97 V | 17.911 (17.739) ns | 229.33 (231.73) ns | 0.88 (0.86) A | 19.77 (12.41) W | 0 | 8.51 W | 26.74 V / 171 A | pass |
| r4 | 7.5% | 125 C | -8.98 [-9.48, -8.48] A; 8.02 V (-8.95; 8.02) | 8.00-8.05 V | 18.256 (18.072) ns | 237.20 (239.64) ns | 1.09 (1.14) A | 20.22 (12.69) W | 0 | 6.47 W | 26.85 V / 168 A | soft, no restart; dither 1.09 A |

## 3. Checks

- **Regression gate.** r0 (`--tj 25`) replays A88 run r1 bit-identically:
  1781 sections, difference 0.0, equal end state.
- **The data checks** of Section 1.

## 4. Predictions (BOUNDARY Section 5) against the results

| | predicted | result |
|---|---|---|
| P_cond | x R factor, about 19.4 W at 3% | 19.48 W (x 1.593) |
| Ton | +0.3-0.5 ns | +0.16-0.18 ns: less than predicted |
| period | (not predicted) | -2.3 to -2.4 ns |
| P_rev | 0 W | 0 W |
| low-side dead time | unchanged within 0.02 ns | D48: -0.007 to -0.009 ns |
| soft switching, phase 4 | unchanged within the dither, turn-on voltage within 0.05 V | yes: within -0.13 A and -0.03 V |
| criterion 2 | 3%, 5% pass; 2%, 7.5% a margin question | 2%, 3%, 5% pass; 7.5% 1.09 A |
| free window | about 0.15 ns (phase 4), about 0.21 ns (phases 1-3) | below 0.16 and below 0.21 ns |

**The Ton prediction was too high.** It took the period as fixed. The
shorter period gives the same output volt-seconds with a smaller Ton
increase.

## 5. Limits

- **A uniform, fixed junction temperature.** There is no thermal network,
  no gradients between devices, and no self-consistent TJ from the
  losses. Those are the next level's thermal model.
- **Coss(V) at 25 C.** There is no public temperature data; the EPC model
  has none either.
- **The base R** is A72's duty-weighted 25 C maximum RDS(on), times the
  typical temperature factor.
- **The module R contains no copper** (DCR 0, as in Track A), so copper
  temperature effects are absent.
- **Not covered:**
  - dynamic RDS(on) (current collapse);
  - temperature drift of the gate driver and comparators;
  - package and PCB parasitics.

## 5a. Reproduction

```
python3 digitize_epc2067_fig9.py <path/to/epc2067_datasheet.pdf>
python3 a90_check_fig9_vs_epc_model.py <path/to/EPCGaNLibrary.lib>
zsh run_a90.sh
python3 a90_analyze.py
```

The mathematical-model side:

```
python3 -m scripts.audit_p24_hot_orbits --pct 3.0         # 5.0, 7.5; 2.0 with --tol 1e-7
python3 -m scripts.audit_p24_hot_orbits --window
```

The datasheet PDF and the SPICE library are not in this repository.
