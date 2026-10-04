# P24 multi-module system - summary for evaluation (2026-10-02)

**The system:** four modules of the single-module design
(`SINGLE_MODULE_SUMMARY_2026-10-02.md`) on one output.
- 1 kW at 1 V, 16 phases. The module count follows P24 Table 1's row
  for 4 phases at IL_peak = 125 A.
- 4 × 4.672 mF output capacitance, a 1 mΩ load.

**The results come from two models that check each other:**
- **Co-simulation:**
  - a Verilog wrapper of four module controllers (one master, three
    slaves);
  - four circuit plants (datasheet nonlinear Coss, reverse conduction)
    whose output nodes are joined every 4 ns;
- **Averaged models:** D58-D61, D59's loop, D60's ladder, D61's
  sharing.

This closes the multi-module level. Each open point is given as cases,
with the value it rests on, for evaluation.

**Corrected 2026-10-03** after an external review (Section 7).

**Updated 2026-10-04 (Section 8):** the level restated for the final
single-module design (2.5 MHz with the Vin feed-forward), C05-C06.
Sections 1-7 describe the earlier A105 module (the 5 MHz design: period
232 ns at full load, 5% target) and stay as the record.
- **Soft switching:** the high side turns on at its valley (~9 V of the
  12 V rail), not at zero voltage. Only the low side switches at zero
  voltage.
- **Interleave accuracy:** the mean positions are within ±0.05 ns.
  Each switching cycle's spacing is less precise; Section 7 gives the
  numbers.

## 1. The system design

| part | what | where |
|---|---|---|
| module | A105's I2 unchanged (5% negative current, timed phase-1 turn-off, A103's start, PI 100 kHz) | single-module summary |
| voltage loop | one, on the master's ADC sample; its Ton broadcast to every module. The gains are the single module's (shared loop: M × gain and M × Co) | D61 (with its erratum), C01 |
| synchronisation | open-loop master-slave: slave m's phase 1 turns its low side off m T/16 after the master's, T the master's measured period (the CRM-PFC method of Huber et al. 2008) | C01, C02 |
| interleave | every slot referenced to phase 1's low-side turn-off (`slot_lo`), so all 16 low-side turn-offs are T/16 apart | C02 |
| current sharing | none beyond the common Ton (D61 scheme A): the modules share by their inductors, about 1/L | D61, C01, C03 |

## 2. Results (25 C)

| condition | result |
|---|---|
| four identical modules | each module equals the single module: load steps +11.4 / −14.6 mV (single +11.65 / −14.68), start-up 1.0131 V, valleys and V_DS within 0.02 A / 0.01 V |
| synchronisation | periods equal to 0.01 ns. The 16 low-side turn-offs: mean positions T/16 ± 0.05 ns in every condition without jitter. **Cycle by cycle:** steady state max 0.05-0.62 ns (sd ≤ 0.04 ns); with 30 / 100 ps jitter max 1.25 / 1.40 ns; in the 30 µs after a load or line step max 1.5-2.0 ns (sd ≤ 0.28 ns), of T/16 = 14.5 ns |
| output current ripple (16 phases) | **6.75 A rms**, 31 A pk-pk per period. With the original slot reference (C01): 45.9 A rms. Without module interleave: 114 A rms |
| standard matrix (16 rows: driver mismatch, jitter, load and line steps) | no overlap in 72 module-runs. Steps within 8% of the single module's. Peak ≤ 200 A except the +10% line step over 1 µs (207 A, as the single module) |
| inductor tolerance | ±5% → currents ±4.7%; one slave at +10% → −8.6%, its valleys −3.9 A. Its low side stays at zero voltage; its high side turns on at its valley, 9.38-9.62 V (nominal modules 8.9-9.1 V) |
| component spread | Cs ±20%: currents ±0.4%. R ±30%: ±1.3%. L ±5%, Cs ±20% and R ±30% together: −5.2% / +6.1%, every valley ≤ −5 A |
| input slew (single module, shared input) | peak ≤ 200 A from 2.4 V/µs; every valley negative only for rising inputs ≤ 0.24 V/µs. Falling inputs, even at 0.096 V/µs, leave the high-rail phases with positive valleys while the series capacitors re-divide |
| model agreement | D61's sharing law within 2.3 A per module (normalised). D59's step within 30%. D60's ladder relaxation explains the line-slew behaviour; the size of the per-phase current split during ladder motion is not yet derived |

## 3. Where the system differs from P24, or P24 is silent

1. **Interleave (corrected).**
   - P24: modules and phases interleaved to reduce the output ripple.
   - The single-module slot reference (A93/A97) put phase 1 one valley
     delay (9.44 ns) early. This was invisible at 4 phases (N·D = 0.31)
     but cost ×7 in ripple at 16 phases (N·D = 1.22).
   - **Corrected in C02.**
2. **Sharing method.** P24 calls sharing "the primary challenge" and
   gives no method. Ours is the common Ton, so sharing follows the
   inductor tolerance. **PROJECT_DECISION.**
3. **Controller, synchronisation, start-up.** P24 describes none. Ours
   follow the CRM-PFC interleaving literature (Huber et al. 2008-2009;
   Liu, Huang, Lee 2016: open-loop interleaving is preferred at MHz).
   **PROJECT_DECISION.**
4. **Carried from the single module:**
   - boundary mode with 5% negative current (P24's 1-2% does not give
     zero voltage, D57);
   - Eq. (4)'s 1.47 nH against Table I's 2.68 nH;
   - the inherited 4.672 mF per module.

## 4. Choices for evaluation

| choice | cases | rests on |
|---|---|---|
| **current sharing** | **Common Ton (chosen):** ±4.7% for ±5% L, ±8.6% for +10% L, plus ~±1% for ±30% R; no extra hardware. **A per-module trim:** it cannot be built on slot timing (A109: no authority). It needs a per-module current measurement acting on Ton or i_neg, which moves the interleave or the negative-current margin (D61) | inductor tolerance (assumed ±5-10%); the thermal limit of a module carrying +5-9% |
| **bus slew the system must ride** | ≥ 2.4 V/µs per 10%: peak above 200 A. 0.24-2.4 V/µs: within 200 A, but some phases' valleys go positive for ~2-20 µs (a hard high-side turn-on at up to 18.8 V instead of the ~9 V valley). Slower rising: valleys stay negative. Falling down to 0.096 V/µs: high-rail phases' valleys go positive while the ladder re-divides | the 48 V bus's real slew (bulk capacitance; unknown) |
| **negative valleys (valley turn-on) during ladder motion** | **accept** the short loss (chosen for now); **per-phase boundary turn-off** during transients (the interleave slides); **active series-capacitor balancing**; **slew shaping** | how often line transients occur; their loss in D62's terms |
| **Ton resolution** | the 31.25 ps Ton step moves Vo ~1.8 mV against a 0.5 mV ADC, so Ton may toggle (a 0.5 mV limit cycle, whether it appears depends on the equilibrium). A dyadic DPWM (Crovetti et al. 2020) adds 2-3 bits | the ADC resolution; the 31.25 ps timing step |
| **slave reference** | the master's low-side turn-off, as now: rare late fires (< 0.2 ns) in slave 1 while the master's turn-off is learning. A predicted reference (last turn-off + period, Zhou et al. 2024) gives a period of margin | timing latency of the master's TDC report |

## 5. Not in this level

- **Coss spread between modules** (needs a scale on the datasheet
  curve); **per-module driver delay** (needs a bridge key).
- **A module joining a running system** (pre-bias); **shedding modules
  at light load** (Cousineau et al. 2021).
- **Impedance between modules** (PDN), **thermal**, protection.
- **Time stamps for late fires** (they are counted, not timed).
- **The derivation of the per-phase current split during ladder
  motion.**

## 6. Evidence

- **Experiments:** `experiments/track_C_multi_module/` (C01-C04; README
  with the P24 consistency table; LITERATURE.md with the sources and
  DOIs) and `experiments/track_A_periodic_steady_state/` (A108, A109).
- **Derivations:** `symbolic_derivations/03_P24_native/` (D58-D62).
- **Running status:** `reports/CURRENT_STATUS.md` (items 30-35; the
  final design: item 51, C05-C06).

## 7. Corrections after the external review (2026-10-03)

| # | the review's point | checked | what changed |
|---|---|---|---|
| 1 | "zero voltage kept" read as high-side ZVS | true: high-side turn-on 8.91-9.07 V (n0), up to 9.62 V (slave at +10% L) | wording here and in C03 / C04 / A108 (errata). The high side turns on at its valley; only the low side is at zero voltage |
| 2 | ±0.05 ns is the mean position, not each cycle | true: max 0.58 ns (n0), 1.97 ns after the +250 A step | numbers above. New `matrix.gaps_per_cycle` (tested on C03 n0). C02 / C03 / C04 errata |
| 3 | `step_stats` called a never-recovered trace recovered | true: a trace stuck at 0.98 V gave 29.9 µs | it now returns inf when the trace ends outside the band (tested). Every existing value is unchanged: all recovered |
| 4 | the output join used the plain mean for any Co | true (all runs so far had equal Co) | `plant.join_nodes`: the Co-weighted mean, the plain mean when equal (bit-identical; tested) |
| 5 | an analysis script that runs is not a gate | true: false criteria only printed, missing runs skipped | `scripts/acceptance.py`: every registered criterion is PASS, DOCUMENTED (listed with its RESULTS section) or FAIL; missing runs and outdated exceptions fail. Now: C01-C04, A108, A109 ACCEPTED, 43 documented misses, 0 unexplained |

**What may be said:**
- A four-module co-simulation runs and reproduces.
- The modules stay locked and interleaved. Mean spacing is within
  0.05 ns, each cycle within 0.6 ns in steady state and 2 ns through
  load and line steps.
- This holds under C04's component spread (C07), with the floor on.
- The low sides switch at zero voltage. The high sides turn on at their
  valleys, ~9 V, as in the single module, and hard during fast line
  transients.

**What may not be said:**
- "All switches ZVS";
- "±0.05 ns throughout".

## 8. The final design on four modules (2026-10-04, C05-C06)

**The module:** A124's 2.5 MHz design (L 2.933 nH, Cs 6 µF, target
−15.6 A = 12.5%, floor 2 A, loop fc 100 kHz) with A129's gated Vin
feed-forward. Four of them, 16 phases, 1 kW. Each configuration is the
single module's plus `"modules": 4`; T/16 is 31.6 ns (A105's: 14.5 ns, so
the module spacing is wider now, not narrower).

**C05: "×4" held except in the start-up transient.**
- Steady state, all load steps, all line steps and the larger-L slave
  rows passed as the single module does.
- m1n, m3n (driver mismatch −1 / −3.4 ns) and j100 (100 ps jitter)
  failed: 203-250 A, 100-339 late fires per module, and an overlap in
  j100.
- **Cause:** a slave's phase 1 is slot-timed from the master and has no
  current-decided turn-off, so its valley is not regulated. After the
  handover (144 µs) a slave's valley ran to −96 A (m1n) and −130 A (j100).
  The slave then sank current, the master's loop raised Ton to its cap,
  the period grew, and the valley went deeper: positive feedback. Two
  modules recover on their own. All failures ended by ~260 µs.

**C06: the slave floor (one RTL addition, cfg `slave_floor`).**
- A118's floor on a slave's phase 1: its front end is armed in LOW at
  the target − 2 A; a crossing before the slot is the turn-off. Off, the
  code reproduces C05 bit for bit (unit tests 64/64).
- **All 18 rows:** no overlap, peak ≤ 185 A, locked, mean gaps T/16
  ± 0.05 ns. m1n 166-184 A, m3n 164-166 A, j100 163-164 A.
- **Steady state (n0):**
  - valleys −15.7 to −16.4 A;
  - low-side turn-on V_DS ≤ −1.0 V (zero voltage);
  - high-side turn-on at 3.3-3.9 V. At 12.5% this is much softer than
    A105's 5% design's ~9 V, but it is not zero.
  - output ripple 6.9 A rms (27.7 A pk-pk on 1002 A);
  - each cycle's spacing within 0.05 ns (j30 0.57, j100 2.2 ns).
- **Larger-L slave:**
  - at +10% L: −8.8% current, valley −13.6 A, low side −0.74 V,
    high side +0.6-0.7 V;
  - at +5% L: −4.6% current.
- **Adopted with three residuals** (decided against the registered rule
  that required criterion 6):
  1. late fires in the post-handover transient only: m1n 19, m3n 68 in
     total (the single module 1 / 5);
  2. l_m48_1us (−4.8 V / 1 µs): Vo +17.9 mV (single +15.7), back within
     1% at 11.1 µs (single 5.9 µs);
  3. the per-cycle spacing through steps (see below).

**Per-cycle spacing through steps is a property of the final design.**
- Even without the floor (C05), load and line steps move single cycles
  by up to ~35 ns (about one slot): Ton moves per phase with the
  feed-forward, and the period changes fast. A105's design (C03)
  stayed within 2 ns.
- The floor enlarges this in line steps: up to 65 ns in l_p48_1us.
- Every row is back below 0.5 ns within 100-150 µs. No overlap or peak
  limit is touched.

**Module component spread (C07, floor on):**
- Cs ±20%, R ±30%, L +5% (module 1 one way, module 3 the other): no
  overlap, peak ≤ 193 A, locked, gaps T/16 ± 0.1 ns. R ±30% moves slave
  valleys −1.6 / +1.7 A and sharing ∓1.3% (the C04 mechanism).
- In steady state the floor stays out of the way (floor on / off
  valleys within 0.03-0.053 A, gaps 0.016 ns); with it off the same rows
  peak at 263-265 A, so it must stay on.

**What may be said (final design):**
- Four modules of the final design run in co-simulation, locked and
  uniformly interleaved in steady state, with the standard matrix's
  hard limits met. This needs one RTL addition: the slave floor.
- The low sides switch at zero voltage. The high sides turn on at
  3-4 V.

**What may not be said:**
- "each cycle within 2 ns through steps" (true only for A105's
  design);
- "identical to the single module in transients" (late fires and
  l_m48_1us differ, see the residuals);
- "all switches ZVS".

