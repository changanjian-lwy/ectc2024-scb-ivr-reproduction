# A247 - the soft turn-on window against the low-side turn-off current (D57 against the records) (BOUNDARY)
Method: math (D57's free node) + ML (GP on the residual, MLP classifier) on existing records; no new co-simulation.
Track A. Written and committed before the physics table, the extraction and the analysis. Looked at beforehand: the
records' field names and counts (A229-A246, 491 run files) and the timing of four free-node traces, no values.
Decision it changes: whether a delay set from the low-side turn-off current can replace the learned dt_pred on phases
2-4, how finely that current must be known (comparator levels, a hardware question), and whether D57 can be the physics
of D63's learner block (step 2).
Cheaper check done first: this is the cheapest step (records exist; D57 traces about 5 min at 10 jobs). Budget: ~45 min.

## 1. What and why
- dt_pred got six special-case rules in ten days (A236-A246). A survey of 15 papers (2026-10-25) found that on the
  edge that needs negative current, published controllers set the delay from a formula of measured V and I each period,
  or from an event, and never learn it from their own valley:
  - Nguyen, Liu, Chiu, IFEEC 2023 (TCM GaN buck, 60 -> 36 V, 200 W, 200-800 kHz, measured): eq. (15) from Vin, Vout, Iout.
  - Liu et al., IPEMC-ECCE Asia 2020 (CRM GaN totem-pole PFC, 1 kW, 0.3-1.2 MHz, measured): eq. (8).
  - Zhu et al., APEC 2021 (CRM GaN totem-pole PFC, 500 W, MHz, measured): eq. (2), a resonance formula.
  - Hu et al., Electronics 2023 (90 V, 20 MHz GaN driver, simulated): T = C dV / I, in analog.
  - The learning loops (Ke & Ma, APEC 2021; Cai et al., TPEL 2026) act on the positive-current edge.
  - Under transients two fall back to a safe value: Yousefzadeh & Maksimovic (TPEL 2006; 5 -> 1 V, 200 kHz,
    measured) and Sun et al. (Microelectronics 54(4), 2024; 12 -> 1 V, 6 MHz, simulated: no dead time seen for four
    periods -> maximum). None tests repeated steps.
- The SCB differs: a slotted phase's negative current is set by the ladder, not by its timing (A109), so the delay is
  the only lever and has to follow the current.
- D57 gives V_DS(t) after a low-side turn-off at i_off (EPC2067 Coss, both sides' reverse conduction). D63 reads it
  only at a fixed t_tr. Here it is the whole trace, and the soft window is the set of delays with V_DS <= 2 V.
- Data: every learned turn-on of phases 2-4 in the plant-V7 records A229-A246 (distinct runs, one and four modules).
  i_off comes from the paired low-side turn-off; the delay is the actual turn-on minus that turn-off.
- ML:
  - m1: a GP on the residual (record - D57) locates missing physics.
  - m2: an MLP classifier of soft turn-ons, trained on the records alone, checks D57's windows without using D57.
- Not tested: phase 1; the closed loop (a delay set from the current changes the currents it then sees; step 2); Coss
  against temperature (D57 is at 25 C). The records sample only the delays the learner chose.

## 2. Criteria
Soft: V_DS at the actual turn-on <= 2.0 V, about 3 % of a 12 V hard turn-on's energy by V^2 (ours, no source).
Rows: i_off <= -5 A (a swing exists), inside D57's grid (rail 6-20 V, i_off -100..+30 A, delay 0-40 ns).
- c1 (D57 predicts the plant): on each board with >= 1000 rows, median |V_D57 - V_rec| <= 1.0 V and soft / hard
  agreement >= 90 %.
- c2 (a delay set from the current is possible): take the rows whose own D57 window is not empty. Split the current
  into K uniform bins over [its 1st percentile, -5 A]; take the rail to the 1 V grid; on D57's grid choose one delay
  per bin. That delay keeps V_DS <= 2 V over +-0.5 ns on >= 95 % of the rows for some K <= 8 (a 3-bit comparator).
- m1 (reported, meaning registered): if the GP lowers the test RMSE by >= 20 %, D57 misses a block, and its largest
  relevance names it.
- Also reported:
  - c2 without the rail;
  - c3: the learner's hard fraction on the same rows (all, after 20 us in mode P, by current);
  - m2's windows against D57's wherever >= 100 rows lie within +-3 A and +-1 V.

## 3. Predictions (not criteria)
- c1 passes on N0 and N75: median 0.3-0.8 V, agreement 92-97 %. S75h (125 C) is similar, because the delay is taken
  at the actual turn-on.
- Windows (N0, rail 12 V, phases 2-3; estimated from A124's I_th 23.6 A and t_tr 16.9 ns):
  - -30 A: 9.8-14.7 ns; -40 A: 6.8-15.4 ns; -70 A: 3.7-21.3 ns.
  - N75 (L x 0.75): about 0.87x in time.
- c2: K = 1 covers < 80 %; K = 4 reaches 95 % with the rail known; without the rail one more bin is needed.
- c3: the learner is hard on 5-15 % of the rows that have a window. Most of these are at -20..-35 A (narrow windows)
  and after releases.
- m1: gain 10-30 %. Top features: the delay and dv_err (D63's fixed rail ratio for the next phase), or the low-side
  edge's timing (loop, edge rate).

## 4. Decision rule
- **c1 and c2 pass:** a delay set from the current is viable.
  - Step 2 builds D63's learner block with both the present learner and a K-level model delay (K from c2).
  - The current comparator's levels become a question for Mihai, covered first by our own scenarios.
- **c1 passes, c2 fails:** the current must be known to finer than 3 bits. Structure B is preferred for step 2: keep
  the learner and fall back to the model value on invalid reports (after Yousefzadeh / Sun).
- **c1 fails on a board:** D57 misses a block there. m1 names it, and the block is added before step 2.
