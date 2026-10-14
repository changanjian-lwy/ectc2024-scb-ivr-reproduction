# A223 - phase 1's relative cap only while Vin rises (RESULTS)
Boundary: 7722118 (code + boundary). Records: release records-a223 (20 cosim records, logs). Analysis: a223_analyze.py
-> a223_summary.json; figure a223_figure.py -> a223_w20.png. Runs from 7722118, cosim_sources_modified False.
Final configuration on plant V7 (A222's trims), one module, 25 C unless named; arms off (as adopted) and g25 (vff
rel_gate 25 codes = 0.5 V).

## 0. Verdict
- **Not adopted as registered: c1 misses on three of the five re-applications, and one of them rises** (N0 +200 A
  from 20 %: 214.0 -> 218.0 A), so the rule's second branch (adopt if every w row falls) does not hold. j1, c2, c3
  and c4 pass. The gate goes on into A224, tested there together with a damped loop.
- **The gate removes what it was built for**: phase 1 is no longer held - its on-time equals phases 2-4's from the
  first period after the step (off: 13.5-15.3 against 22-27 ns in the first 2 us), and rail 1 stays at 12.2-12.6 V
  (off 15.3-19.5 V). Peaks: N0 from no load 223.6 -> 150.0 A, N0 from 5 % 248.3 -> 214.4 A, N75 from 5 % 232.1 ->
  219.2 A, S75 125 C +175 A from 30 % (post-step) 181.0 -> 158.3 A. It also frees phase 1 after the specified
  +62.5 A from 5 % (u_N0: 13.0 against 15.5 ns off; rail 1 12.71 -> 11.94 V; peak 59.7 -> 58.0 A).
- **Unchanged where it should be**: the k row, +4.8 V / 2 us, -8 V / 10 us and the tightest S75 125 C +4.8 V / 1 us
  are bit for bit the same in both arms over the whole run (at a rising Vin the gate opens and tlp equals the
  low-passed Ton of a steady state); every pair is bit for bit the same before its event (c4).
- **A second mechanism, in both arms: the loop rings after large re-applications** (figure a223_w20.png, records
  run_w20_N0_off.json / _g25.json): Vo swings 0.96-1.03 V with a period of about 2.9 us for more than 25 us while
  the loop's Ton swings 9-36 ns; the low-side turn-off currents of all four phases follow Ton (-70..+117 A against
  the -15.6 A target), and the peaks come at the swing's current maxima. Phase 1's timed low-side edge learns at
  most 2 ns per period (lo_smax 64), so a fast-rising Ton lets the current integrate Ton's excess; around that
  integrator the P term and Co make an undamped pair (estimate 2.8 us, A224 Section 1). In the off arm phase 1,
  held by the cap, damped the swing a little; freed, the swing grows (Vo maximum 1.012 -> 1.030 V).

## 1. Criteria
| row | j1 / c4 | c1 / c2 / c3 | off -> g25 (peak, Vo extreme, rail 1 max, late fires after) |
|---|---|---|---|
| w0_N0 (0 -> +250 A) | c4 same | c1 pass | 223.6 -> 150.0 A, -47.5 -> -57.8 mV, 19.51 -> 12.23 V, 0 -> 0 |
| w5_N0 (5 % -> +237.5 A) | c4 same | **c1 miss** | 248.3 -> 214.4 A, -54.3 -> -42.8 mV, 18.66 -> 12.41 V, 59 -> 30 |
| w20_N0 (20 % -> +200 A) | c4 same | **c1 miss** | 214.0 -> **218.0** A, -42.5 -> -40.8 mV, 17.25 -> 12.38 V, 86 -> 104 |
| w5_N75 (5 % -> +237.5 A) | c4 same | **c1 miss** | 232.1 -> 219.2 A, -39.7 -> -31.2 mV, 17.77 -> 12.60 V, 75 -> 68 |
| w30_S75h (125 C, 30 % -> +175 A) | c4 same | c1 pass | post 181.0 -> 158.3 A (whole 180.0: the handover), 15.34 -> 12.23 V |
| u_N0 (5 % -> +62.5 A) | c4 same | c2 pass | 59.7 -> 58.0 A, -10.2 -> -10.1 mV, 12.71 -> 11.94 V |
| k_N0, l_N0_p48, l_N0_m80, k_S75h | c4 same | c2 / c3 pass | bit for bit (181.3, 178.5, 168.3, 193.0 A) |
- j1: unit tests 106 of 106 (the constant-Vin test fails without the gate), regression quick and full bit for bit,
  k_N0_off = A222's run_k_n_s_p62.json bit for bit. No overlap or shoot-through; V_DS <= 33.3 V.

## 2. Predictions
- Held: off arm 214-248 A (220-260 predicted); phase 1 equal to phases 2-4 from the second period; rail 1 <= 13 V;
  the line rows bit for bit (l_N0_m80 predicted; the rising rows within 0.5 A predicted, identical found); c4
  bit for bit; u_N0 / k_N0 within 0.5 A (-1.7 / 0).
- Missed: g25's w rows 160-200 A (150.0-219.2); D63's ranking held only where the ring is small (D63 has phases
  2-4 equal to phase 1 and under-states the swing: 146 against 218 A on w20).

## 3. Limits
- One step position per row, one module, 25 C except S75 at 125 C. The gate's threshold assumes a bus whose
  sample-to-sample ripple stays below 0.5 V; a load step during a rising Vin still meets the cap as before.
