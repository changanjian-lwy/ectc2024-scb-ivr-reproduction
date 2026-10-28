# A259 - a latched fault trip: under-voltage, a fault level that never suspends, and the average current (BOUNDARY)
Method: cosim (bridge cfg "fault"; plant cfg "short", bdac50e). Track A. Written and committed before the arm-f runs.
Plant V7, one module, 25 C (S75h: slow devices at 125 C). Final configuration = A244 cfg_w + rev_n 16 + hold_floor_ns
3.0 + ocp {110 / 125 / 140 A, t_ns 1.0, n_susp 6, n_cap 6}.
Looked at beforehand:
- User decision 2026-10-28: build the fault protection. Background: D89 found that once the limit suspends, the
  loop carries about 136 %, and above that nothing stops the current.
- Survey (agent, 2026-10-28; datasheets read in full; notes kept outside the repo):
  - TI TPS54A20 (a 2-phase SCB, 8-14 V, 10 A): 3 sequential over-currents turn all switches off, then hiccup; UVP
    at 90 % of Vref; Ct window 35 / 65 % of Vin; Ct is pre-charged to Vin / 2 before every start.
  - TI TPS546D24A: an up/down OC count, default 3; a high-side short gets 3 cycles of pulse-by-pulse limiting, then
    both FETs off; UV at 60-95 % with a delay of 1 / 3 / 7 PWM clocks, not active during the soft start.
  - Renesas ISL68222 / 68233: peak, valley and total-current limits, the total current with a response delay;
    default latch-off.
  - No 2020+ paper on a fault path for an SCB or ladder-SCB regulator was found.
- Arm d (no fault path; make_diag_cfgs.py, run from bdac50e, records cosim/run_d_*.json):
  - Rows: 0.25 / 1 mOhm shorts and 150 / 200 % resistive overloads from 400 us.
  - The limit holds every row at 172-179 A until it suspends, 2.39-2.75 us in. The first uncut pulse then runs
    away: 322-390 A at once on the shorts and on 200 %, reaching 445-668 A, V_DS 53.6-82.0 V and a ladder
    4.2-7.1 V off. On 150 % the peak is 228 / 259 A.
  - At suspension, the loop's Ton had risen 360-1491 LSB while the limit cut (125 % rows: -148..+185).
  - Vo falls below 0.9 V 0.22 / 0.48 / 0.61 us into the shorts. On 200 % it stays >= 0.905 V.

Decision it changes: whether the final configuration gets a latched fault trip. This is stage 1; a hiccup restart,
which needs the flying capacitors handled, is stage 2.

Cheaper check first: arm d, plus replays on the final configuration's 57 records:
- no gate peak above 211.8 A (a_S75h_d2, phase 1 for 15 us after the handover);
- no Vo below 0.9418 V in mode P;
- the 10 us mean of the load at most about 317 A (125 % plus Co's recharge).

Budget: 10 runs at 10 jobs, about 1 h.

Pre-flight (scripts/preflight.py):
- IDENT rows, on their own records, pass f4.
- FAULT rows, on arm d, fail f1 / f3 as they must, and f2 on the shorts and on 200 %.
- f3's path ran on a synthetic trip record.

Provoking rows: the legit row closest to each detector (IDENT); the 1 mOhm short, where Vo falls slowest; 200 %,
where under-voltage never acts.

## 1. What and why
- In the final configuration a fault runs into the limit's suspension (the count of 6). The Ton the loop built up
  while the limit cut then drives the first uncut pulse to 322-390 A.
- Three detectors (bridge cfg "fault"). Any of them trips; every switch then turns off at t_drv and stays off:
  - **Under-voltage:** Vo below 0.9 V (TPS54A20's 90 %) for 400 ns, from mode P on. 400 ns is about one switching
    period, TPS546D24A's shortest delay.
  - **Fault level:** 220 A on the phase current at window ends while the high side is on. The pulse is cut even
    while the limit is suspended, and an up/down count of 3 trips (TPS546D24A). 220 A is 8 A above the final
    configuration's largest legit peak (211.8 A).
  - **Average current:** the 10 us mean of the phase currents' sum above 350 A (140 %; D89 puts the rating at
    136-140 %). This is ISL68222's total-current fault.
- Rows:
  - FAULT (6): sh025_N75, sh1_N75, sh025_S75h, ov150_N75, ov150_S75h, ov200_N75.
  - IDENT (4): a_S75h_d2, p_N75_60k, o125_S75h, pr_N75.
- Not tested: restart (hiccup), four modules, the N0 / N13 boards, faults during start-up or a transient, a fault
  that clears.

## 2. Criteria
- f0: portable suite 706 OK (with cocotb; test_cosim_fault 6, test_cosim_short 3), regression quick + full PASS
  (tmp/logs/a259_{tests,reg_quick,reg_full}.log).
- f1: every FAULT row trips; the shorts trip by under-voltage before the limit suspends.
- f2: on every FAULT row, whole-run V_DS <= 40 V and gate-record peak <= 300 A; on the shorts, <= 200 A.
- f3: from 2 us after the shutdown to the end, every phase current stays within +-5 A.
- f4: IDENT rows never trip and equal their records (A246's same over A236's KEYS).

Where 300 A comes from: a cut ends 11 ns after a 220 A crossing (55-60 A on 2.2 nH at a 12 V rail), and the gate's
fall adds about 10 A, which gives about 285 A. This bounds the mechanism; it is not a device limit (EPC2067 is rated
409 A pulsed per device, with 2 per high side).

## 3. Predictions (not criteria)
- **Shorts:** under-voltage trips 0.6 / 0.9 / 1.0 us after the short (sh025_N75 / sh025_S75h / sh1_N75), before
  the suspension at about 2.4 us. Peaks stay at arm d's pre-suspension 176-179 A.
- **ov200_N75:** no under-voltage trip. The limit suspends at about 2.4 us, the fault level cuts the next pulses at
  about 275-290 A, and a phase's third cut trips about 1 us later.
- **ov150:** pulses go over 220 A from 2.8 us (S75h) / 3.4 us (N75), and the count trips about 1 us later, with
  peaks <= 260 A. The average would only have tripped at about 9 us.
- **After the trip:** the currents fall through the low sides' reverse conduction within about 0.2 us. The ladder
  stays within about 1 V of its state before the trip, since no switch conducts across a capacitor.
- **IDENT rows:** equal to their records.

## 4. Decision rule
- **f0 or f4 fails:** wiring or a false trip; trace it and report.
- **f1-f4 pass:** the latched fault trip joins the final configuration, and the user is told. Stage 2 (hiccup
  restart and the flying capacitors) is registered next.
- **f1 fails on a short** (under-voltage too late): measure Vo's fall and the trip time, and report.
- **f2 fails** (a peak over 300 A or V_DS over 40 V): name the pulse. The candidate fix is freezing the integrator
  while the limit cuts (the hand-back), and the user decides it, as they did on 2026-10-27.
