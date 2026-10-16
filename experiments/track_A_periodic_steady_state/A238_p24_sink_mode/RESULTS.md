# A238 - a sink mode at the lower Ton limit for item 6b (RESULTS)
Boundary: b78b871 (runs from it, cosim_sources_modified False). Records: release records-a238 (11 cosim records, logs).
Analysis: a238_analyze.py -> a238_summary.json; figure a238_figure.py -> a238_sink.png. Plant V7, one module, final
configuration + sink {hi_mv 20, lo_mv 3, i_a −40}; references: A237's and A230's records.

## 0. Verdict
- **Not adopted: t1, t5 and t7 miss. On N75 the sink mode latches and drives Vo to 1.10-1.28 V (A237 without it:
  1.046 V)** (s_c0_N75, figure right).
  - Sink is set 2.4 us after the release and never clears. Phase 1's valley sits at the −46 A its learner reaches, but
    phases 2-4 (slotted, not compared with the target) swing between −30 and −80 A over ~20 us. At the Ton limit the
    ripple is 90-110 A, not the 62 A of A237's skipping, so the module's mean current turns positive.
  - Sink suppresses the pause, so nothing stops the rise: a worse failure than the one it was meant to fix.
- **On N0 it works at the module level but not per phase.**
  - Releases to 0 / 5 A return within 1 % 10.7 / 10.5 us after the step (A237: never / 47.5 us). Vo is above 1.05 V for
    2.3 us; then the module pauses at 1.0094 / 1.0007-1.0087 V.
  - But phase 4 ratchets: each period its high side cannot bring the current back, so its valley goes −40 -> −134 A in
    2.5 us (s_cw5_N0, figure lower left; −113 A on s_c10_N0) until sink clears.
  - The −104..−113 A phase-4 valleys at 302 us are the release itself (in A237's records too), not the sink.
- **Start-ups into 1 kOhm end within 1 %:** 1.0079 / 1.0076 V (A230: 1.0218 / 1.0252 V), with one short sink
  episode each.
  - The ladder stays unbalanced: deviation 5.69 / 11.32 V at the end (A230: 6.84 / 11.98 V).
  - t5 misses on N0 by its Vo <= 1.05 V clause: 1.0534 V is the start-up's own overshoot before mode P, the same as
    A230's. Registered without checking the reference's value (lesson 8).
- **Where it does not engage it is A230 / A237 bit for bit or close:** s_u_N0_100 equals A230's record; S75 at 125 °C
  never sets sink. Re-applications 155.6-170.5 A (A237: 152.6-171.1 A); 25 A rows end in band, back 14.0 / 9.0 us
  (A237: 11.7 / 8.6 us).
- Mechanism in one line: P24's slotted phases 2-4 share the current through the series capacitors' charge balance.
  Run in reverse at the Ton limit, they do not follow phase 1's deeper valley, and neither the sign nor the size of
  the module's mean current is set (no source covers SCB reverse flow: BOUNDARY Section 1).

## 1. Criteria
| # | criterion | result |
|---|---|---|
| t0 | tb 117 / 117, regression quick + full PASS (fresh outputs) | pass |
| t1 | 0 A: <= 25 us above 1.05 V, back within 1 % <= 25 us, Vo in 1 % at the end | **1 / 2: N75 latches (1.13-1.22 V at the end)** |
| t2 | limits on every row | pass (peaks <= 170.5 A, V_DS <= 35.3 V) |
| t3 | 5 / 25 A rows in 1 % at the end, 25 A valleys in band | pass |
| t4 | re-applications <= 200 A and <= A237 + 10 A | pass (+9.0 / −15.5 / 0.0 A) |
| t5 | start-ups into 1 kOhm: Vo in 1 %, <= 1.05 V, ladder <= reference | **1 / 2: N0's 1.0534 V start-up overshoot (as A230)** |
| t6 | full-load start-up identical or within 2 A | pass (identical) |
| t7 | sink clears; valleys while set >= −55 A | **3 / 9 rows with an episode: N75 never clears; deepest valleys while set N0 −57.6..−133.7 A (phase 4 on c10 / cw5), N75 −63.2..−156.0 A** |

## 2. Predictions
- Held: N0's return within 6-15 us (10.7 / 10.5 us); start-ups within 1 %; s_u_N0_100 identical; S75's
  re-application identical.
- Missed: the valleys while sinking (−38..−50 A predicted; phase 4 to −134 A on N0, phases 2-4 −30..−80 A on N75); N75
  altogether (the ripple at the Ton limit was taken from skipping bursts, 62 A, but is 90-110 A at a −40 A valley);
  25 A back faster (slower: 14.0 against 11.7 us); the ladder below 2 V after a start-up; re-applications within 5 A
  (N0 +9.0 A, N75 −15.5 A).

## 3. Limits
- One sink target (−40 A) and one pair of thresholds; one module; 25 °C except S75h.
- Decision rule applied: t1 / t5 traced; the 2 % minimum load stands (coverage, scorecard T35). A sink for this
  topology would need each phase's own valley in reverse (phases 2-4 are slotted), not a deeper target on phase 1.
