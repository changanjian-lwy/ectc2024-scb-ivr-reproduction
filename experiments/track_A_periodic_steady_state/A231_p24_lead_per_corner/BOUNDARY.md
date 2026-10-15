# A231 - the handover lead on nominal boards only, checked hot (BOUNDARY)
Method: cosim (cfg only; code as at 63d7c8b, A230's hand_lead_us).
Track A. Written and committed before the runs. Looked at beforehand: A230's records and results.
Decision it changes: whether the start-up's handover request gets a 0.7 us slope lead on nominal boards (closes item 6
at the specified 30 % minimum load on every board), with slow boards keeping the plain request.
Cheaper check done first: A230 itself. With the lead N0 / N75 into 30 % at 25 C pass (1.0465 / 1.0426 V against
1.0510 / 1.0501 V without), and slow boards pass without it (S75 into 30 % 1.0483 / 1.0491 V at 25 / 125 C) but not with
it at 125 C (dip to 0.9827 V). The board's corner is read from its 25 C mode-S trim, as A190's cold table already does,
so a per-corner lead is a factory value like the trim. What A230 did not run: nominal boards hot, where the request also
fires at full load (A188: N0 at 125 C requests at 140 us). Budget: 12 runs to 200-300 us, about 1 h at 10 jobs.

## 1. What and why
- Rows (adopted configuration of A229, one module, load resistance from t = 0): N0 and N75 at 125 C into 30 % and into
  full load; N0 and N75 at 25 C into 20 % (information: the start-up range below 30 %). Arms base / lead (0.7 us). Hot
  = gate temp 125 C and r_sw_mohm x 1.581, as A222's S75 hot cfg differs from its 25 C cfg; trims locked at 25 C (A188).
- Sources as A230 (Lin et al. 2019; Maruta et al. 2017); the per-corner value follows A190's per-corner trim table.
- Not tested: 0 / -40 C (the cold trims of A190 move the start-up's Vo), four modules, comparator noise.

## 2. Criteria
- x1 (lead, N0 / N75 at 125 C into 30 %): A225's f6 (completes, Vo <= 1.05 V, peaks <= 200 A, no overlap or
  shoot-through, V_DS <= 40 V, Vo within 1 % over the last 20 us) and Vo >= 0.99 V after mode P's entry.
- x2 (lead, N0 / N75 at 125 C into full load): f6, handover peak <= base + 2 A, Vo's minimum after the entry >= base's
  - 2 mV and >= 0.99 V.

## 3. Predictions (not criteria)
- Base: N0 / N75 hot 30 % 1.049-1.053 V; hot full load requests at 138-141 us.
- Lead: hot 30 % <= 1.047 V with dips >= 0.990 V; hot full load requests 0.5-0.8 us earlier, handover within 2 A,
  minimum within 2 mV; 20 % rows 1.048-1.052 V.

## 4. Decision rule
- x1 and x2 pass: hand_lead_us 0.7 on nominal boards, 0 on slow boards, enters the final configuration; item 6 closes for
  start-ups into 30-100 % on N0 / N75 / S75 at 25 / 125 C (A230 + A231 rows). Below 30 % stays open (A230: N0 at 10 %
  1.0518 V; a true no load does not come back down, item 6b).
- Else: the final configuration stays; item 6 stays open.
