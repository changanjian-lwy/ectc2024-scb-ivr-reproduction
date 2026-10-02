# C03 - the four-module standard matrix (RESULTS)

Track C.

**Boundary:** `BOUNDARY.md`, committed (4d68c34) before any run.

**Records:**
- `cosim/run_*.json`, `cfg_*.json` (`make_cfgs.py`);
- `c03_summary.json` (`c03_analyze.py`, on the shared
  `scb_ivr.cosim.matrix`).

**Models:**
- **Physical:**
  - Verilog RTL `scb_multi`: four modules, A105's I2 with C02's
    `slot_lo`;
  - four A88 plants (kernel2) joined every 4 ns;
  - 5%, 25 C.
- **References:**
  - each row's single-module run (A105 i2, A106 pi100), which has no
    `slot_lo`;
  - for ls_*, C02's m4_n0.

## 0. Verdict

1. **The four-module system passes the standard matrix as the single
   module does.**
   - 18 runs, 72 module-runs. No overlap anywhere.
   - Peak ≤ 200 A in every row except l_p48_1us. That exception was
     registered as expected: 207 A in the master, as A106's single
     module.
   - The periods stay locked. The 16 gaps are T/16 to ±0.05 ns in every
     row without driver jitter.
   - **Per module against its single-module row:**
     - valleys within 0.05 A;
     - high-side turn-on V_DS within 0.01 V;
     - the low-side maximum within 0.1 V (m rows) or within +0.24 V
       (j rows, over all phases).
   - **Steps:** every load and line step's extreme is within 8% of the
     single module's, the largest gap l_p48_1us at −7.5% (registered:
     10%).

2. **A slave with larger inductors keeps zero-voltage switching up to
   +10%.** This answers C01's open question.

   | row | slave 1 current (vs nominal slaves) | slave 1 valleys | slave 1 high-side turn-on | slave 1 low-side max |
   |---|---|---|---|---|
   | ls_p5 (+5% L) | 237.4 A (−4.5%) | −4.87 to −5.96 A (nominal −5.85 to −6.95) | 9.13-9.34 V (+0.23) | −0.88 V |
   | ls_p10 (+10% L) | 229.6 A (−8.6%) | −3.89 to −4.98 A | 9.38-9.62 V (+0.47) | −0.83 V |

   - Every registered prediction holds: −4.6 ± 1.5% and −9 ± 3%, valley
     shifts 1.0 and 2.0 A, V_DS +0.23 and +0.47 V.
   - The shallowest valley at +10% is −3.89 A, 1.4 A beyond A82's −2.5 A
     soft-switching boundary.
   - So **D61's scheme A tolerates ±10% inductors without a per-slave
     valley loop.** The cost:
     - ±9% sharing;
     - a slightly harder high-side turn-on in the larger-L module (+0.5 V
       of 9 V).

3. **Misses as registered. None is a hard constraint.**
   - **Turn-off sd in the m rows (m1n, m1p, m3n, m3p).**
     - Without jitter, this sd only measures whether the voltage loop's
       Ton toggles (the Peterchev-Sanders limit cycle).
     - Each run either toggles or not: single m3n 0.02 A against four
       modules 0.15-0.19 A; single m1p 0.10-0.12 A against four modules
       0.06-0.09 A.
     - All are ≤ 0.23 A. **This criterion was ill-posed for jitter-free
       rows.**
   - **Low-side maximum, phase by phase, in j30 and j100.** A window's
     maximum is an extreme-value statistic, so phase-by-phase comparison
     is noise. Over all phases:
     - j100: 4.86 V against the single module's 4.89 V;
     - j30: 0.54 V against 0.30 V.
   - **Late fires:**

     | rows | where | count | cause |
     |---|---|---|---|
     | j30, j100, m and ls rows | slave 1, phase 1 | 1-9 | C02's mechanism: the slave reference's latency while the master learns |
     | l_m48_1us, l_m80_10us, m3p | master and slave 3, phase 1 | 1-3 | comes with `slot_lo` in one module too |

     - **The diagnostic** (`tmp/`, not published): A106's rows rerun with
       `slot_lo` on one module give 1 and 2 phase-1 late fires, where
       A106 had 0.
     - The mechanism is not identified, because late fires are counted
       but not time-stamped.
     - **The effect is bounded:** no overlap, and the peak current and Vo
       equal to the single module's (l_m48_1us: 190-191 A against 193 A,
       −17.96 mV against −18.46 mV).

## 1. The matrix (last 200 master periods; steps from 400 µs)

| row | peak (A), 4 modules (single) | gaps (ns) | step extreme (single) | back within 1% (single) | late fires (single) |
|---|---|---|---|---|---|
| n0 | 170 ×4 (170) | 14.49-14.54 | - | - | 0 (0) |
| m1n | 169 (169) | 14.49-14.53 | - | - | 1 (0) |
| m1p | 171 (171) | 14.50-14.55 | - | - | 0 (0) |
| m3n | 165 (165) | 14.50-14.54 | - | - | 1 (0) |
| m3p | 172-173 (173) | 14.50-14.54 | - | - | 2 (0) |
| j30 | 170-171 (169) | 14.50-14.54 | - | - | 6 (0) |
| j100 | 170-173 (170) | 14.51-14.57 | - | - | 9 (0) |
| s_m25 (−100 A) | 170 (170) | 14.49-14.53 | +5.41 mV (+5.34) | 0 (0) | 0 (0) |
| s_p25 (+100 A) | 170 (170) | 14.49-14.53 | −5.46 mV (−5.60) | 0 (0) | 0 (0) |
| s_m62 (−250 A) | 170 (170) | 14.49-14.53 | +11.26 mV (+11.65) | 4.97 µs (5.77) | 0 (0) |
| s_p62 (+250 A) | 174-176 (176) | 14.49-14.53 | −14.74 mV (−14.68) | 8.39 µs (8.39) | 1 (1) |
| l_m48_1us | 190-191 (193) | 14.49-14.53 | −17.96 mV (−18.46) | 3.04 µs (3.05) | 8 (0) |
| l_p48_1us | **207** / 199 / 199 / 200 (207) | 14.49-14.53 | +10.89 mV (+11.77) | 2.20 µs (2.44) | 1 (0) |
| l_m48_10us | 170 (170) | 14.49-14.53 | −3.81 mV (−3.86) | 0 (0) | 1 (1) |
| l_p48_10us | 171 (171) | 14.49-14.53 | +4.05 mV (+4.22) | 0 (0) | 1 (0) |
| l_m80_10us | 170 (170) | 14.49-14.53 | −7.44 mV (−7.44) | 0 (0) | 4 (0) |
| ls_p5 | 165-171 (C02 170) | 14.62-14.69 | - | - | 0 (0) |
| ls_p10 | 161-171 (C02 170) | 14.74-14.79 | - | - | 1 (0) |

**Ladder deviation peaks** after the steps are within 0.001 of the
single module's (e.g. l_m48_1us 0.0700 against 0.0697).

**Each module against its single-module row** (all modules and phases):

| row | valleys (A) | high-side turn-on (V) | low-side max (V) |
|---|---|---|---|
| m1n | −6.93 to −5.85 (single the same) | 8.91-9.07 (the same) | −0.87 (−0.87) |
| m1p | −6.94 to −5.85 (−6.92 to −5.84) | 8.90-9.07 (8.91-9.07) | −0.93 (−0.87) |
| m3n | −6.92 to −5.85 (−6.94 to −5.88) | 8.91-9.07 (8.91-9.06) | −0.92 (−1.01) |
| m3p | −7.02 to −6.19 (−7.00 to −6.18) | 8.90-8.97 (8.90-8.98) | −2.36 (−2.36) |
| j30 | −7.01 to −5.91 (−6.98 to −5.89) | 8.88-9.05 (8.89-9.06) | +0.54 (+0.30) |
| j100 | −7.17 to −5.99 (−7.12 to −5.96) | 8.82-9.03 (8.83-9.04) | +4.86 (+4.89) |

**Output current ripple** (16 phases, ac rms):
- 6.6-7.4 A in the n0, m and step rows;
- 8.5 A with j100;
- 8.3 A with slave 1 at +10% L.

## 2. Consistency with P24 (`../README.md` Section 2)

| point | P24 | C03 | tag |
|---|---|---|---|
| current sharing "the primary challenge" | Sec. III-B | ±10% inductor tolerance on one slave: −8.6% current, zero-voltage switching kept | D61 scheme A sufficient up to ±10% L; a sharing trim is an option, not a necessity |
| interleaved modules | Sec. III-B | uniform under driver mismatch, steps and line steps | consistent |
| everything else | - | as C02 | - |

## 3. What this closes, and what stays open

**Closed at the four-module level:**
- the standard matrix;
- inductor tolerance to ±10% on a slave.

**Open, flagged:**
- **The fast rising line step's 207 A.** It is a single-module property:
  phase 1's rail takes the whole step (LITERATURE Section 7). The
  scenarios (a)-(d) are for A108.
- **Late fires:** time-stamp them in the bridge records, then identify
  the `slot_lo` phase-1 path. Separately, the slaves' predicted
  reference (C02 Section 3).
- **Not in this matrix:**
  - module-to-module driver spread;
  - Cs, Coss or controller differences between modules;
  - a module starting into a running system (pre-bias);
  - shedding modules at light load (Cousineau et al. 2021).
