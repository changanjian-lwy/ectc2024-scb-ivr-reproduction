# A230 - the handover request with a slope lead: start-ups into light load (RESULTS)
Boundary: 63d7c8b (code + boundary). Records: release records-a230 (20 cosim records, logs). Analysis: a230_analyze.py
-> a230_summary.json. Runs from 63d7c8b, cosim_sources_modified False. Adopted configuration (A229) on plant V7, one
module, the load resistance from t = 0; arms base (request at Vo >= 1.045 V) and lead (Vo + 0.7 us x slope >= 1.045 V).

## 0. Verdict
- **Not adopted as registered: v1 misses on four of seven light rows.** The final configuration stays; item 6 stays open.
- **At 30 % the lead works on nominal boards and hurts the hot slow board.** Vo's maximum, base -> lead: N0 1.0510 ->
  1.0465 V, N75 1.0501 -> 1.0426 V (both pass v1 with the lead, both miss 1.05 V without it). S75 at 25 / 125 C passes
  in both arms (1.0483 / 1.0491 -> 1.0402 / 1.0408 V), but at 125 C the earlier handover (request 94.8 against 95.4 us,
  Vin 33.2 V) dips to 0.9827 V (base 0.9903 V) and misses v1's 0.99 V floor; at 25 C it reaches 0.9903 V.
- **Below 30 % the lead is not enough.** N0 at 10 %: 1.0565 -> 1.0518 V (back within 1 % at the end). The lead moves
  the request by 0.6 us and takes off about 5 mV; at 10 % Vo still climbs 11-14 mV past the request.
- **A start into a true no load (1 kOhm) does not come back down.** N0 / N75 at 0 % end at 1.0181 / 1.0428 V (base)
  and 1.0218 / 1.0252 V (lead), 300 us after the start: below its lower Ton limit the module pauses with every switch
  off, so it cannot sink current, and 1 kOhm does not discharge 4.67 mF in this time. A221's no-load row is a different
  load: a 4 mOhm resistor with a -250 A source, 0 A at 1 V but 250 A per volt above it, which pulls an overshoot back.
  The registration did not see that difference; a true no load is a new open point (item 6b), not a property of the lead.
- **Full load**: S75 at 125 C hands over 0.6 us earlier with the lead at the same minimum 0.9997 V (179.2 against
  178.9 A, v2 passes); N0 and S75 at 25 C never request, lead = base bit for bit (v3).
- Late fires after the start, S75 at 30 %: 67 -> 144 (25 C), 59 -> 65 (125 C); no overlap or shoot-through anywhere,
  peaks <= 179.2 A, V_DS <= 32.4 V.

## 1. Criteria
| row | base: Vo max / min after entry | lead: Vo max / min after entry | result (lead) |
|---|---|---|---|
| N0 0 % | 1.0589 / 1.0132 V | 1.0534 / 1.0136 V | v1 **miss** (max; Vo 1.0218 V at the end) |
| N0 10 % | 1.0565 / 0.9907 V | 1.0518 / 0.9907 V | v1 **miss** (max) |
| N0 30 % | 1.0510 / 0.9999 V | 1.0465 / 0.9909 V | v1 pass |
| N75 0 % | 1.0542 / 1.0428 V | 1.0487 / 1.0252 V | v1 **miss** (Vo 1.0252 V at the end) |
| N75 30 % | 1.0501 / 0.9936 V | 1.0426 / 0.9919 V | v1 pass |
| S75 30 %, 25 C | 1.0483 / 0.9976 V | 1.0402 / 0.9903 V | v1 pass |
| S75 30 %, 125 C | 1.0491 / 0.9903 V | 1.0408 / 0.9827 V | v1 **miss** (dip) |
| S75 100 %, 125 C | handover 178.9 A, min 0.9997 V | 179.2 A, 0.9997 V | v2 pass |
| N0 / S75 100 %, 25 C | - | bit for bit base | v3 pass |
- j1: cosim_regression --quick and --full bit for bit.

## 2. Predictions
- Held: base N0 30 % 1.050-1.052 V (1.0510), N0 10 % 1.052-1.058 V (1.0565), N0 no load 1.055-1.065 V (1.0589); S75
  30 % <= 1.0495 V; S75 125 C full load within 2 A; v3 bit for bit.
- Missed: N75 no load 1.055-1.065 V (1.0542); the lead arm <= 1.047 V on every light row (N0 0 / 10 % 1.0534 / 1.0518 V,
  N75 0 % 1.0487 V within it but not back).

## 3. Limits
- One module; 25 and 125 C only; noiseless samples for the slope. One tau.
