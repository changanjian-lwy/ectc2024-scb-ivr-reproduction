# C03 - the four-module standard matrix (BOUNDARY)

Track C. **Written before any C03 run.**

**The design under test:** C02's four modules, A105's I2 with
`slot_lo`.

**The matrix:**
- the shared standard matrix (`scb_ivr.cosim.matrix.ROWS`, 16 rows: A105's
  and A106's);
- two rows with one slave's inductors larger, the question C01 left
  open.

## 1. Question

Does the four-module system pass the matrix the single module passed,
module by module? Specifically:
- Each module's soft switching under driver mismatch and jitter.
- Load steps (×4 at the system) and line steps.
- Whether a slave with larger inductors keeps its zero-voltage turn-on.
  Its valley is not regulated (C01 Section 3).

## 2. Runs (all from `make_cfgs.py`)

| rows | change from C02 m4_n0 | to |
|---|---|---|
| n0, m1n, m1p, m3n, m3p, j30, j100 | driver mismatch m (ns) / jitter σ (ps) on every module, each module its own seed | 500 µs |
| s_m25, s_p25, s_m62, s_p62 | system load step −100 / +100 / −250 / +250 A at 400 µs (the matrix's per-module steps × 4) | 600 µs |
| l_m48_1us, l_p48_1us, l_m48_10us, l_p48_10us, l_m80_10us | shared input step −4.8 / +4.8 / −4.8 / +4.8 / −8 V over 1 or 10 µs at 400 µs | 600 µs |
| ls_p5, ls_p10 | slave 1's inductors +5% / +10%, the rest nominal, n0 | 500 µs |

**References:**
- each row's single-module run: A105 `run_i2_<row>`, A106
  `run_pi100_<row>`;
- for ls_*, C02's m4_n0.

## 3. Registered predictions and criteria

Over the last 200 master periods, before the step for step runs.

1. **Hard constraints, every row:** no overlap in any module; peak
   ≤ 200 A.
   - **Expected exception:** l_p48_1us. A106's single module peaks at
     207 A there, and the four-module system shares the same input.
     Expected 200-215 A per module, a known open item (input
     feed-forward), not a C03 failure.
2. **Locked and uniform:** every row has the slaves' periods equal to
   the master's within 0.1 ns, and the 16 gaps within T/16 ± 0.1 ns at
   m = 0, σ = 0.
3. **Each module like its single-module row** (n0, m and j rows):
   - valleys within ±0.5 A of the single-module run's, phase by phase;
   - high-side turn-on within ±0.2 V;
   - low-side turn-on V_DS maximum ≤ the single module's + 0.3 V;
   - turn-off sd within the single module's × (1 ± 0.3), or ±0.05 A
     when below 0.17 A.
4. **Steps:** the extreme within ±10% of the single module's row (the
   same per-module step). Back within 1% within the single module's
   time + 2 µs. Ladder deviation peak ≤ the single module's + 0.01.
5. **Larger slave inductor** (D61: equal Ton, current ∝ 1/L; C01: a
   slave's valley moves with its L):
   - ls_p5: slave 1 carries −4.6% ± 1.5% of a nominal module (C01:
     −4.6% for +5%). Its valleys are 0.5-1.5 A shallower than the
     nominal slaves'. Its high-side turn-on V_DS rises 0.1-0.4 V.
   - ls_p10: −9% ± 3%; valleys 1-3 A shallower; high-side turn-on
     +0.2-0.8 V.
   - **Zero-voltage turn-on kept in both:** slave 1's low-side turn-on
     V_DS ≤ 0 and its valleys still ≤ −2.5 A (A82's soft-switching
     boundary).
   - **What would fail:** a valley above −2.5 A, or a low-side turn-on
     with positive V_DS, at +10%. That would make ±10% inductor
     tolerance infeasible without a per-slave valley loop (D61 scheme
     B, C01 Section 3).
6. **Late fires:** at most as many as the single module's row, plus
   C02's j30 mechanism (slave 1 during the master's learning phase, each
   < 0.2 ns late) in jitter rows.

## 4. What stays assumed

As C01 and C02:
- identical controllers;
- one output node;
- an ideal shared input;
- 25 C;
- Co inherited.

The driver mismatch m is the same on every module (the matrix's
definition). Module-to-module driver spread is not in this matrix.
