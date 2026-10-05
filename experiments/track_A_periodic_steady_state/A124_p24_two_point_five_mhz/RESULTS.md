# A124 - the 2.5 MHz design point (RESULTS)

Track A, main line.

**Design:** Eq. (4)'s 2.933 nH, Cs 6 µF, time-scaled ×2 from 5 MHz, D59
loop at 100 kHz, 2 A floor.

**Boundary:** `BOUNDARY.md`, committed (703aded) before any run.

**Records:**
- `cosim/run_*.json`, `cfg_*.json`;
- `a124_predictions.json`;
- `a124_summary.json` (`a124_analyze.py`).

## 0. Verdict

1. **2.5 MHz is the most efficient design measured in this project** (D62
   middle case), and its steady state is clean.

   | target | high side, phases 1-4 | efficiency, middle / ideal inductor | start-up |
   |---|---|---|---|
   | 10% | 5.39 / 5.18 / 5.18 / 4.88 V | 90.49 / 92.34% | 163 A |
   | **12.5%** | 3.93 / 3.70 / 3.71 / 3.26 V | **90.61 / 92.51%** | 163 A |
   | 15% | 2.45 / 2.20 / 2.21 / 1.59 V | 90.62 / 92.57% | 167 A |

   - **Against the others:** 5 MHz's best (20%) is 90.17%; the 1 MHz
     candidate 88.97%.
   - **Every steady-state criterion passes:** D57 within 0.35 V;
     period, Ton and peaks; efficiency +0.18 points over the prediction.
   - **The valley margin at 12.5% is 7.9 A,** 3× the 1 MHz design's.
2. **The load steps are as good as at 5 MHz:**
   - −62.5 A: +15.9 mV, 6.6 µs;
   - +62.5 A: −12.0 mV, 3.6 µs;
   - D63: +16.8 / −10.1 mV.
   - **The control without the floor recovers too** (+11.9 mV, 4.5 µs)
     although phase 1 reaches −40.4 A. That is the prospective test of
     D63's refitted crossing rule: it predicted 8.9 A × 30 periods,
     below 12 A, so recovery. **With this margin the floor is not
     needed for load steps.**
3. **Line steps:**
   - **falling ones pass:** −4.8 V / 5 µs 174 A, −8 V / 10 µs 169 A;
   - **rising ones do not:** +4.8 V / 5 µs **210 A**; the 1 µs steps 216
     / 218 A.
   - **The rising-step limit is common to every frequency:** 5 MHz 207 A
     (A106), 1 MHz 206 A, 2.5 MHz 218 A at 1 µs.
     - **Mechanism:** the ladder lags the input, so phase 1's rail takes
       the step.
     - **Its levers:** a faster ladder (smaller Cs; A123: −11 A), an
       input feed-forward to Ton (not built), or a bus slew
       specification.
4. **A registration error, recorded.** The floor-holds criterion
   (≥ −18.6 A) took the front end's delay as 1 A, the 1 MHz value.
   - At 2.5 MHz the low side's current falls at Vo/L = 0.34 A/ns, 2.5×
     faster. So the 11 ns of t_async + t_drv overshoot ~3.75 A.
   - Phase 1's floor turn-offs at −19.4 to −19.9 A are that physics. They
     are well inside the 23.6 A threshold. The miss is in the criterion,
     not the floor.

**Recommendation:**
- **2.5 MHz, 12.5% negative current, floor 2 A (optional at this
  margin), Cs 6 µF, 100 kHz loop.** It is the efficient and robust
  design for P24's in-package inductor scale (D64).
  - **Erratum (D67, 2026-10-05):** the comparison holds for D62's middle R/L (an MPC-class magnetic core, as in
    P24's package). With an air-core stripline in Fig. 5's 0.25-0.63 cm² per phase, D64 picks 5 MHz instead.
- **Open:** rising line steps faster than ~10 µs per 4.8 V. That is a
  bus specification, or a smaller Cs, or an input feed-forward.

## 1. Criteria (BOUNDARY Section 3)

| row | result |
|---|---|
| p10_n0, p125_n0, p15_n0 | all pass |
| p125_s_m62, p125_l_m48_5us, p125_l_m80_10us | pass except **floor_holds** (registration error, 0.4) |
| p125_s_p62 | pass |
| p125_l_p48_5us | **peak_200a miss** (210 A), floor_holds (registration error) |
| p125_l_p48_1us, p125_l_m48_1us | no overlap, no runaway; 218 / 216 A reported |
| t125_s_m62 (control) | **recovers** (D63's refitted rule, prospective) |
