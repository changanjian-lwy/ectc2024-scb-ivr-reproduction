# A119 - the 1 MHz candidate on the standard matrix (RESULTS)

Track A, main line.

**Candidate:** A118 f6 (1 MHz, 10%, timed turn-off with a 2 A floor, Cs
6 µF, 60 kHz).

**Boundary:** `BOUNDARY.md`, committed (42c0bf2) before any run.

**Records:**
- `cosim/run_*.json`, `cfg_*.json`;
- `a119_predictions.json` (D63);
- `a119_summary.json` (`a119_analyze.py`).

## 0. Verdict

1. **The candidate passes the standard matrix, with two marginal misses
   and a driver cost.**

   | row | result |
   |---|---|
   | m1n, m1p, m3n, m3p | high side within 0.03 V of n0; sd ≤ 0.01 A; start-up ≤ 185 A (m3n, 26 late fires at the start-up); no overlap |
   | j30 | sd 0.14-0.17 A (**registered ≤ 0.16: a 0.01 A miss**); high side within 0.02 V |
   | j100 | sd 0.34-0.40 A (≤ 0.6 pass) |
   | ±25 A | +9.3 / −7.6 mV; peaks 141 / 155 A (D63 140 / 154) |
   | ±4.8 V over 10 µs | 160 / 188 A, back in ≤ 36 µs |
   | −8 V over 10 µs (to 40 V) | **205 A (a 5 A miss)**, −91.3 mV, back in 51.5 µs; **no limit cycle** at 40 V |

   **With A118's rows, the candidate's full matrix:**
   - every load step passes;
   - every line step over ≥ 5 µs passes, except −8 V (205 A);
   - every driver row passes (j30's sd 0.01 A over).
   - **Misses:** the 1 µs steps (201 / 206 A) and −8 V / 10 µs (205 A).
2. **The floor removes the low-line limit cycle.**
   - At 40 V the rail is 10 V and D57's threshold ~12.3 A, below the
     12.5 A target.
   - The timed design without a floor sat in a ±18 mV limit cycle at
     43.2 V (A116 t30).
   - With the floor, Vo's peak-to-peak over the last 200 periods is
     0.00 mV.
   - **So the floor also makes the target safe across the input range.**
     It holds phase 1 where the valley measurement still works.
3. **A driver mismatch of +3.4 ns costs 0.85 points at 1 MHz** (88.12%
   against 88.97%).
   - The low side turns on 3.4 ns late. The peak current (~140 A) flows
     in the low side's reverse conduction (−2.37 V) for that time:
     2.39 W.
   - The timed low side's dtl cannot go below 0. A late driver longer
     than the node's own fall is not compensable.
   - A driver property (A91), not the floor's. It applies at 5 MHz too.
4. **D63:**
   - **Peaks:** within 10% on ±25 A and −4.8 V / 10 µs. The rising
     10 µs row was 188 against 178 A (flagged weak).
   - **Missed at 40 V:** 205 against 168 A, and Vo's sign: −91 against
     +75 mV. The deepest-input step is outside its validated range.

## 1. Criteria (BOUNDARY Section 2)

| row | criteria |
|---|---|
| m1n, m1p, m3n, m3p, j100 | pass |
| j30 | **sd_0.16A miss** (0.17 A) |
| s_m25, s_p25, l_m48_10us, l_p48_10us | pass |
| l_m80_10us | **peak_200a miss** (205 A); no overlap, no runaway pass |

## 2. Next

- **The candidate stands for a bus with slew ≥ 5 µs per 4.8 V.** The
  remaining misses are 1-6 A over 200 A.
- **Possible levers:**
  - the floor depth (2 A is not optimised);
  - fc (A120: higher fc helped; ki's 16-bit register allows up to
    ~68 kHz);
  - a slightly lower target at low input (the margin).
- **Then multi-module at 1 MHz** (C-track): four modules with the
  candidate.
