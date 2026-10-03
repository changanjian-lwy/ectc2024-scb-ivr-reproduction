# A116 - the 1 MHz 10% design's transients (RESULTS)

Track A, main line. One factor: the controller variant: loop 60 / 30 kHz
× phase 1's turn-off timed / comparator.

**Boundary:** `BOUNDARY.md`, committed (3647264) before any run.

**Records:**
- `cosim/run_*.json`, `cfg_*.json`;
- `a116_predictions.json`;
- `a116_summary.json` (`a116_analyze.py`).

**Physical model:** as A115 (Verilog RTL, A88 kernel2 plant, 7.333 nH,
Cs 15 µF, 10% negative current, 25 C).

## 0. Verdict

| variant | n0 | −62.5 A | +62.5 A | −4.8 V / 1 µs | +4.8 V / 1 µs |
|---|---|---|---|---|---|
| t60 (A115: timed, 60 kHz) | pass | **runaway** (554 A) | −19.9 mV, 14 µs | **runaway** (495 A) | **runaway** (546 A) |
| t30 (timed, 30 kHz) | pass | −36.4 mV (a dip), **200 µs**; valleys to −54 A | −29.9 mV, 98 µs | **238 A**; ±18 mV limit cycle to the end | **233 A**, 74 µs |
| **c60 (comparator, 60 kHz)** | pass (sd 0.12 A) | **+28.0 mV, 16 µs** | **−28.6 mV, 22 µs** | +94 mV, 44 µs, **206 A** | **341 A**, −129 mV, 52 µs |
| c30 (comparator, 30 kHz) | pass | +47.3 mV, 52 µs | −48.2 mV, 80 µs | +125 mV, 98 µs, **212 A** | **312 A**, −229 mV, 91 µs |

**Bold** marks a hard-constraint miss or the best entry. No overlap in
any of the 17 runs.

1. **H1 holds; H2 is falsified.** The runaway's trigger is the valley
   crossing the zero-voltage threshold, not the loop's speed.
   - With the 30 kHz loop the timed design's valleys still fall to
     −47 to −54 A after the load decrease, far past 14.9 A.
   - It does not run away, but it oscillates slowly: back within 1% in
     200 µs. That is A112's 25% behaviour at 5 MHz (183 µs).
   - So the loop's speed only decides between a runaway (60 kHz) and a
     slow oscillation (30 kHz).
2. **The comparator turn-off fixes the load steps at 1 MHz.**
   - **Phase 1's valley:** held within −12.7 to −12.2 A after both
     steps.
   - **The slotted phases** stay within −18.2 to −6.4 A. After the load
     increase phase 4 passes the threshold by ~3 A for a few periods
     without a breakdown. A short, shallow crossing is tolerated; t30's
     −54 A is not.
   - **c60:** +28.0 / −28.6 mV, back in 16 / 22 µs; peaks 158 / 176 A.
   - **Steady state unchanged** (efficiency 88.97 against 88.98%). The
     high side turns on 0.08 V lower. The turn-off sd is 0.11-0.12 A
     (timed: 0.00).
3. **With the comparator, D59 is exact; the registered bands were
   wrong.**
   - D59: +27.6 / −28.8 mV (60 kHz) and +45.6 / −47.0 mV (30 kHz).
   - Measured: +28.0 / −28.6 and +47.3 / −48.2. All within 4%.
   - **The registered bands** (0.7 × D59) carried over A115's timed
     factor, and miss for that reason. The 0.7 belongs to the timed
     turn-off. In a transient its learned interval is frozen, so phase
     1's valley (and the slots') moves with Ton. The current per unit
     Ton is then larger than D59's boundary-mode gain, which gives
     smaller extremes.
   - **This explains A115's "D59 over-predicts by 30%".**
4. **Every variant fails the ±4.8 V / 1 µs line steps at 1 MHz.** The
   best is c60: both recover in ≤ 52 µs, but peak at 341 A (rising) and
   206 A (falling).

   **Mechanism (t60_l_p48_1us traced):**
   - **The ladder lags the input:** V_Cs1 35.7 → 39.4 V over ~15 µs.
     D60's τ ∝ Cs, and Cs is 5× A105's.
   - So phase 1's rail takes the step:
     - phase 1's valley goes positive (+43 to +84 A, hard turn-ons);
     - the slotted phases' valleys fall to −59 to −93 A, past the
       threshold. The node clamps and the timing breaks down.
   - The 60 kHz loop then runs away.
   - **With the comparator:**
     - **falling:** phase 1 holds (−12.7 to −12.3 A), but the slotted
       phases swing from −41 to +120 A;
     - **rising:** phase 1 stretches. Its turn-off is forced by the
       2 µs restart timer at up to +71 A, and the slotted phases swing
       from −171 to +65 A.
     - This is A114's mechanism.
   - **At 5 MHz** the 5% design's worst line-step peak was 207 A (A106).
     At 1 MHz the margin is smaller (2.4 against 27 A) and the ladder 5×
     slower.
5. **The margin moves with the input** (D57: I_th 13.45 / 14.90 /
   16.32 A at 43.2 / 48 / 52.8 V).
   - After the −4.8 V step the timed design (t30) settles at 43.2 V, a
     margin of 0.95 A, into a ±18 mV limit cycle until the run ends.
     This is A115's 12.5% oscillation.
   - The comparator design at the same point settles to 0.1 mV.
   - **So the timed turn-off needs a margin of more than ~1 A at the
     lowest operating input; the comparator turn-off does not.**

## 1. Registered criteria (BOUNDARY Section 2)

| row | t60 | t30 | c60 | c30 |
|---|---|---|---|---|
| n0 (high side ±0.2 V, efficiency ±0.1, ripple ±1 A, Vo, late, c: phase 1 valley ±1 A) | (A115) | pass | pass | pass |
| −62.5 A: band, back, peak | (A115: runaway) | **band miss** (−36.4 mV, a dip, against +32 ± 10); **back 200 µs > 60**; peak pass | **band miss** (+28.0 against 19 ± 6: D59 exact); back 16 µs pass; phase 1 ±3 A pass | **band miss** (+47.3 against 32 ± 10: D59 exact); back 52 µs pass; phase 1 pass |
| +62.5 A: band, peak | (A115) | pass (−29.9 against −33 ± 10) | **band miss** (−28.6 against −20 ± 6: D59 exact) | **band miss** (−48.2 against −33 ± 10: D59 exact) |
| −4.8 V / 1 µs: peak ≤ 200 A, back ≤ 60 µs | **miss, miss** (runaway) | **miss** (238 A), **miss** (limit cycle) | **miss** (206 A), pass (44 µs) | **miss** (212 A), **miss** (98 µs) |
| +4.8 V / 1 µs, as registered: timed ≥ 207 A; comparator runs away (> 200 A) | as registered (546 A) | as registered (233 A) | as registered (341 A) | as registered (312 A) |

**H1 against H2** (t30_s_m62): the minimum valley after the step is
−53.6 A, below −15 A as H1 predicts, and recovery takes 200 µs. **H1.**

**The decision rule:** adopt the variant that passes n0, both load steps
and −4.8 V.
- **None passes strictly.**
- **c60 comes closest:**
  - n0 and both load steps meet every hard constraint, and their extremes
    are D59's;
  - −4.8 V recovers in 44 µs but peaks 6 A over the limit.
- **Provisional choice at 1 MHz: c60.** The line-step limit stays open.

## 2. What this answers, and next

**For the trade-off map** (`reports/TRADEOFF_SCORECARD.md`):
- **T12's mechanism is confirmed:** the trigger is the threshold
  crossing.
- **T13:** at 1 MHz the comparator turn-off is needed for load steps.
- **New:** the margin depends on the input, and the line steps depend on
  the ladder's speed, so on Cs (T15 at 1 MHz).

**Next, one factor each, on c60:**
1. **A117: the line-slew tolerance at 1 MHz** (A108's method). Find
   which slew the 200 A limit holds from, 1 to 20 µs per 4.8 V. If it is
   a slew a 48 V bus with bulk capacitance has anyway, the line-step
   limit is a specification, not a design gap.
2. **Then Cs at 1 MHz.** 3 µF instead of 15 µF makes the ladder 5×
   faster (D60: τ ∝ Cs), at the cost of Q/Cs ≈ 1.7 V (A107: ~1 V more
   high-side turn-on). That trades steady-state switching loss for line
   robustness.
