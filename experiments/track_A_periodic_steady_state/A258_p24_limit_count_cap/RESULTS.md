# A258 - a ceiling on the limit's count, so it re-arms soon after an overload (RESULTS)
Boundary: 78a86f9 (bridge option 2071bc7). Plant V7, one module, 25 C (S75h: slow devices at 125 C). Records: cosim/run_{s,c}_*.json, 13 runs from
78a86f9 (cosim_sources_modified False; release records-a258). Analysis: a258_analyze.py -> a258_summary.json.
Figure: a258_figure.py -> a258_count_cap.png. Peaks are gate-level turn-off currents (gate_offs_last i_max_a, A240's q1).

## 0. Verdict
- **t0-t3 pass as registered: n_cap 6 joins the final configuration** (decision rule, Section 4).
- **t1, the gap A258 was run for, is closed.** After a 90 us overload (+62.5 A, 125 %, 200-290 us) and a 1 MHz train
  from 300 us:
  - with the ceiling (arm c) the limit re-arms at 292.9 / 293.9 us (N75 / S75h), before the train. The train peaks
    at 198.0 / 187.3 A, V_DS 35.0 / 32.0 V, Vo never above 1.05 V;
  - with A256's count (arm s) it re-arms at 374.5 / 371.6 us, 84.5 / 81.6 us after the overload. The train runs
    unprotected until then: 276.9 / 209.3 A, 20 / 4 turn-offs over 200 A.
- **t2: the ceiling changes nothing before the re-arm.** On A256's four suspending rows, arm c's peaks, NEW, Vo and
  ladder equal A256's. Only the re-arm comes earlier, 12.1-19.0 us after the suspension instead of 19.5-31.6 us
  (k_S75h 15.6 against 26.8 us).
- **t3: under a repeated overload (100 kHz, 125 % highs, S75h) the two arms are identical.** Peaks 187.0 A, ladder
  1.18 V, 0.0 A / 0.0 V apart over the whole train. The ceiling does bind: arm c re-arms 0.47-1.04 us earlier in
  five of the first six lows. Both arms re-arm inside the low levels, though, where nothing is cut, so every high
  starts with the limit armed in both.
- **t0:** A256's three rows that stay suspended (k_N0, o125_N75, o125_S75h: suspended at 517.3 / 511.6 / 505.5 us
  with the overload lasting to 620 us) are equal bit for bit (A246's same). Their counts sit at the ceiling but never
  return to 0, so nothing re-arms in either arm.

## 1. Criteria
| # | criterion | result |
|---|---|---|
| t-1 | tests 726, regression quick + full | pass (tmp/logs/a258_{tests,reg_quick,reg_full}.log) |
| t0 | HOLD rows k_N0, o125_N75, o125_S75h equal to A256 | pass, bit for bit |
| t1 | pr rows, arm c: whole peak <= 200 A, V_DS <= 40 V, Vo > 1.05 V for < 25 us | pass: 198.0 / 187.3 A, 35.0 / 32.0 V, 0 us |
| t2 | REARM rows, arm c vs A256: peaks + 2 A, NEW, \|Vo ext\| + 2 mV, ladder + 0.2 V | pass, equal (k_S75h 193.3 A, a_S75h_d2 211.8 A, a_S75h_d20 201.0 A, a_S75_d20 191.9 A) |
| t3 | ro_S75h, arm c vs arm s, the same test | pass, identical |

a_S75h_d2 / a_S75h_d20 pass 200 A in both A256 and arm c: they sit inside item 2's 40 us hold-off (A236 ITEM2).

The analysis needed one fix after the runs (criterion unchanged). t3's row has a pulse train, and A236's row function
reads only line and load steps. The pre-flight gave ro_S75h no stand-in, so this path never ran before the records
existed. train_row() takes the same quantities from the train's start; it passes run_s_ro_S75h against itself.

## 2. Predictions against the records
- Arm s misses q1, re-arming 60-100 us after the overload: yes, 84.5 / 81.6 us.
- Arm s train peaks "as without the limit, about 230 / 210 A": 276.9 / 209.3 A. The 230 A was A246's controller-level
  peak (highoffs 231.7 A); the same record's gate-level peak is 244.6 A, first over 200 A 3.9 us into the train. My
  prediction used the wrong quantity.
- Arm c re-arms within 3 us: 2.9 us on N75, 3.9 us on S75h (missed by 0.9 us; both before the train).
- Arm c train peaks as A254's 193.2 / 182.7 A: 198.0 / 187.3 A, 4.8 / 4.6 A higher. The cause is the 10 us gap, in
  both arms. At 299.5 us Vo is still 5.3 mV high from the release and the Ton register is at 797 (A254: 786).
- ro_S75h, each high suspends: the first six highs do (6 cuts per phase each). From about 360 us the loop has adapted,
  and later highs bring 0-6 cuts; suspensions follow only at 403, 463, 533 and 553 us. After 600 us the load stays at
  312.5 A (load_pulse ends high), so both arms suspend at 619.6 us and stay suspended to the end: A256's behaviour
  under a lasting overload.

## 3. Limits
- N75's margin after an overload is 2.0 A (198.0 A), and it was tested only with a train 10 us after the release.
  A train that starts sooner meets a loop that is still recovering; that case was not run. The re-arm cannot come
  sooner than 6 clean pulses on every phase, about 2.4 us at 2.5 MHz, because a ceiling below n_susp would stop the
  limit from ever suspending (the bridge now refuses it, fae6272). A train inside that window starts unprotected;
  A246's unprotected N75 train first passed 200 A 3.9 us after its start. A count replay on this experiment's arm-s
  trains (D89) re-arms the limit 2.2 us into a train that starts at the ceiling: only 3-7 % of the train's pulses
  last the 11 ns from the 110 A crossing to a cut.
- With lows too short for A256's count to recover, the ceiling re-arms the limit where A256 would not. Each re-arm
  then costs at most 6 cuts per phase before the next suspension (n_susp 6), each with A256's hand-back kick
  (+11-14 A on S75h). This bound comes from the mechanism, not from a run: in ro_S75h both arms re-armed in every
  low.
- One module, 25 C (S75h 125 C), 2.2 nH (110 A level). The 125 / 140 A levels on 2.933 / 3.813 nH carry the same count logic but
  were not run with n_cap.
