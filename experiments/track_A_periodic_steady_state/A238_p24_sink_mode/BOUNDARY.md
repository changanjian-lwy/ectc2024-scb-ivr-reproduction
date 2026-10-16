# A238 - a sink mode at the lower Ton limit for item 6b (BOUNDARY)
Method: RTL + bridge + cosim. scb_ctrl cfg_sink / cfg_sink_hi / cfg_sink_lo -> output sink; the bridge's target is the
sink target while sink is set (cfg "sink" {hi_mv, lo_mv, i_a}); absent = bit-identical. Code and cfgs committed before
the runs. Track A. Looked at beforehand: A237's records (ripple and period at the Ton limit), scb_ctrl's skip logic,
the bridge's target path (A132's dep moves it the same way), A230's start-ups into 1 kOhm.
Decision it changes: whether the load range is 0-100 % on nominal boards with a true current load, or a stated
minimum load of about 2 % (A237), and whether item 6b (start-up into no load) closes.
Cheaper check done first: hand estimate from A237's records (below). Budget: 11 runs, about 60 min at 10 jobs.

## 1. What and why
- A237: below the lower Ton limit the module pauses with every switch off and cannot sink. A release from full load
  to 0 A stays at 1.0576 V (N0) / 1.0460 V (N75); a start into 1 kOhm ends at 1.022 / 1.025 V (A230) with the ladder
  left unbalanced (rail 1 18.8 / 24.0 V at the end, A230 records).
- Basis: Dell, US 9467052 B2 (Zhang, Luo, Li; filed 2014-12-23): a synchronous buck VR in light-load PFM / DCM cannot
  sink, and a sinking load drives an over-voltage fault; on an overshoot (Vout above an upper threshold) it enters FCCM,
  which sinks every cycle, and returns to PFM on a positive load current below a threshold (single-phase buck for
  memory VTT / VDDQ rails). Intel's VR12 decay mode (US 8791676) lets the output fall at the load's rate, but only for a
  commanded VID-down, not for an overshoot. No source found on net sinking in a series-capacitor buck: Zhao et al.
  (ECCE 2023, 3-phase 48 V SCB) report negative inductor current at very light load, but not a sinking module or its
  ladder balance. Ours is flagged as unsourced.
- Our form of FCCM: P24's control holds the valley (−15.6 A) and moves Ton, so at the Ton limit the mean current is
  fixed (A237: ripple ~51 A on N0, ~62 A on N75, period ~180 ns, about +38 A per module while switching). Instead the
  valley target moves: while sink is set (a sample above vref + 20 mV with Ton at its limit, until a sample at or below
  vref + 3 mV) the module does not pause and the target is −40 A. Estimate: mean per phase −40 + 25.5 = −14.5 A on N0
  (−58 A per module), −40 + 31 = −9 A on N75 (−36 A); peaks +11 / +22 A stay positive, so the low sides still turn on
  at zero voltage. Deviations from the source: entry needs the Ton limit (the mode replaces the pause only), exit on
  Vo, not on the load current (none is measured). Threshold 20 mV: clear of a 10 % row's skipping band (+7 mV) and of
  the specified load step's +15.3 mV (where Ton is not at its limit anyway).
- Rows (plant V7, final configuration, one module, + sink {hi_mv 20, lo_mv 3, i_a −40}): A237's eight (releases to
  0 / 5 / 25 A constant current, re-applications from 12.5 / 75 A) and A230's lead-arm start-ups into 1 kOhm (N0, N75)
  and full load (N0). References: the source records.
- Not tested: four modules (the slaves do not follow a pause), slow boards at light load (they do not skip), line steps
  while sinking, other temperatures for N0 / N75, other i_a / thresholds.

## 2. Criteria
- t0: tb 117 / 117; regression quick + full PASS on fresh outputs with the option absent.
- t1 (s_c0_N0, s_c0_N75): above 1.05 V for <= 25 us in all; back within 1 % <= 25 us after the release; Vo within
  1 % over the last 20 us.
- t2 (every row): completes, whole-run peak <= 200 A, V_DS <= 40 V, no overlap or shoot-through.
- t3 (s_c2_N0, s_c10_*): Vo within 1 % over the last 20 us; 25 A rows: A229's skipping run test and valleys in
  −20..−12 A over the last 20 us.
- t4 (s_cw5_*, s_c30_S75h): post-step peak <= 200 A and <= A237's + 10 A; Vo within 1 % over the last 20 us.
- t5 (s_u_N0_0, s_u_N75_0): Vo within 1 % over the last 20 us, Vo <= 1.05 V, ladder deviation at the end <= the
  reference's.
- t6 (s_u_N0_100): if sink is never set, the record equals A230's (sections, edges, peaks); otherwise the handover
  peak <= the reference + 2 A and Vo within 1 % at the end.
- t7 (every row): sink low at the end; every valley while sink is set >= −55 A.

## 3. Predictions (not criteria)
- 0 A: sink set within 2 us of the release; back within 1 % 6-15 us after it; above 1.05 V <= 5 us; then paused at
  1.003-1.006 V. Valleys while sinking −38..−50 A once phase 1's learner has followed (<= 2 ns per period); peaks
  +5..+25 A.
- 5 A: back within 1 % in 6-15 us (A237: 47.5 us). 25 A: back in 5-10 us; last-20-us valleys within 1 A of A237's.
- Re-applications within 5 A of A237 (161.5 / 171.1 / 152.6 A). Start-ups: Vo within 1 %, ladder deviation < 2 V.
- s_u_N0_100: sink never set (identical to A230).

## 4. Decision rule
- All pass: the sink mode joins the final configuration (one module); the coverage's load range becomes 0-100 % with a
  true current load on nominal boards, item 6b closes.
- t1 or t5 misses: traced before anything moves. t3 / t4 / t6 misses: the cost is weighed (another i_a or threshold
  first); otherwise the 2 % minimum load is stated.
