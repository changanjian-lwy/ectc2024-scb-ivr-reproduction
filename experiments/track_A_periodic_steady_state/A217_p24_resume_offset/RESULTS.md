# A217 - a resume that ends at the valley target (RESULTS)
Boundary: 10087ca (branch a217-resume, merged into main with db7efde). Records: release records-a217 (6 cosim
records, logs). Analysis: a217_analyze.py -> a217_summary.json. Runs from 10087ca, cosim_sources_modified False.
Final configuration on plant V6 (low sides 0.3 ohm x the board's factor, A206's trims, ton_min_ns 4.0 ns, ton_lat
16), skip hi 5 mV / lo 1 mV, resume offset res_ofs_a = 8 ns x Vo / L (2.73 A on N0, 3.64 A on N75 / S75), one module.

## 0. Verdict
- **Not adopted (decision rule): s3 still misses by more than 1 A on both nominal boards.** j1, s1 and s2 pass on all
  six rows, s4 on the +62.5 A row.
- **The offset does what it was meant to: phase 1's first valley after a resume is -15.62 A (N0) and -15.96 A
  (N75)**, against -18.3 / -19.6 A in A216 (target -15.6 A).
- **Phases 2-4 still start off target**, and the alternation still follows: N75's first round -19.95 / -24.56 /
  -20.88 A, phase 3 then -8.59, -20.07, -13.08 A; N0's -11.49 / -9.95 / -14.36 A. Over the last 20 us N0's valleys
  reach -5.7 A (phase 4, band -20..-12 A) and N75's -24.6 / -8.6 A (phase 3).
- **Cause, read from the edge log** (record cosim/run_z_N75_25_10.json, resume at 440.191 us): the four low-side
  intervals have the same length and each current falls by 18.3-19.3 A; each first valley differs from phase 1's by
  the current that phase carried at its own low-side turn-on (+2.7 / -0.6 / -5.7 / -2.6 A). Those currents are a
  ring of the idle phases: the pause starts with each low side turned off at its valley (-11..-16 A), the node swings
  to its rail and rings with about 11 V, and with 0.54 mOhm as the only damping the idle currents are still 6.2-7.1 A
  at the pause's ticks (last 60 us; 6.4 A after 60 us of pause at no load). The next step is therefore A220 (the
  pause starts at zero current), not the per-phase resume comparator the decision rule named: that would fix the
  first round but leave the ring.
- **No load: s3 not measured.** The last 20 us are one pause (98 ticks, no turn-off); A216's function counts that as
  a pass. Over the last 60 us (28 turn-offs) the valleys are -27.5..-15.1 A.
- **The slow board never skips at 10 %**: its Ton register stays at 6.91-7.13 ns (25 C) and 5.44 ns (125 C), above
  the 4.0 ns limit, and it regulates at about 8.25 MHz (121 ns period) with 13.67 / 12.72 W of semiconductor loss
  for 25 W out, 10.6 / 9.9 W of it in high-side edges. Its rows are A216's bit for bit where A216's has finished
  (z_S75_25_10). Skipping as designed does not reach slow boards; their light-load loss stays a shedding question.

## 1. Criteria
| row | s1 | s2 | s3 | s4 | Vo, last 20 us | valleys, last 20 us (A) | loss (A216) |
|---|---|---|---|---|---|---|---|
| N0 10 % | pass | pass | **miss** | - | 0.9989-1.0078 V | -18.8 .. -5.7 | 2.73 W (2.59) |
| N0 no load | pass | pass | not measured | - | 1.0014-1.0039 V | none (60 us: -27.5 .. -15.1) | - |
| N75 10 % | pass | pass | **miss** | - | 0.9995-1.0093 V | -24.6 .. -8.6 | 2.87 W (2.44) |
| S75 25 C 10 % | pass | pass | pass | - | 0.9997-1.0000 V | -17.1 .. -13.8 (no skip) | 13.67 W (13.67) |
| S75 125 C 10 % | pass | pass | pass | - | 0.9999-1.0002 V | -16.7 .. -14.5 (no skip) | 12.72 W |
| N0 5 %, +62.5 A | pass | pass | pass | pass | 1.0001-1.0003 V | -16.8 .. -15.0 | 4.13 W (4.12) |
- j1: unit tests 101 of 101, regression quick and full bit for bit. Peaks <= 181.1 A, V_DS <= 31.2 V, no late fire.

## 2. Predictions
- Held: phase 1's first valley within 1.5 A of -15.6 A on N0 and N75; s1, s2, s4 as in A216.
- Missed: the alternation's first swing (N75 phase 3: 16.0 A against A216's 19.4 A, not halved); s3 on N75; N0's
  miss (6.3 A, not up to 1 A); the no-load row (not measured in 20 us, -27.5 A over 60 us); loss within 5 % of A216's
  (N75 +18 %). The slow board was open: it does not skip at all.

## 3. Limits
- One step position, 150 us after the release, 25 C on the nominal boards. The ring's size rests on the plant's
  damping (the inductor's DC resistance only); a real inductor's AC resistance would damp it, by an unknown amount.
