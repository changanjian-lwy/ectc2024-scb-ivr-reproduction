# C01 - four modules (1 kW, 16 phases): the baseline system (BOUNDARY)

Track C. **Written before any C01 run.** The framework is committed:
C1-C3, 798fd45.

## 1. Question

Does the single-module design (A105's I2), as M = 4 modules on one
output, give the multi-module behaviour D61 predicts?
- equal periods (locked interleave);
- current sharing set by the inductor tolerance;
- the single module's step response;
- every module still switching soft.

## 2. The system (P24 consistency: `../README.md` Section 2)

| point | here | P24 | tag |
|---|---|---|---|
| modules | 4 × 250 W, 1 kW, 1 V | Table 1, nP = 4, nM = 4 (IL_peak 125 A) | P24_EXPLICIT |
| one output | Co 4 × 4.672 mF, load 1 mΩ (4 × 4 mΩ shares) | parallel modules into one output capacitor | consistent (Co inherited, flagged) |
| equal frequency and duty for all high sides | one Ton (the master's PI, broadcast); the slaves' periods follow the master | "all high-side switches have the same fsw and D" | consistent |
| interleave | slave m's phase-1 low-side turn-off at t_ref + m T/16 (t_ref: the master's phase-1 turn-on); each module's phases 2-4 at T/4 from its own phase 1 (A97) | "interleaved phases and modules"; no shift given | PROJECT_DECISION (uniform 16-phase) |
| sharing | none beyond equal Ton | "the primary challenge"; no method | PROJECT_DECISION (D61's baseline) |

**Flagged deviation: phase 1 of each module is offset by the predicted
valley delay.**
- Phases 2-4 (and the slaves' phase 1) are placed by their low-side
  turn-off. The master's phase 1 is the reference by its high-side
  turn-on.
- So in low-side-turn-off terms, the master's phase 1 sits ~9 ns
  (dt_pred, 4% of T) early against a uniform 16-phase spacing. The
  single-module design (A93/A97) has had the same offset between phase 1
  and phases 2-4.
- Not corrected here: correcting it changes every earlier single-module
  result. It is measured.

## 3. Physical model

- Verilog RTL: four `scb_ctrl` instances in `scb_multi`, 0 the master
  and 1-3 slaves.
- Four single-module plants (A88's, kernel2), each with its Co and load
  share. Their output nodes are joined by charge conservation every 4 ns.
- A105's I2:
  - timed phase-1 turn-off on the master;
  - the master's PI at 100 kHz, Ton broadcast;
  - A103's start (load from 0, handover at 72 µs, mode S Ton 17.75 ns).
- 5%, 25 C.

| run | case | to |
|---|---|---|
| m4_n0 | identical modules, n0 | 500 µs |
| m4_L5 | inductors +5% / 0 / 0 / −5% | 500 µs |
| m4_j30 | 30 ps on every edge (each module its own seed) | 500 µs |
| m4_s_m250, m4_s_p250 | system load step ∓250 A (∓62.5 A per module) at 400 µs | 600 µs |

## 4. Registered predictions and criteria (last 200 master periods unless stated)

1. **No overlap in any module.** Peak current ≤ 200 A. The output join's
   largest difference is ≤ 0.1 mV.
2. **Locked periods:** every slave's mean period equals the master's
   within 0.1 ns.
   - Slave m's phase-1 low-side turn-off lies at m T/16 after the
     master's turn-on, within one 31.25 ps LSB plus the slot's rounding.
   - Its high-side turn-on is one predicted valley delay later.
3. **Sharing** (module current = the mean of its phases' (valley + peak)
   / 2):
   - m4_n0: the four modules within ±1%.
   - m4_L5 (D61, equal Ton): 236.9 / 250 / 250 / 264.5 A, within ±3 A
     each.
4. **Each module like the single module** (A105 i2 n0):
   - valleys −5.8 to −7.0 A;
   - high-side turn-on 8.9-9.1 V;
   - low-side turn-on V_DS ≤ 0;
   - a slave's phase 1 within the same bands.
   - m4_j30: phases' turn-off sd within A105 i2 j30's (0.48-0.53 A)
     ×(1 ± 0.3).
5. **Vo:**
   - 1.000 V ± 1 mV;
   - steps (D59 per module): −250 A → +15.5 mV, +250 A → −15.9 mV, each
     within ±30%;
   - start-up peak ≤ 1.05 V.

## 5. What stays assumed

- **Identical controllers and ADCs:** one ADC, the master's.
- **No PDN between modules:** one node.
- **Input source:** ideal and shared.
- **25 C.**
