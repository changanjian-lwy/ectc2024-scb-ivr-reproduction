# C02 - the uniform interleave: slots referenced to phase 1's low-side turn-off (RESULTS)

Track C. One factor: cfg `slot_lo` = 1. Phases 2-4, and the slaves'
phase 1, are slotted from phase 1's low-side turn-off instead of its
high-side turn-on. This corrects the deviation flagged in C01.

**Boundary:** `BOUNDARY.md`, committed with the code (8a1f12d) before
any run. Every run records that commit with the co-simulation sources
unmodified.

**Records:**
- `cosim/run_*.json` and `cfg_*.json` (`make_cfgs.py`: A105's or C01's
  configuration plus `slot_lo`);
- `c02_summary.json` (`c02_analyze.py`, on the shared
  `scb_ivr.cosim.matrix`).

**Models:**
- **Physical:** as A105 (one module) and C01 (four modules):
  - Verilog RTL;
  - A88's plant (kernel2);
  - A105's I2;
  - 5%, 25 C.
- **Prediction:** C01's re-placement of the recorded waveforms (C01
  RESULTS Section 2).

## 0. Verdict

1. **The correction works as predicted, and nothing else moves.**
   - **One module:** the four low-side turn-offs are at 0 / 57.99 /
     116.01 / 174.01 ns after phase 1's (T/4 = 58.01 ns). A105 had
     them 9.44 ns late on every phase.
   - **Four modules:** the 16 gaps are 14.49-14.54 ns (T/16 = 14.50).
     C01 had 4.4-23.9 ns.
   - **Unchanged within the registered bands** in all nine runs:
     - soft switching (valleys, high-side and low-side turn-on V_DS);
     - sharing; steps; start-up;
     - the jitter spread.
   - The one-module runs are identical to A105 up to the handover
     (72 µs), as registered.

2. **The 16-phase output current ripple falls by ×5 (switching) and ×7
   (rms).**

   | m4_n0 | C01 | C02 | predicted (C01 re-placement) |
   |---|---|---|---|
   | pk-pk within one period (median) | 162.8 A | **31.0 A** | 31.3 A |
   | ac rms over the window | 45.9 A | **6.75 A** | 6.6 A |
   | pk-pk over the window | 162.8 A | 55.2 A | 31.3 A (**miss**, item 3) |

   - For one module the gain is small, as predicted: 31.3 → 29.4 A rms.
   - m4_L5 (±5% L): 62.4 A pk-pk and 7.64 A rms against C01's 188.1 /
     45.9 A, within the registered ±30% of the prediction.

3. **Two registered criteria miss as written. Neither is a defect of
   the correction.**
   - **m4_n0 window pk-pk (55.2 A, predicted 31.3 ± 30%):**
     - The voltage loop's Ton now toggles 567/568, and occasionally
       564/571: the Peterchev-Sanders limit cycle that A105's single
       module also has.
     - So the per-period mean current moves by 10.7 A, and the window's
       pk-pk adds that to the switching ripple.
     - C01 happened to settle inside the ADC's zero bin (Ton 568 for all
       200 periods). Its waveforms had no such motion, so the
       re-placement could not show it.
     - The switching prediction holds (31.0 A per period).
   - **m4_j30 late fires (slave 1: 6; C01: 1, module 3):**
     - Every one is under 0.2 ns late (Section 3).
     - Five fall in the master's learning phase (72-310 µs), where
       phase 1's turn-off is the asynchronous latch. Its time reaches
       t_lo1 only through the TDC report, which leaves slave 1's slot
       (+T/16) about zero margin.
     - The sixth is after learning, like C01's one.
     - **Flagged for later:** a predicted reference (the master's last
       t_lo1 + T) would give the slaves a period of margin.

4. **Recommendation: adopt `slot_lo` = 1 in the design from C03 on**
   (I2 + uniform interleave).
   - It costs nothing measurable in one module.
   - It restores P24's interleaved-ripple cancellation in the system.
   - Not yet run with it: driver mismatch, j100 and line steps. They are
     C03's rows.

## 1. Part A - one module against A105 i2 (last 200 periods; before the step for step runs)

| criterion (BOUNDARY 4A) | s1_n0 | s1_j30 | s1_s_m62 | s1_s_p62 | verdict |
|---|---|---|---|---|---|
| identical to A105 before 72 µs | yes | yes | yes | yes | pass |
| low-side turn-offs (k − 1) T/4 ± 0.1 ns after phase 1's | 0 / 57.99 / 116.01 / 174.01 (T/4 58.01) | 0 / 58.00 / 116.02 / 174.04 (58.02) | 0 / 57.99 / 116.01 / 174.00 | the same | pass |
| valleys within ±0.5 A of A105 | ≤ 0.01 A | ≤ 0.05 A | ≤ 0.01 A | ≤ 0.01 A | pass |
| high-side turn-on within ±0.2 V | ≤ 0.01 V | ≤ 0.02 V | 0 | 0 | pass |
| low-side turn-on V_DS ≤ 0 (n0) | ≤ −0.87 V | (+0.31 max; A105 +0.30) | ≤ −0.87 V | ≤ −0.87 V | pass |
| no overlap; peak ≤ 200 A | 0; 170.2 A | 0; 169.4 A | 0; 170.2 A | 0; 174.3 A | pass |
| late fires ≤ A105's | 0 (0) | 0 (0) | 0 (0) | 1 (1, the step) | pass |
| module ripple 100.9 A pk-pk / 29.4 A rms ± 20% | 105.8 / 29.42 (A105 126.6 / 31.30) | 106.2 / 29.43 | 103.8 / 29.42 | 103.8 / 29.42 | pass |
| Vo 1.000 V ± 1 mV | 1.00011 | 0.99998 | 1.00008 | 1.00008 | pass |
| step within ±10% of A105 | - | - | +11.30 mV (+11.65) | −14.59 mV (−14.68) | pass |
| j30 turn-off sd within A105's × (1 ± 0.3) | - | 0.49 / 0.49 / 0.54 / 0.51 (0.48 / 0.49 / 0.52 / 0.53) | - | - | pass |
| start-up ≤ 1.05 V | 1.0131 | 1.0134 | 1.0131 | 1.0131 | pass |

## 2. Part B - four modules against C01 (last 200 master periods)

| criterion (BOUNDARY 4B) | m4_n0 | m4_L5 | m4_j30 | m4_s_m250 | m4_s_p250 |
|---|---|---|---|---|---|
| 16 gaps T/16 ± 0.1 ns | 14.49-14.54 (C01 4.36-23.94) | 14.62-14.66 (T/16 14.63) | 14.50-14.54 (jitter; not graded) | 14.49-14.53 | 14.49-14.53 |
| ripple (pred. ±30%) | rms 6.75 pass; window pk-pk 55.2 **miss**; per period 31.0 | 62.4 / 7.64 pass (pred. 69.7 / 9.0) | 47.9 / 6.99 (C01 181.4 / 46.0) | 55.4 / 6.84 | 55.4 / 6.84 |
| locked periods | pass | pass | pass | pass | pass |
| normalised currents within ±1 A of C01 | 250.0 × 4 (250.1) | 238.4 / 249.7 / 249.7 / 262.2 (238.4 / 249.6 / 249.8 / 262.2) | 250.0-250.1 | 250.0 × 4 | 250.0 × 4 |
| valleys within ±0.5 A of C01 | ≤ 0.02 A | ≤ 0.03 A | ≤ 0.05 A | ≤ 0.02 A | ≤ 0.02 A |
| no overlap; peak ≤ 200 A; join ≤ 0.1 mV | 0; 170 A; 60 µV | 0; 176 A; 62 µV | 0; 171 A; 59 µV | 0; 170 A; 60 µV | 0; 176 A; 60 µV |
| step within ±10% of C01 | - | - | - | +11.26 mV (+11.35) | −14.74 mV (−14.63) |
| start-up ≤ 1.05 V | 1.0131 | 1.0134 | 1.0131 | 1.0131 | 1.0131 |
| late fires ≤ C01's | 0 (0) | 0 (0) | **[0, 6, 0, 0] (C01 [0, 0, 0, 1])** | 0 ([0, 0, 0, 1]) | [1, 0, 0, 0] ([1, 0, 0, 1]) |

**Ton over the window** (added after the runs; C01 in brackets):
- m4_n0: 568 ×167, 567 ×30, 571 ×2, 564 ×1 (568 ×200);
- m4_L5: 570/571 in both;
- m4_j30: 567/568 in both.

The limit cycle is the usual one. Whether it appears depends on where
the equilibrium falls in the ADC bin (C01 RESULTS Section 3).

## 3. The late fires in m4_j30 (diagnosis, after the runs)

**Where they happen.** The runs are deterministic (seeded), so the same
configurations were rerun to 160 and 320 µs into `tmp/`
(`scb_ivr.cosim.run CFG --out-dir ... --t-end-us T`).

| run | late fires by 160 µs | by 320 µs | by 500 µs |
|---|---|---|---|
| C02 m4_j30, slave 1 | 2 | 5 | 6 |
| C01 m4_j30, module 3 | - | 0 | 1 |

- The master's timed turn-off starts at 309.7 µs. Before that its
  phase 1 is turned off by the asynchronous latch (1024 fires).

**How late.**
- Every recorded phase-1 low-side turn-off of slave 1 lies within
  ±0.17 ns of the master's + T/16 (0-160 µs and 152-500 µs). This is
  the size of the 30 ps driver jitter on two edges.
- The one exception is at the handover (72.246 µs, −1.08 ns, early),
  where the period changes.
- So each late fire is a slot passed by less than ~0.2 ns, fired at
  the next window start.

**Mechanism (consistent with the data, not time-stamped):**
- In the learning phase the master's low-side turn-off time is the TDC
  report a_tlo. It reaches t_lo1 and the slaves a few 4 ns windows after
  the latch.
- Slave 1's slot is t_lo1 + 14.5 ns, so its margin is about zero.
- C01's reference, t_ref + 14.5 ns, was 9.4 ns later and had margin.

**Not corrected here** (one factor). Candidate, flagged:
- reference the slaves to the master's previous t_lo1 plus the averaged
  period, a slot known one period ahead;
- this is the predicted-timebase idea listed since A97 (Huber et al.
  2009).

## 4. Consistency with P24 (updates `../README.md` Section 2)

| point | P24 | after C02 | tag |
|---|---|---|---|
| interleaved phases and modules to reduce the output ripple | Sec. III-B | 16 low-side turn-offs T/16 apart (±0.04 ns). The high-side turn-ons follow each by its own dt_pred (8.2-9.4 ns), so they are uniform to ~1.3 ns | **C01's DEVIATION corrected** (with `slot_lo`) |
| ripple cancellation | Sec. III-B | 16-phase switching ripple 31 A pk-pk against 427 A with no module interleave and 140 A for one phase | consistent |
| everything else | - | as C01 | as C01 |

## 5. Next

- **C03: the four-module standard matrix with `slot_lo` = 1.** Driver
  mismatch m ±1 / ±3.4 ns, j100, line steps, and +5% L on a slave
  (C01's open question).
- **Flagged, not yet scheduled:**
  - the slaves' predicted reference (Section 3);
  - the Ton limit cycle's effect on the low-frequency output current
    (10.7 A per-period wander), which belongs with the loop's ADC
    resolution, not the interleave.

## Erratum (2026-10-03, external review)

**"16 gaps 14.49-14.54 ns"** (Sections 0 and 2) are gaps between each
phase's **mean** low-side turn-off over 200 periods (`lsoff_after`).
- **Cycle by cycle** (`matrix.gaps_per_cycle`): m4_n0's spacing has
  sd 0.028 ns and max 0.58 ns from T/16 = 14.5 ns. The Ton dither moves
  each period; the slaves follow the averaged period.
- The interleave is uniform on average and to ±0.6 ns in each cycle.
- The ripple results are unaffected: they sum the recorded waveforms of
  every cycle.

**"Soft switching unchanged"** here means the low side at zero voltage
and the high side at its valley (~9 V). The high side does not switch at
zero voltage (single-module summary).
