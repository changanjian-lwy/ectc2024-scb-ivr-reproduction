# A101 / D56 - an auxiliary commutation branch for the high side's zero-voltage turn-on (RESULTS)

Track A, `CROSS_PAPER_EXTENSION`.

**Boundary:** `BOUNDARY.md`.
- Sections 1-8 were written before any co-simulation code.
- The predictions (`d56_predictions.json`) were registered in c127cf3.

**Records:**
- `cosim/run_*.json` and `cfg_*.json`;
- `a101_summary.json` (`a101_analyze.py`).

**Models:**
- **Physical:** Verilog RTL (unchanged) with A88's plant (kernel2) and the
  adopted design (A92's correctors, A97's slots), 5%, 25 C, ~250 A
  resistive load, 500 µs, Cm from 0 V.
  - Per phase: Lr and a bidirectional switch (two dies of alpha ×
    EPC2067) to Cm = 1 µF.
  - The switch is commanded with the low side complemented and opens at
    zero current.
- **Mathematical:** D56, a single-phase edge and cycle model
  (`symbolic_derivations/03_P24_native/D56_P24_AUX_COMMUTATION.md`).

**Statistics:** over the last 200 periods, unless stated.

## 0. Verdict

1. **The high side turns on at zero or near-zero voltage, and the low
   side keeps its zero voltage, in a stable closed loop.** The main ripple
   does not grow.

   | run | Lr | high-side V_DS at turn-on (four phases) | net loss change, four phases | registered criteria |
   |---|---|---|---|---|
   | ref | none | 8.9-9.05 V | 0 | - |
   | **p125** | 1.25 nH | **2.11-2.15 V** | **−5.0 to −5.3 W** (D56: −4.9 to −5.2) | **all met** |
   | dz_lr100 (diagnostic) | 1.0 nH | 0.93-0.97 V | −5.0 to −5.3 W | (no per-phase prediction) |
   | **dz_vz0** (diagnostic) | 0.75 nH | **−0.72 to −0.79 V** | **−4.4 to −4.8 W** (D56: −4.1 to −4.5) | **all met** |
   | z075 (registered) | 0.75 nH | +2.7 V mean, up to +15 V (phases 2-4) | (unstable) | **missed** |

   - In every stable run:
     - the low side's turn-on V_DS is −1.1 to −1.9 V;
     - each phase's ripple is 1-2% below the reference;
     - Vo is 1.000 V.
   - **At ~250 W the net is 2% of the output, as D56 predicted.**
2. **The registered full-zero-voltage run (z075) was unstable, and the
   cause was the measurement I added, not the circuit.**
   - z075 used the new option `valley_zero` 1: the high side's valley
     measurement stops at the first V_DS ≤ 0.
   - Under it, phases 2-4 (whose low sides turn off at a predicted time,
     not at a current comparator) lost control of their turn-off current:
     - mean −7 to −9 A with a spread of 26-36 A, from −117 to +38 A;
     - branch-current bursts of ~400 A when Cm swung by up to 18 V;
     - Vo oscillating between 0.93 and 1.08 V with a period of ~20 µs.
   - Phase 1, whose low side turns off at its current comparator, stayed
     stable.
   - **The same design with the existing valley measurement** (dz_vz0):
     - meets every registered criterion;
     - its high side turns on 0.7-0.8 V past the rail, which is below the
       reverse-conduction threshold (2.09 V), so there is no reverse
       conduction.
   - **This follows BOUNDARY Section 6.2's first choice** ("check whether
     the existing predictive turn-on and A92's corrector converge"), which
     the registered runs skipped. **dz_vz0 was run after z075's result was
     seen.**
   - A larger Cm (10 µF, dz_cm10) did not stabilise `valley_zero` 1. The
     instability is in the measurement and corrector loop, not in Cm's
     charge balance.
   - **`valley_zero` now defaults to 0.**
3. **D56 predicted the stable runs closely** (Section 3):
   - Vm within 0.15 V;
   - V_DS within 0.1 V;
   - branch currents within 5%;
   - the net loss change within 0.3 W.
4. **New costs found, not in D56:**
   - **Start-up.** With Cm starting at 0 V and the branch active from the
     start, branch currents reach 270-430 A until about 150 µs, in every
     design. They settle by 108-146 µs (Cm within 2%).
     - **A practical design must enable the branch after the handover,
       with Cm precharged.** Not tested.
   - **Jitter.** At 30 ps, phases 2-4's turn-off-current spread rises from
     0.58-0.64 A (reference) to 0.9-1.3 A, and the period spread from
     0.58 to 0.76-0.84 ns.
     - With the branch, the high side's zero voltage no longer depends on
       that current, so the margin it costs is smaller than before.
   - **All four phases need a branch.** With a branch on phase 1 only
     (dz_ph1), phase 1's faster edges shift the slot schedule. Phases 2-4
     then turn off at +11 A, without negative current.
5. **Not adopted yet.** The decisive uncertainties are:
   - the hard turn-on loss model (Section 4);
   - the start-up;
   - the real cost of the bidirectional switch (BOUNDARY Section 8).

## 1. Gates

| check | result |
|---|---|
| shared plant with the branch off | `--full` regression PASS (bit-identical; `highoffs_last` is a format addition) |
| the branch in all four plants | `tests/test_cosim_plants.py`: Reference, Fast, Kernel and Kernel2 bit-identical over 3000-20000 steps with branches on every phase, including the zero-current openings (6 of 6) |
| D56 | `tests/test_p24_aux_commutation.py`, 6 of 6 |
| RTL | unchanged |
| provenance | every run from committed code (`cosim_sources_modified`: false) |

## 2. Runs

| run | status | design | note |
|---|---|---|---|
| ref | 500 µs | none | the comparison |
| z075 | 500 µs, unstable | 0.75 nH, alpha 0.3, `valley_zero` 1 | registered |
| p125 | 500 µs | 1.25 nH, alpha 0.25, `valley_zero` 1 (never triggered: V_DS stays above 0) | registered |
| z075_j30 | **overlap stop at 396.8 µs** (phase 4) | z075 + 30 ps | registered |
| dz_vz0 | 500 µs | z075 with `valley_zero` 0 | diagnostic |
| dz_lr100 | 500 µs | 1.0 nH, alpha 0.25 | diagnostic |
| dz_cm10 | 500 µs, unstable | z075 with Cm 10 µF | diagnostic |
| dz_ph1 | 500 µs | z075 on phase 1 only | diagnostic |
| dz_ref_j30, dz_vz0_j30, dz_p125_j30 | 500 µs, no overlap | 30 ps on every edge | diagnostic |

## 3. Against D56 (per phase, 1/2/3/4)

| quantity | p125 co-simulation | p125 D56 | dz_vz0 co-simulation | z075 D56 |
|---|---|---|---|---|
| Vm (V) | 8.20 / 8.41 / 8.41 / 8.73 | 8.28 / 8.41 / 8.42 / 8.68 | 9.02 / 9.26 / 9.27 / 9.59 | 9.06 / 9.18 / 9.19 / 9.45 |
| high-side V_DS (V) | 2.11 / 2.14 / 2.15 / 2.14 | 2.14 / 2.05 / 2.06 / 2.03 | −0.74 / −0.72 / −0.72 / −0.79 | 0 (at the rail) |
| branch current (A) | +22.1/−27.3 … +21.1/−25.8 | +22.1/−27.7 … +20.8/−25.8 | +33.2/−35.6 … +31.4/−33.3 | +32.9/−36.6 … +30.7/−33.8 |
| high-side turn-off current (A) | 159 / 158 / 158 / 160 | 162 / 163 / 163 / 162 | 167 / 165 / 165 / 167 | 171 / 172 / 172 / 170 |
| low-side turn-on V_DS, max (V) | −1.11 / −1.22 / −1.22 / −1.65 | zero voltage | −1.24 / −1.30 / −1.32 / −1.66 | zero voltage |
| ripple p-p (A), reference 140.1 / 140.4 / 140.4 / 141.8 | 138.7 / 138.8 / 138.8 / 139.9 | unchanged | 138.0 / 138.2 / 138.2 / 139.1 | unchanged |
| Cm within 2% from 0 V | 127 / 144 / 139 / 138 µs | stable | 108 / 144 / 116 / 132 µs | stable |

- **dz_vz0's high side turns on past the rail** because A92's corrector
  aims 94 ps after the valley. Here that is the reverse-conduction
  region's minimum, not the rail.
- **The period shortens** from 232.2 ns to 222.9-225.7 ns, because the
  transitions are faster. Powers below use each run's own frequency.

## 4. Loss bookkeeping (nJ per cycle and phase, phase 1; four-phase totals)

**Method.** D56's formulas, applied to the co-simulation's measured
quantities:
- the hard turn-on from each turn-on's V_DS;
- branch conduction from the recorded ∫i² dt;
- reverse conduction from the recorded energies;
- BDS gate and Coss at the measured Vm;
- the overlap at the measured turn-off currents.

**The main switches' extra conduction is D56's**, not measured.

| term | p125 | dz_lr100 | dz_vz0 |
|---|---:|---:|---:|
| hard turn-on saved | −510 | −532 | −538 |
| branch conduction | +77 | +97 | +107 |
| reverse conduction | 0 | 0 | 0 |
| BDS gate | +43 | +43 | +51 |
| BDS Coss | +38 | +41 | +55 |
| main switches' extra conduction (D56) | +24 | +27 | +30 |
| high-side turn-off overlap | +6 to +23 | +7 to +26 | +8 to +31 |
| **four phases** | **−5.04 to −5.33 W** | **−4.95 to −5.29 W** | **−4.37 to −4.77 W** |

**The sign rests on the hard turn-on model, as in D56.**
- The saving uses D56's central estimate: the device's Eoss plus the
  charge of the other capacitances drawn through its channel, 538 nJ at
  8.94 V.
- With A91's lower bound (the high side's Eoss alone, 3.1 W for four
  phases at 5%), the branch would roughly break even or lose.

## 5. What is not covered

- **Start-up:** enabling after the handover, with Cm precharged.
- **Load and line steps; other targets** (2%); temperature.
- **The bidirectional switch:**
  - a real device (here alpha × EPC2067; a ~12 V die would do);
  - its floating gate supply;
  - its zero-current detection, which is ideal here.
- **Lr's and Cm's own losses** beyond 0.2 mΩ for Lr; their layout in the
  package.
- **The main switches' conduction** with the branch: D56's estimate, not
  measured.
- **Why `valley_zero` 1 destabilises phases 2-4.** Identified as the
  measurement and corrector loop by elimination (dz_vz0, dz_cm10). The
  mechanism itself is not derived.
