# C01 - four modules (1 kW, 16 phases): the baseline system (RESULTS)

Track C, the first multi-module experiment. One factor against A105:
the module count (1 → 4), with D61's baseline A (one shared loop, one
Ton, slot-synchronised slaves).

**Boundary:** `BOUNDARY.md`, committed (592a13a) before any run. Every
run records that commit with the co-simulation sources unmodified.

**Records:**
- `cosim/run_*.json` and `cfg_*.json`;
- `c01_summary.json` (`c01_analyze.py`, on the shared
  `scb_ivr.cosim.matrix`).

**Models:**
- **Physical:**
  - Verilog RTL `scb_multi`: four `scb_ctrl`, 0 the master, 1-3 slaves.
  - Four A88 plants (kernel2), each with 4.672 mF and a 4 mΩ load share.
    Their output nodes are joined every 4 ns.
  - A105's I2:
    - timed phase-1 turn-off on the master;
    - A103's start;
    - the master's PI at 100 kHz, Ton broadcast.
  - 5%, 25 C.
- **Mathematical:** D61 (sharing), D59 (steps).
- **Reference:** A105 i2 (one module, the same design).

## 0. Verdict

1. **The four-module system works as D61's baseline predicts.**
   - Every registered criterion passes except one: the sharing check
     as literally registered (Section 1, item 3). It passes once its
     metric's known scale error is removed.
   - Periods lock exactly. Every slave's phase 1 sits on its slot to the
     LSB.
   - Inductor tolerance gives the D61 sharing (±4.7% for ±5% L), with
     no drift.
2. **Four identical modules behave as one module, ×4, in everything
   measured except the output ripple.**
   - Load steps: +11.4 / −14.6 mV vs A105's +11.65 / −14.68 mV.
   - Start-up peak 1.0131 V (the same).
   - Valleys and high-side turn-on V_DS: within 0.02 A and 0.01 V of
     A105.
   - So the single-module conclusions carry over, as D61's corrected
     shared-loop analysis said: the crossover is unchanged.
3. **Flagged deviation: the 16-phase interleave is not uniform, and
   most of P24's ripple cancellation is lost** (Section 2).

   | 16-phase placement (m4_n0, the same recorded waveforms re-placed) | output current pk-pk | ac rms |
   |---|---|---|
   | no interleave between modules (4 single modules aligned) | 427.0 A | 113.6 A |
   | **actual (C01)** | **162.8 A** | **45.9 A** |
   | slaves anchored to the master's phase-1 low-side turn-off | 120.7 A | 40.6 A |
   | uniform T/16 grid (also phase 1 inside each module) | 31.3 A | 6.6 A |

   - **Cause:** inside each module, phases 2-4 are slotted from phase 1's
     high-side turn-on (A93/A97), but phase 1's low-side turn-off is one
     valley delay (dt_pred, 9.44 ns, 4% of T) earlier. So phase 1 sits
     9.44 ns early.
   - **Single module:** the cost is small (4-phase ripple 122.4 vs
     100.9 A pk-pk; N·D = 0.31).
   - **16 phases:** N·D = 1.22, near the cancellation point, so the same
     offset costs ×7 in rms ripple.
   - Registered as a known offset in BOUNDARY Section 2; its size was not
     predicted.
4. **The slaves' valleys are not regulated.** This is a mechanism D61
   did not assume (Section 3).
   - Only the master's phase 1 is boundary-timed. The slaves are
     slot-timed followers, and their valleys settle where the shared Ton
     and period put them.
   - At ±5% L, a nominal slave's valleys move 1 A deeper; the −5% slave's
     move 2 A deeper.
   - This changes how D61's scheme B (i_neg trim) would have to work on a
     slave.

## 1. Registered criteria (BOUNDARY Section 4; last 200 master periods, before the step for step runs)

| # | criterion | result | verdict |
|---|---|---|---|
| 1 | no overlap; peak ≤ 200 A; join ≤ 0.1 mV | 0 overlaps in 20 module-runs; peaks 165-176 A; join max 67-78 µV | pass |
| 2 | slaves' periods = master's within 0.1 ns | equal to 0.01 ns in every run | pass |
| 2 | slave m's phase-1 low-side turn-off at m T/16 | 14.50 / 29.00 / 43.50 ns (n0; targets the same); j30 sd 0.05-0.08 ns; L5 within 0.01 ns of its own T/16 | pass |
| 2 | its high-side turn-on one predicted valley delay later | +9.44 ns (n0: 23.94 / 38.44 / 52.94 ns) | pass |
| 3 | m4_n0 sharing within ±1% | 250.1 A each (identical) | pass |
| 3 | m4_L5 = 236.9 / 250 / 250 / 264.5 A ± 3 A | registered metric: 243.5 / 254.6 / 254.6 / 266.8 A → **MISS** as written. Normalised to the load (Section 3): 238.4 / 249.6 / 249.8 / 262.2 A, within 2.3 A | **miss as registered; pass normalised** |
| 4 | each module like A105 i2 n0: valleys −5.8 to −7.0 A, high-side on 8.9-9.1 V, low-side on ≤ 0 | n0 and steps, all modules: −5.84 to −6.92 A, 8.91-9.07 V, ≤ −0.95 V | pass |
| 4 | m4_j30 turn-off sd within 0.48-0.53 A × (1 ± 0.3) | 0.44-0.60 A, all modules and phases | pass |
| 5 | Vo 1.000 V ± 1 mV | 1.0000-1.0002 V | pass |
| 5 | steps (D59): −250 A → +15.5 mV, +250 A → −15.9 mV, ±30% | +11.4 mV (0.74 of D59), −14.6 mV (0.92) | pass (the −250 A step at the edge) |
| 5 | start-up peak ≤ 1.05 V | 1.0131-1.0134 V | pass |

**Why the m4_L5 check misses as written.**
- The registered module current, the mean of the phases' (valley +
  peak) / 2, reads 255.2 A per 250 A module in m4_n0 (+2.1%). That
  shifts every m4_L5 value up by ~5 A.
- I registered D61's absolute numbers against that metric without
  checking its scale on n0 first. The ratios are what D61 predicts, and
  they agree (next section).

**Outside the registered bands, as expected:**
- **m4_L5's slaves:** valleys −6.8 to −8.9 A, high-side on 8.39-8.75 V.
  This is the unregulated-valley mechanism, Section 3.
- **m4_j30's low-side turn-on V_DS:** up to +0.59 V (slave 3, phase 4),
  against +0.07 to +0.30 V in A105's j30. A105 graded j30 by its spread,
  and so does this analysis: the ≤ 0 check is applied to n0, L5 and the
  steps.

## 2. The interleave (flagged deviation)

**Low-side turn-off of all 16 phases** (m4_n0, ns after the master's
phase-1 high-side turn-on; T = 232.02 ns, T/16 = 14.50 ns):

| module | phase 1 | phase 2 | phase 3 | phase 4 |
|---|---|---|---|---|
| 0 (master) | 222.58 (= −9.44) | 58.00 | 116.00 | 174.00 |
| 1 | 14.50 | 81.94 | 139.94 | 197.94 |
| 2 | 29.00 | 96.44 | 154.44 | 212.44 |
| 3 | 43.50 | 110.94 | 168.94 | 226.94 |

- **The gaps range from 4.4 to 23.9 ns** against a uniform 14.5 ns.
- **Two offsets add up:**
  1. **In every module:** phase k's slot (k = 2-4) is t_ref + (k − 1)
     T/4, where t_ref is phase 1's high-side turn-on. Phase 1's own
     low-side turn-off is dt_pred (9.44 ns) before t_ref. This is the
     single-module design since A93/A97.
  2. **Across modules:** slave m's phase-1 low-side turn-off is at
     t_ref + m T/16. Its phases 2-4 follow its own high-side turn-on, so
     they sit +9.44 ns off the 16-phase grid. The master's phases 2-4
     sit on it.

**The ripple numbers in Section 0** re-place the recorded waveforms
(piecewise-linear between each phase's low-side turn-off, high-side
turn-on and high-side turn-off) and sum all 16.
- **Assumption:** the waveforms do not change when moved. A
  co-simulation with the corrected placement must confirm it.
- **The ideal** (16 copies of phase 2's waveform at T/16) gives 18.1 A
  pk-pk. The remaining difference to 31.3 A is the phases' unequal
  waveforms (phase 4's valley is 1 A shallower).

**Correction, in two parts** (the next experiment, C02, one factor: the
interleave reference):
- **System layer:** reference the slaves to the master's phase-1
  low-side turn-off: ext_slot = t_ref − dt_pred(master, phase 1) +
  m T/16. The module does not change. Ripple 162.8 → 120.7 A pk-pk.
- **Module layer:** slot phases 2-4 from phase 1's low-side turn-off,
  t_ref − dt_pred(phase 1) + (k − 1) T/4.
  - It is a new opt-in RTL setting; the A93/A97 placement stays the
    default, so earlier runs are bit-identical.
  - It moves phases 2-4 9.44 ns earlier relative to phase 1. The slot
    guard and the zero-voltage timing must be re-checked in a single
    module first.
  - With both parts: 31.3 A pk-pk, 6.6 A rms.

## 3. Sharing and the slaves' valleys (added after the runs)

**Module current from the piecewise-linear waveforms:**
- The four modules sum to 983 A for a 1000 A load (−1.7%). The
  transitions are drawn as straight lines.
- So each module's value is normalised so the four sum to Vo / 1 mΩ.

| run | module | L | current (normalised) | D61 | valleys (A, phases 1-4) | dt_pred, phase 1 |
|---|---|---|---|---|---|---|
| m4_n0 | 0-3 | nominal | 250.1 | 250 | −6.30 / −6.91 / −6.92 / −5.84 | 9.44 ns |
| m4_L5 | 0 (master) | +5% | 238.4 | 236.9 | −6.29 / −6.86 / −6.87 / −5.84 | 9.63 ns |
| m4_L5 | 1, 2 | nominal | 249.6, 249.8 | 250 | −7.25 / −7.85 / −7.86 / −6.82 | 9.19 ns |
| m4_L5 | 3 | −5% | 262.2 | 264.5 | −8.29 / −8.94 / −8.94 / −7.87 | 8.78 ns |

- **Sharing:**
  - Spread 9.5% of the mean, against D61's 11.0%.
  - The +5% module carries −4.6% (D61 −5.3%); the −5% module +4.9%
    (D61 +5.8%).
  - The nominal slaves keep exactly their n0 current.
- **Valleys (D61 assumed every module's valley fixed at −i_neg):**
  - **The master:** its phase 1 is boundary-timed (timed turn-off with
    the learned target). Its valleys stay at n0's to 0.05 A even at +5%
    L.
  - **The slaves:** every phase is slot-timed from the master's
    reference. The valleys are set by the shared Ton (571, up 3 LSB
    from n0) and period (234.13 ns), and the module's own L.
    - Nominal slaves: 1 A deeper.
    - The −5% slave: 2 A deeper. More zero-voltage margin.
  - **The risk is the other direction:** a slave with a larger L gets a
    shallower valley, which D61 already flagged at +6%. In C01 the +5%
    inductor sat on the master, where the valley is regulated.
- **Consequences:**
  - The measured spread is a little smaller than D61's, because each
    slave's deeper valley offsets part of its 1/L current.
  - **D61 scheme B (i_neg trim) cannot act on a slave as written:** a
    slave has no valley target. It would need either a per-slave valley
    loop or a trim of the slave's slot.
  - Not tested here.

**Ton dither:**
- m4_n0 holds Ton at 568 with Vo 1.00024 V (inside the ADC's zero bin,
  ±0.25 mV). So the turn-off sd is 0.02 A.
- A105 i2 n0 toggles 567/568 (Vo pk-pk 0.51 mV, sd 0.16 A).
- Whether the equilibrium falls inside the zero bin is the
  Peterson-Erickson condition and depends on 0.1 mV-level details. It
  is not a multi-module property.

## 4. Consistency with P24 (updated from `../README.md` Section 2)

| point | P24 | C01 | tag |
|---|---|---|---|
| parallel modules, one output, 1 kW | Sec. III-B, Fig. 3; Table 1 nM = 4 | 4 × 250 W, joined output, 1000 A | P24_EXPLICIT, met |
| same fsw and D on all high sides | Sec. III-B | one Ton, periods equal to 0.01 ns | consistent, met |
| interleaved phases and modules to reduce output ripple | Sec. III-B | interleaved, but not uniformly: gaps 4.4-23.9 ns for 14.5 ns; ripple 45.9 A rms against 6.6 A uniform | **DEVIATION (ours, from A93/A97's slot reference).** Correction in C02 |
| current sharing "the primary challenge" | Sec. III-B | ±4.7% for ±5% L, stable; no method in P24 | PROJECT_DECISION (D61 scheme A), met |
| fixed Ton, CCM/DCM boundary | Sec. III | boundary mode with 5% negative current, period follows Ton | DEVIATION carried from the single module (README Section 2) |

## 5. What stays assumed

- Identical controllers.
- One output node, no PDN between modules.
- An ideal shared input.
- 25 C.
- Co inherited (4.672 mF per module).
- Unchanged from BOUNDARY Section 5.

## 6. Next

- **C02: the uniform interleave** (the flagged deviation).
  - First the module layer in one module: phases 2-4 slotted from phase
    1's low-side turn-off, an opt-in RTL setting. Gates: the default is
    bit-identical; A105 i2 n0's checks re-run.
  - Then the system layer: slaves anchored to the master's low-side
    turn-off.
  - Prediction: the 16-phase output current ripple falls from 45.9 to
    ~6.6 A rms.
- **C03: the four-module standard matrix.** Driver mismatch, j100, line
  steps, +5% L on a slave.
- **Later:**
  - a system start-up with the Cs-scaled ramp;
  - input feed-forward for fast line steps (A106/A107);
  - the slave-valley question for sharing scheme B.
