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
| synchronisation | periods equal to 0.01 ns; the 16 low-side turn-offs T/16 ± 0.05 ns in every condition without jitter |
| output current ripple (16 phases) | **6.75 A rms**, 31 A pk-pk per period. With the original slot reference (C01): 45.9 A rms. Without module interleave: 114 A rms |
| standard matrix (16 rows: driver mismatch, jitter, load and line steps) | no overlap in 72 module-runs. Steps within 8% of the single module's. Peak ≤ 200 A except the +10% line step over 1 µs (207 A, as the single module) |
| inductor tolerance | ±5% → currents ±4.7%; one slave at +10% → −8.6%, its valleys −3.9 A, zero voltage kept |
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
| **current sharing** | **Common Ton (chosen):** ±4.7% for ±5% L, ±8.6% for +10% L, plus ~±1% for ±30% R; no extra hardware. **A per-module trim:** it cannot be built on slot timing (A109: no authority). It needs a per-module current measurement acting on Ton or i_neg, which moves the interleave or the zero-voltage margin (D61) | inductor tolerance (assumed ±5-10%); the thermal limit of a module carrying +5-9% |
| **bus slew the system must ride** | ≥ 2.4 V/µs per 10%: peak above 200 A. 0.24-2.4 V/µs: within 200 A, zero-voltage turn-on lost on some phases for ~2-20 µs. Slower rising: soft. Falling down to 0.096 V/µs: high-rail phases lose zero voltage while the ladder re-divides | the 48 V bus's real slew (bulk capacitance; unknown) |
| **zero voltage during ladder motion** | **accept** the short loss (chosen for now); **per-phase boundary turn-off** during transients (the interleave slides); **active series-capacitor balancing**; **slew shaping** | how often line transients occur; their loss in D62's terms |
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
- **Running status:** `reports/CURRENT_STATUS.md` (items 30-35).
