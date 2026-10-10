# A190 - a temperature-compensated mode-S trim below 25 C (BOUNDARY)
Method: mixed (cosim, plant V5, code cfe581f; cfg only: ton_s_ns(T) = ton_s_ns(25 C) + DT[corner][T]. Math: DT =
-(Vo(T) - Vo(25 C)) / (dVo/dton), a first-order correction)
Track A, package layer. Written and committed before the runs.
Decision it changes: whether A188's start-up extends below 25 C with a characterised trim table per device corner,
read from the board's 25 C trim (slow ~35.5 ns, nominal ~23.7 ns) and its temperature, instead of stating 25-125 C.
Cheaper check done first: A189. Cold mode-S Vo fell 28.9 / 78.6 mV (S75, 0 / -40 C) and 6.1 / 16.8 mV (N0). The trim
slope at 200 ns is 0.0545 / 0.0535 V/ns (slow / nominal, A183), so DT = +0.531 / +1.441 ns (slow) and +0.113 /
+0.313 ns (nominal). The table comes from S75 and N0 only (table.json). Budget: 11 start-ups to 200 us, ~25 min.

## 1. What and why
- A189: below 25 C the slow boards' mode-S Vo falls under the cliff (-40 C) and the bumpless seed, which assumes the
  25 C entry Vo, overshoots the first Ton (0 C, 211 A). Bringing Vo(143.5) back to ~1.035 V fixes both, if the
  correction carries from one board to another of the same corner.
- Runs at 0 and -40 C: hold-out S0, S80 (slow, L0 and L x 0.8), N75 (nominal, L x 0.75), N13 (nominal, L x 1.3,
  -40 C only); in-sample S75, N0. Seeds unchanged (25 C), request 1.045 V.
- Not tested: post-step behaviour cold; four modules; ff (passed uncompensated, A189).

## 2. Criteria (per run)
 c1 start-up / handover <= 200 A;  c3 V_DS <= 40 V, COMPLETED, 0 shoot-throughs / overlaps;  c4 entry Vo >= 0.99 V;
 c8 Vo(143.5 us) within 1.035 +- 0.015 V.
The table holds if c1, c3, c4 and c8 pass on every hold-out run.

## 3. Predictions (not criteria)
- In-sample: Vo(143.5) 1.030-1.040 V. Hold-out slow boards: within +-10 mV of 1.035 V (S0's 25 C drift matched S75's
  within 3 mV at 125 C, A184: +91 vs +95 mV). Nominal: within +-5 mV.
- Handover <= 185 A everywhere; minima >= 0.985 V.

## 4. Decision rule
- The table holds: the start-up spec covers -40 to 125 C with the trim table (device model extrapolated below 25 C).
  FINAL_SPEC's start-up row adds it.
- c8 passes but c1 fails on a board: the trim is right and the handover is not; named with its mechanism.
- c8 fails on a hold-out board: the drift is board-specific, so a per-board two-temperature trim would be needed.
  The spec stays 25-125 C.
