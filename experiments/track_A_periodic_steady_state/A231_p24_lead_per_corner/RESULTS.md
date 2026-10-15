# A231 - the handover lead on nominal boards only, checked hot (RESULTS)
Boundary: 3787df8. Records: release records-a231 (12 cosim records, log). Analysis: a231_analyze.py -> a231_summary.json.
Runs from 3787df8 (10) and 665000d (2; docs only), cosim_sources_modified False. Adopted configuration (A229), plant V7,
one module, load resistance from t = 0; arms base and lead (hand_lead_us 0.7).

## 0. Verdict
- **Adopted as registered: x1 and x2 pass.** The final configuration's start-up gets hand_lead_us 0.7 on nominal boards
  (N0, N75) and none on slow boards (S75): a factory value per corner, read from the 25 C mode-S trim like A190's cold
  table. Item 6 closes for start-ups into 30-100 % of the load on N0 / N75 / S75 at 25 and 125 C (A230 + A231 rows).
- **Nominal boards at 125 C into 30 %** (base -> lead): Vo maximum N0 1.0517 -> 1.0469 V, N75 1.0496 -> 1.0421 V; the
  minimum after the entry rises (0.9931 -> 0.9954 V, 0.9926 -> 0.9951 V); handover peaks 111.3 / 116.2 A.
- **Into 20 % at 25 C (information)**: N0 1.0545 -> 1.0489 V, N75 1.0501 -> 1.0442 V, both inside 1.05 V with the lead.
  With A230 the nominal start-up range with the lead is 20-100 % (10 %: 1.0518 V; a true no load: item 6b).
- **Hot full load never requests on V7**: N0 / N75 at 125 C stay at 1.0270 / 1.0291 V before 144 us, so the lead arm is
  the base arm bit for bit (handover 149.8 / 151.0 A). A188's hot N0 request (V5, 140 us) does not occur with V7's trims.
- No overlap or shoot-through, peaks <= 151.0 A, V_DS <= 29.4 V, Vo within 1 % at the end of every run.

## 1. Criteria
| row | base: Vo max / min after entry | lead: Vo max / min after entry | result |
|---|---|---|---|
| N0 125 C, 30 % | 1.0517 / 0.9931 V | 1.0469 / 0.9954 V | x1 pass |
| N75 125 C, 30 % | 1.0496 / 0.9926 V | 1.0421 / 0.9951 V | x1 pass |
| N0 125 C, 100 % | 1.0270 / 1.0001 V, 149.8 A | bit for bit base | x2 pass |
| N75 125 C, 100 % | 1.0291 / 1.0001 V, 151.0 A | bit for bit base | x2 pass |
| N0 / N75 25 C, 20 % | 1.0545 / 1.0501 V | 1.0489 / 1.0442 V | information |

## 2. Predictions
- Held: base hot 30 % 1.049-1.053 V (1.0517 / 1.0496); lead hot 30 % <= 1.047 V (1.0469 / 1.0421) with dips >= 0.990 V;
  lead 20 % within 1.048-1.052 V for N0 (1.0489).
- Missed: hot full load requesting at 138-141 us (no request on V7); N75's 20 % with the lead (1.0442 V, below the range).

## 3. Limits
- One module; 25 / 125 C (0 / -40 C not run: A190's cold trims move the start-up's Vo); noiseless slope samples; the
  per-corner rule assumes the corner is known at the factory, as A190 does.
