# A117 - D63's design map at 1 MHz put to the co-simulation: input slew and Cs (RESULTS)

Track A, main line. Factors: the input slew, Cs (15 / 3 µF), phase 1's
turn-off (comparator / timed); 60 kHz loop; 1 MHz, 10%.

**Boundary:** `BOUNDARY.md`, committed (1f53a83) before any run.

**Records:**
- `cosim/run_*.json`, `cfg_*.json`;
- `a117_predictions.json` (D63, registered);
- `a117_summary.json` (`a117_analyze.py`).

## 0. Verdict

1. **D63's peaks hold. Its registered outcome rule is falsified.**
   - **Peaks:** within 10% in all 5 bounded rows: 286 / 286, 225 / 208,
     201 / 194, 174 / 175, 143 / 140 A.
   - **Outcomes:** 6 of the 10 reliable step rows miss the registered
     rule (falsified above 2).
     - **Three are knife-edge:** back in 61.6 µs against the 60 µs
       class limit; 78 µs with the peak right; 201 A against 200.
     - **Three are real:**
       - c15_tim_l_m48_50us: a phase-1 crossing of 9.5 A × 50 periods,
         no harm;
       - c3_tim_l_m48_10us: 23.5 A × 12, back in 13.7 µs;
       - c3_cmp_l_m48_1us: the map diverges; the co-simulation peaks at
         208 A and recovers in 32 µs.
   - **The 8 A threshold was too low.** On all 10 phase-1 crossings now
     co-simulated, "deeper than ~12 A for ~25 periods or more" separates
     the slow and runaway outcomes from the others. The exception is the
     timed 60 kHz design on 1 µs line steps, D63's known weak domain.
     - (8.6 × 27, 9.5 × 50, 23.5 × 12, 37 × 13 → ok; 13.5 × 46,
       17.3 × 44, 19.2 × 44, 32.1 × 29, 119 × 1313 → slow or runaway.)
     - **Fitted after the runs: to be registered and tested, not
       claimed.**
2. **Cs 3 µF rescues the line steps, but breaks the start-up.**
   - **Line steps:**
     - timed: +4.8 V / 1 µs 188 A, back in 7.6 µs; −4.8 V / 10 µs
       163 A, 13.7 µs;
     - comparator: +4.8 V / 20 µs 174 A; −4.8 V / 1 µs 208 A, 32 µs;
       −62.5 A +25.4 mV.
   - **But the handover to mode P oscillates for ~1.1 ms in every
     3 µF run** (identical up to the step):
     - currents to 517 A, Vo 0.95-1.07 V, ~1200 late fires;
     - the ladder swings 2-3 V per period.
     - **Mechanism:** mode S ends at Vo 1.070 V. The PI cuts Ton from
       88.8 to 45 ns at once, so the valleys pass the threshold. The
       5× faster ladder and the 60 kHz loop then oscillate with a
       ~15 µs period. It settles by ~1500 µs.
     - **D63 does not explain it** (checked after the runs).
       - From the handover's true state, its ladder near balance and Vo
         1.070 V, the map gives 149 A and no oscillation.
       - The sections sample C1 at its in-cycle low. At 3 µF that is
         ~1 V under the mean, the same in steady state (34.55 against
         34.77 V at the handover).
       - Fed those samples as the ladder, the map diverges, but for the
         wrong reason.
       - **The in-cycle ripple, which D63 does not model, is the likely
         cause. Open.**
   - **A fast rising step with the comparator also runs away**
     (+4.8 V / 5 µs: 282 A, 249 late fires, not recovered), as D63
     predicted.
   - **Steady state:**
     - the efficiency is unchanged (88.95 against 88.98%);
     - the in-cycle Cs ripple moves the turn-ons: phases 1 and 4
       +1.1 V, phases 2 and 3 −0.8 V (their valleys −16.1 A against
       −12.5 A);
     - registered: +0.5 to +1.5 V on every phase, a miss.
3. **With Cs 15 µF the slew decides:**
   - **comparator:**
     - falling reaches 200 A from 5 µs (201 A, 49 µs);
     - rising does not by 50 µs (225 A, back in 78 µs). As D63 says,
       the comparator's rising failure is not a fast-slew effect: phase
       1 stretches with its rail;
   - **timed:**
     - rising 10 µs: 231 A (D63 flagged here: 196);
     - falling 20 µs is slow (92 µs, phase 1 crossing as predicted);
       50 µs is fine.
4. **For the design** (with D63 and the trade-off map):
   - **No variant run so far meets everything at 1 MHz.**
   - **The pattern points to two changes, both suggested by the
     model:**
     - **the floor turn-off,** for the load decrease and falling steps
       of the timed design;
     - **an intermediate Cs, or a softer handover,** for the line
       steps without the 3 µF start-up.
   - D63's peak predictions are good enough to choose the Cs and the
     slew before running. Its outcome rule needs the refit above, and
     the co-simulation.

## 1. Rows (outcome after the step: peak from the high-side turn-offs after 2000 µs, late fires less the n0 row's)

| row | outcome (D63) | peak after (D63) | Vo extreme, back | phase 1 valleys after |
|---|---|---|---|---|
| c3_cmp_l_p48_5us | **runaway** (runaway) | 282 A (diverged) | −77.0 mV, not recovered; 249 late | −13 to −12 |
| c3_cmp_l_m48_1us | peak (**runaway**) | 208 A | −50.7 mV, 31.9 µs | −13 to −12 |
| c15_tim_l_m48_20us | slow (slow or runaway) | 179 (166) | −18.3 mV, 92.4 µs | −52 to −2 |
| c3_tim_l_m48_10us | ok (**slow or runaway**) | 163 (154) | −20.7 mV, 13.7 µs | −37 to −8 |
| c15_tim_l_m48_50us | ok (**slow or runaway**) | 148 (145) | −6.9 mV, 0 | −30 to −8 |
| c15_cmp_l_p48_20us | slow (peak) | **286 (286)** | −101.8 mV, 61.6 µs | −13 to +15 |
| c15_cmp_l_p48_50us | slow (peak) | 225 (208) | +71.3 mV, 78.1 µs | −13 to −12 |
| c15_cmp_l_m48_5us | peak (ok) | 201 (194) | +112.2 mV, 49.3 µs | −13 to −12 |
| c15_tim_l_p48_10us (flagged) | peak (ok) | 231 (196) | +8.3 mV, 0 | −41 to +67 |
| c3_tim_l_p48_1us (flagged) | ok (peak) | 188 (202) | +19.8 mV, 7.6 µs | −24 to +28 |
| c3_cmp_l_p48_20us | ok (ok) | **174 (175)** | −23.0 mV, 35.2 µs | −13 to −12 |
| c3_cmp_s_m62 | ok (ok) | 143 (140) | +25.4 mV (D63 +28.9: −12%, **miss**), 12.9 µs (16.5: pass) | −13 to −12 |

**n0 rows, Cs 3 µF:**

| row | high-side turn-on, phases 1-4 | shift against Cs 15 µF | efficiency | start-up peak |
|---|---|---|---|---|
| c3_tim_n0 | 3.07 / 0.68 / 0.71 / 2.11 V | +1.13 / −0.79 / −0.76 / +1.17 | 88.95% (88.98) | **517 A** |
| c3_cmp_n0 | 2.99 / 0.59 / 0.63 / 2.02 V | +1.13 / −0.79 / −0.76 / +1.18 | 88.94% (88.97) | **517 A** |

No overlap in any run.

## 2. Analysis note

**The registered outcome definitions use the peak and the late fires.**
- **The Cs 3 µF start-up** reaches 517 A with ~1210 late fires before
  any step, and identically in every 3 µF run.
- **So the outcomes are taken after the step:**
  - the peak from the high-side turn-off records after 2000 µs;
  - the late fires as the run's total less its n0 row's (the same
    configuration without the step, identical before it).
- The start-up is reported as its own finding (0.2).

## 3. Next

1. **Refit D63's outcome rule** (0.1) and register it for the next
   test.
2. **The 3 µF handover** needs the co-simulation (D63 cannot see it).
   - Try a handover at Vo ≈ 1.0 V (A103's rule: mode S's Ton at the
     loaded value).
   - Try a Cs between 3 and 15 µF.
3. **A118: the floor turn-off** (an RTL option), on the Cs D63 picks:
   load steps, line steps and the start-up.
