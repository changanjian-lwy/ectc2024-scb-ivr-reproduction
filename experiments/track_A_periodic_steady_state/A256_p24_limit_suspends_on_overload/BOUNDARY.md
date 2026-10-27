# A256 - the peak limit suspends itself after a run of limited pulses (BOUNDARY)
Method: cosim. Bridge option "ocp" "n_susp" at f9369fe (off by default; tests 724, regression quick + full PASS; A254's
p_S75h_10k equal with and without n_susp 6 to 160 us, 5 fires included). Track A. Written and committed before the
runs. A255 (the 125 % step on the 2.2 nH boards) is still running; its rows here are judged against its arm h.
Looked at beforehand:
- A254: 110 / 125 A take item 10's 1 MHz rows to 193.2 / 182.7 A. But a 125 % load on N0 makes the limit cut almost
  every pulse, and the ladder collapses (k_N0, m4_s_p250).
- User decision 2026-10-27: no adoption yet; first an overload response that keeps the ladder.
- Survey (agent, 2026-10-27; datasheets read in full, papers as abstracts):
  - commercial controllers count limit events, then shut down or hiccup:
    - TI TPS546D24A: up/down count, default 3;
    - Renesas ISL68222 / 68233: 6 consecutive cycles;
    - Infineon TDA21490: a flag after >= 10 cycles;
    - TI TPS54A20 (an SCB): 3 sequential, then a hiccup that re-pre-charges Ct to Vin / 2, and a Ct window trip;
  - peak current control cannot balance a flying capacitor; valley control can (Abdelhamid et al., TPEL 2019);
  - a clamp on the shared command keeps the balance (Dialog patent US10554124B1).

Decision it changes: whether the final configuration adds the limit with n_susp 6, closing item 10 at 1 MHz.

Cheaper check first: a256_counts.py replays the up/down count on A254's records:
- the 1 MHz rows reach 2 and the handover rows 1;
- the item-2 and line-step rows reach 18-74 on phase 1;
- k_N0 / m4_s_p250 reach 201 / 159.

Budget: 11 runs at 6 jobs, about 3 h (the four-module row first).

## 1. What and why
- n_susp = 6, Renesas's default count, applied as an up/down count. It sits above the 1 MHz rows' 2 and below the
  overloads' runs. A hiccup would drop the specified +62.5 A row, so the count hands the overload back to the loop.
  That action is ours; no source does it.
- Rows (cfg_s_<row> = A254 / A255 arm l + n_susp 6):
  - CHANGE, A254's rows whose count reached 6: m4_s_p250, k_N0, k_S75h, a_S75h_d2, a_S75h_d20, a_S75_d20;
  - O125: A255's o125_N75, o125_S75h;
  - IDENT, rows that stay under 6: p_N75_1000k, p_S75h_1000k, p_S75h_10k. They must equal A254's records.
- The other 24 rows of A254 count at most 1, or did not fire. They equal A254 by construction (the count never reaches
  6), and IDENT checks that.
- Not tested: n_susp other than 6; overloads above 125 %; a real fault (short circuit). A fault needs a total
  over-current trip with a hiccup and a pre-charged restart (TPS54A20), which this plant does not model.

## 2. Criteria
- s0: tests 724, regression quick + full PASS (tmp/logs/a256_*.log).
- s1: IDENT rows equal A254's records (A246's same).
- s2: k_N0, m4_s_p250, o125_N75, o125_S75h, against the final configuration (A246 run_h_ / A255 run_h_):
  - A253's o3: whole peak and post-event peak <= max(reference, 200 A) + 2 A, NEW <= the reference's,
    |Vo extreme| <= the reference's + 2 mV;
  - the ladder's deviation after the event <= max(reference, 1 V) + 0.2 V on every module.
- s3: k_S75h, a_S75h_d2, a_S75h_d20, a_S75_d20: the same as s2 against A246 run_h_.
- s4: the 1 MHz rows meet A240's q1 + q2 (whole peak <= 200 A).

## 3. Predictions (not criteria)
- s1 and s4 hold: the 1 MHz rows are A254's (193.2 / 182.7 A).
- The overload rows suspend within 6 limited pulses (about 2-3 us after the first fire), before the ladder moves. They
  then run as the final configuration: k_N0 about 181 A, rails within 0.4 V.
- The item-2 rows suspend early in their phase-1 runs and land within 2 A of the final configuration (211.2 / 207.8 A),
  so item 2 stays as it is.

## 4. Decision rule
- **s0 or s1 fails:** wiring; trace it.
- **s2-s4 pass:** the user decides adoption (AskUserQuestion). Item 10 closes at 1 MHz, with the stated limit (no fault
  path modelled).
- **s2 fails (a collapse or a peak above the final configuration):** the suspension comes too late or re-arms too early.
  Measure when, then report to the user.
- **s3 fails:** name each row's cost; the user decides.
